/* hub-behaviours v1.4 — the controlled behaviour library.
 *
 * Markup opts in with data-hub-module="<name>" attributes, which are inert
 * until something puts this module on the page — so a page written today
 * works today, and gains behaviour whenever the module arrives.
 *
 * Two ways it arrives, and a pattern never knows which. A site can carry this
 * file as its own asset and reference it with one module tag. Or a platform
 * can inject it, which is better when it exists: one cached copy across every
 * brand, versioned in one place, and no page carrying a tag at all. The
 * contract below is what makes both safe.
 *
 * It is an ES module. The tag is <script type="module" src="…"></script> —
 * a classic script fails on the export at the foot of this file.
 *
 * Contract (see CONTRIBUTING.md, "Behaviours"):
 *   - every behaviour is a progressive enhancement over working HTML/CSS;
 *   - init is idempotent and error-contained per element;
 *   - one global (window.HubBehaviours), events as hub:<name>:<event>,
 *     options only from data-hub-* attributes;
 *   - all motion honours prefers-reduced-motion.
 */

const registry = new Map();
/* The real record of what has been set up. An attribute survives cloneNode
   and an innerHTML round trip, so a re-rendered container would arrive
   already marked done and never be initialised; a node's identity does not
   survive either, which is the property this needs. The attribute is kept
   alongside it, for anyone inspecting the page. */
const live = new WeakSet();
const INITIALISED = "data-hub-initialised";
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

/* Behaviour state styles are injected here, not shipped in page CSS: a page
 * whose script never loads must render exactly as authored, so no authored
 * stylesheet may hide content in anticipation of a behaviour. */
const stateStyles = [];

function register(name, { setup, css }) {
  if (registry.has(name)) return;
  registry.set(name, setup);
  if (css) stateStyles.push(css);
}

function injectStyles() {
  if (!stateStyles.length || document.getElementById("hub-behaviour-styles")) return;
  const style = document.createElement("style");
  style.id = "hub-behaviour-styles";
  style.textContent = stateStyles.join("\n");
  document.head.append(style);
}

function initAll(scope) {
  injectStyles();
  const root = scope || document;
  const targets = Array.from(root.querySelectorAll("[data-hub-module]"));
  // querySelectorAll excludes the root itself; a scoped re-init whose root IS
  // a module element must still initialise it.
  if (root !== document && root.matches && root.matches("[data-hub-module]")) {
    targets.unshift(root);
  }
  targets.forEach((el) => {
    if (live.has(el)) return;
    // Marked before, so a behaviour that triggers another init cannot
    // recurse; cleared on failure, so a half-built element can be repaired
    // later rather than being marked done forever.
    live.add(el);
    el.setAttribute(INITIALISED, "");
    new Set(el.getAttribute("data-hub-module").split(/\s+/)).forEach((name) => {
      const setup = registry.get(name);
      if (!setup) return; // unknown module: inert, never an error
      try {
        setup(el);
      } catch (err) {
        // One broken element never takes down the page or its siblings, and
        // it is not left marked done: a later init may find the page in a
        // state it can finish.
        live.delete(el);
        el.removeAttribute(INITIALISED);
        console.error(`hub-behaviours: ${name} failed on`, el, err);
      }
    });
  });
}

function emit(el, name, event, detail) {
  el.dispatchEvent(new CustomEvent(`hub:${name}:${event}`, { bubbles: true, detail }));
}

/* --- reveal: entrance animation on scroll ------------------------------- */
/* Markup: data-hub-module="reveal" on the element (or a container with
 * data-hub-reveal-children to stagger its direct children).
 * Honours reduced motion by doing nothing at all. */
register("reveal", {
  setup(el) {
    if (reducedMotion.matches) return;
    const targets = el.hasAttribute("data-hub-reveal-children")
      ? Array.from(el.children)
      : [el];
    // Everything fallible is constructed BEFORE any content is hidden: if
    // setup dies here, the page stays exactly as authored.
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.remove("hub-reveal-pending");
        entry.target.classList.add("hub-revealed");
        observer.unobserve(entry.target);
        emit(entry.target, "reveal", "shown");
      });
    }, { rootMargin: "0px 0px -10% 0px" });
    targets.forEach((t, i) => {
      t.classList.add("hub-reveal-pending");
      t.style.setProperty("--hub-reveal-delay", `${Math.min(i * 80, 400)}ms`);
      observer.observe(t);
    });
  },
  css: `
.hub-reveal-pending { opacity: 0; translate: 0 24px; }
.hub-revealed {
  opacity: 1; translate: 0 0;
  transition: opacity 0.6s ease-out var(--hub-reveal-delay, 0ms),
              translate 0.6s ease-out var(--hub-reveal-delay, 0ms);
}
/* Belt and braces: whatever state the script got to, reduced-motion and
   print always see the content. */
@media (prefers-reduced-motion: reduce), print {
  .hub-reveal-pending { opacity: 1; translate: none; }
}`,
});

/* --- marquee: a rail that moves on its own, and a control to stop it ----- */
/* Markup: data-hub-module="marquee" on a block whose scroller is its own list.
 * Nothing is authored inside a platform-filled block, so the track is FOUND
 * rather than named, and the pause control is BUILT - no control ships in the
 * page, so the authored render is a rail the visitor drives and nothing else.
 * Options: data-hub-marquee-speed, pixels per second, default 30.
 *          data-hub-marquee-pause-label, the control's word.
 *
 * Under reduced motion it does nothing at all: no movement, and so no control,
 * because there is nothing to stop.
 *
 * WCAG 2.2.2 is why the control is not optional. Content that starts moving by
 * itself and runs for more than five seconds needs a way to stop it, and
 * pause-on-hover is not one - it does nothing for a visitor on a phone or
 * using a keyboard. */
register("marquee", {
  setup(el) {
    if (reducedMotion.matches) return;
    const track = el.querySelector("ul, ol") || el.firstElementChild;
    if (!track || track.children.length < 2) return;

    // A seamless loop needs the run duplicated: at half the scroll width the
    // view is identical to the start, so resetting there is invisible. The
    // copies are decoration - they are removed from the tree assistive
    // technology reads, and nothing in them can be tabbed to.
    const originals = Array.from(track.children);
    originals.forEach((node) => {
      const copy = node.cloneNode(true);
      copy.setAttribute("aria-hidden", "true");
      copy.setAttribute("data-hub-marquee-copy", "");
      copy.querySelectorAll("a, button, input, select, textarea, [tabindex]")
        .forEach((f) => f.setAttribute("tabindex", "-1"));
      if (copy.matches("a, button")) copy.setAttribute("tabindex", "-1");
      track.append(copy);
    });

    const speed = Math.min(
      Math.max(Number(el.getAttribute("data-hub-marquee-speed")) || 30, 5), 200);
    const label = el.getAttribute("data-hub-marquee-pause-label") || "Pause";

    const button = document.createElement("button");
    button.type = "button";
    button.className = "hub-marquee-control";
    button.setAttribute("aria-pressed", "false");
    button.textContent = label;
    el.prepend(button);

    // Snapping fights a scroll position set every frame: mandatory snapping
    // pulls the rail back to its nearest point as fast as this moves it, and
    // the block sits still. It is turned off ON THE ELEMENT rather than in the
    // injected stylesheet, because a class cannot be guaranteed to outrank
    // whatever selector the page used to switch snapping on - and a behaviour
    // does not know that page's CSS. The authored value returns if motion is
    // ever turned off below.
    // Smooth scrolling is the same fight one step along: it turns every
    // per-frame nudge into its own animation, so the rail lags behind and,
    // worse, keeps gliding after a visitor has pressed stop - which is the
    // one thing the control exists to guarantee.
    const authored = {
      snap: track.style.scrollSnapType,
      behavior: track.style.scrollBehavior,
    };
    track.style.scrollSnapType = "none";
    track.style.scrollBehavior = "auto";
    track.classList.add("hub-marquee-running");

    let paused = false, stopped = false, last = null, onScreen = true;

    function step(now) {
      if (stopped) return;
      const half = track.scrollWidth / 2;
      if (last !== null && !paused && onScreen && half > 0) {
        track.scrollLeft += speed * ((now - last) / 1000);
        // The reset is a subtraction, never a jump to zero: at half width the
        // pixels are identical, so nothing moves on screen.
        if (track.scrollLeft >= half) track.scrollLeft -= half;
      }
      last = now;
      requestAnimationFrame(step);
    }
    requestAnimationFrame(step);

    function setPaused(next, byControl) {
      paused = next;
      if (byControl) {
        button.setAttribute("aria-pressed", String(next));
        emit(el, "marquee", next ? "paused" : "resumed");
      }
    }
    // The control latches; hover and focus are held only while they last, and
    // never override a visitor who has actually pressed stop.
    let latched = false;
    button.addEventListener("click", () => {
      latched = !latched;
      setPaused(latched, true);
    });
    const hold = () => { if (!latched) setPaused(true, false); };
    const release = () => { if (!latched) setPaused(false, false); };
    el.addEventListener("pointerenter", hold);
    el.addEventListener("pointerleave", release);
    el.addEventListener("focusin", hold);
    el.addEventListener("focusout", release);
    // A visitor dragging the rail is driving it themselves.
    track.addEventListener("pointerdown", hold);
    track.addEventListener("pointerup", release);

    // Off screen, it stops: a page does not animate what nobody is looking at.
    new IntersectionObserver((entries) => {
      onScreen = entries[0].isIntersecting;
    }).observe(el);

    // Reduced motion can be turned on while the page is open. Stop for good,
    // put the track back, and take the control away with the movement.
    reducedMotion.addEventListener("change", (e) => {
      if (!e.matches) return;
      stopped = true;
      track.style.scrollSnapType = authored.snap;
      track.style.scrollBehavior = authored.behavior;
      track.classList.remove("hub-marquee-running");
      track.querySelectorAll("[data-hub-marquee-copy]").forEach((n) => n.remove());
      button.remove();
    });
  },
  css: `
.hub-marquee-running { scrollbar-width: none; }
.hub-marquee-running::-webkit-scrollbar { display: none; }
.hub-marquee-control {
  display: inline-flex; align-items: center; min-height: 44px;
  margin-bottom: 0.5rem; padding: 0 1rem;
  border: 1.5px solid currentColor; border-radius: 999px;
  background: transparent; color: inherit;
  font: inherit; font-size: 0.85rem; font-weight: 700; cursor: pointer;
}
.hub-marquee-control:focus-visible { outline: 3px solid currentColor; outline-offset: 2px; }
@media (prefers-reduced-motion: reduce), print {
  .hub-marquee-control { display: none; }
}`,
});

/* --- tabs: one rail over stacked panels --------------------------------- */
/* Markup: data-hub-module="tabs" on the panels container; every direct child
 * carrying data-hub-tab-label="..." is a panel. The rail is BUILT from those
 * labels - no tab control ships in the page, so the authored render is every
 * panel, stacked, each under its own heading.
 * Options: data-hub-tabs-label names the rail for assistive technology. */
let tabsInstances = 0;

function tabsBase() {
  // Derived, never fixed: two instances on one page must not share ids.
  let base;
  do {
    tabsInstances += 1;
    base = `hub-tabs-${tabsInstances}`;
  } while (document.getElementById(`${base}-tab-0`) ||
           document.getElementById(`${base}-panel-0`));
  return base;
}

register("tabs", {
  setup(el) {
    const panels = Array.from(el.children).filter((child) =>
      (child.getAttribute("data-hub-tab-label") || "").trim() &&
      !child.classList.contains("hub-tabs-list"));
    // One panel is not a tab set; leave the markup exactly as authored.
    if (panels.length < 2) return;

    const base = tabsBase();
    const list = document.createElement("div");
    list.className = "hub-tabs-list";
    list.setAttribute("role", "tablist");
    const listLabel = el.getAttribute("data-hub-tabs-label");
    if (listLabel) list.setAttribute("aria-label", listLabel);

    const tabs = panels.map((panel, i) => {
      const tab = document.createElement("button");
      tab.type = "button";
      tab.className = "hub-tabs-tab";
      tab.id = `${base}-tab-${i}`;
      tab.setAttribute("role", "tab");
      // An id the page already gave the panel is the page's, and something
      // may be pointing at it.
      const authored = panel.id && !panel.hasAttribute("data-hub-tabs-own-id");
      tab.dataset.hubTabsPanel = authored ? panel.id : `${base}-panel-${i}`;
      if (!authored) panel.setAttribute("data-hub-tabs-own-id", "");
      tab.setAttribute("aria-controls", tab.dataset.hubTabsPanel);
      tab.textContent = panel.getAttribute("data-hub-tab-label");
      list.append(tab);
      return tab;
    });

    let selected = -1;
    function show(next, moveFocus) {
      const index = (next + panels.length) % panels.length;
      if (index === selected) return;
      const switching = selected !== -1;
      selected = index;
      tabs.forEach((tab, i) => {
        tab.setAttribute("aria-selected", i === index ? "true" : "false");
        // Roving tabindex: the whole rail is one tab stop.
        tab.tabIndex = i === index ? 0 : -1;
        panels[i].hidden = i !== index;
      });
      if (moveFocus) {
        tabs[index].focus();
        tabs[index].scrollIntoView({
          block: "nearest", inline: "nearest",
          behavior: reducedMotion.matches ? "auto" : "smooth",
        });
      }
      if (switching && !reducedMotion.matches) {
        const panel = panels[index];
        panel.classList.add("hub-tabs-enter");
        panel.addEventListener("animationend", () => {
          panel.classList.remove("hub-tabs-enter");
        }, { once: true });
      }
      emit(el, "tabs", "change", { index, panel: panels[index] });
    }

    // Both listeners live on the rail, which is a child of the element this
    // behaviour was given, so they leave with it. Nothing is attached to the
    // document.
    list.addEventListener("click", (event) => {
      const tab = event.target.closest(".hub-tabs-tab");
      if (tab) show(tabs.indexOf(tab), true);
    });
    list.addEventListener("keydown", (event) => {
      let next;
      if (event.key === "ArrowRight") next = selected + 1;
      else if (event.key === "ArrowLeft") next = selected - 1;
      else if (event.key === "Home") next = 0;
      else if (event.key === "End") next = panels.length - 1;
      else return;
      event.preventDefault();
      show(next, true);
    });

    // Insert first, then clear any rail this element already owned. Sweeping
    // first would leave a container with no rail at all if this throws.
    el.prepend(list);
    el.querySelectorAll(":scope > .hub-tabs-list").forEach((old) => {
      if (old !== list) old.remove();
    });
    panels.forEach((panel, i) => {
      panel.id = tabs[i].dataset.hubTabsPanel;
      panel.classList.add("hub-tabs-panel");
      panel.setAttribute("role", "tabpanel");
      panel.setAttribute("aria-labelledby", tabs[i].id);
      // A panel holding nothing focusable is its own tab stop.
      panel.setAttribute("tabindex", "0");
    });
    show(0, false);
  },
  css: `
.hub-tabs-list { display: flex; flex-wrap: wrap; }
/* !important on screen: sheet order is not guaranteed and a pattern rule with
   more classes outweighs this one, and a panel that fails to hide is every
   panel at once. Print reverts to the UA default, which is block in every
   engine, so the whole set prints. */
.hub-tabs-panel[hidden] { display: none !important; }
@media print { .hub-tabs-panel[hidden] { display: revert !important; } }
@media (prefers-reduced-motion: no-preference) {
  .hub-tabs-enter { animation: hub-tabs-in 0.35s ease-out; }
}
@keyframes hub-tabs-in {
  from { opacity: 0; translate: 0 8px; }
  to { opacity: 1; translate: 0 0; }
}`,
});

/* --- drawer: the three things a CSS drawer cannot reach ----------------- */
/* Markup: data-hub-module="drawer" on a <details> whose <summary> is the
 * control and whose other element child is the panel. The disclosure already
 * opens, closes, takes the keyboard and shows focus on its own; this adds
 * Escape, a click on the backdrop, and holding the page still behind it.
 *
 * It is modal only while the stylesheet has the panel fixed to the viewport,
 * so the same markup at a width where the menu is an ordinary row needs no
 * option here and gets no lock. Emits hub:drawer:open and hub:drawer:close.
 * It moves nothing itself, so there is no motion to reduce.
 */
const drawersHolding = new Set();

register("drawer", {
  setup(el) {
    const summary = el.querySelector(":scope > summary");
    const panel = Array.from(el.children).find((child) => child !== summary);
    // Not a disclosure with a panel in it: leave the markup alone.
    if (!summary || !panel) return;

    // The stylesheet decides, not a breakpoint written down twice.
    const modal = () =>
      el.open && window.getComputedStyle(panel).position === "fixed";

    function hold(on) {
      if (on) drawersHolding.add(el);
      else drawersHolding.delete(el);
      // The one thing that cannot be done from inside the element asking for
      // it: a page holds still at its root or not at all. Counted, so two
      // drawers on one page cannot release each other's hold.
      document.documentElement.classList.toggle(
        "hub-drawer-holding", drawersHolding.size > 0);
    }

    function sync() {
      const on = modal();
      if (on === drawersHolding.has(el)) return;
      hold(on);
      emit(el, "drawer", on ? "open" : "close");
    }

    function close() {
      if (!el.open) return;
      el.open = false;
      summary.focus({ preventScroll: true });
    }

    el.addEventListener("toggle", () => {
      // Some engines do not focus a summary that was tapped, and Escape has
      // to arrive from somewhere inside this element for either listener
      // below to see it.
      if (modal() && !el.contains(document.activeElement)) {
        summary.focus({ preventScroll: true });
      }
      sync();
    });

    // Both listeners are on the element this behaviour was handed, and the
    // backdrop is that element's own ::before - so a press on the backdrop
    // arrives with the element itself as the target, which neither the
    // control nor anything in the panel ever is.
    el.addEventListener("click", (event) => {
      if (event.target === el && modal()) close();
    });
    el.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && modal()) {
        event.preventDefault();
        close();
      }
    });

    // A width change can take the panel out of the fixed state it was held
    // for. The panel's own box is what changes, so the panel is what is
    // watched - nothing is attached to the document.
    new ResizeObserver(() => sync()).observe(panel);
    sync();
  },
  css: `
.hub-drawer-holding, .hub-drawer-holding > body { overflow: hidden; }`,
});

/* --- menu: submenus that open on purpose --------------------------------- */
/* Markup: data-hub-module="menu" on a <nav> holding a list. Every item of
 * the first list that carries a list of its own is a parent, and the parent's
 * first <a> or <button> is its control. The stylesheet has already given the
 * child list a hover and focus-within reveal; this makes the parent a real
 * control with aria-expanded, adds Escape, an outside press, the arrow keys
 * and hover grace, and turns a panel that would leave the viewport around.
 *
 * Acts only while the stylesheet positions the child list - inside a drawer
 * the lists are inline and every parent is left exactly as authored. Emits
 * hub:menu:open and hub:menu:close. It moves nothing itself.
 */
const HOVER_GRACE_MS = 220;

register("menu", {
  setup(el) {
    const list = el.querySelector("ul, ol");
    if (!list) return;
    const parents = new Map();

    const childList = (li) =>
      Array.from(li.children).find((c) => c.matches("ul, ol"));
    const control = (li) =>
      Array.from(li.children).find((c) => c.matches("a, button"));
    const positioned = (sub) =>
      /^(absolute|fixed)$/.test(window.getComputedStyle(sub).position);
    const focusable = (root) => Array.from(root.querySelectorAll(
      "a[href], button, [tabindex]:not([tabindex='-1'])"));

    function setOpen(li, on) {
      const p = parents.get(li);
      if (!p || !p.active || p.open === on) return;
      p.open = on;
      li.setAttribute("data-hub-menu-open", on ? "true" : "false");
      p.toggler.setAttribute("aria-expanded", on ? "true" : "false");
      if (on) {
        parents.forEach((q, other) => { if (other !== li) setOpen(other, false); });
        // Turned around only when its own edge leaves the viewport, and only
        // after the reveal has laid it out.
        li.removeAttribute("data-hub-menu-flip");
        requestAnimationFrame(() => {
          if (!p.open) return;
          const r = p.sub.getBoundingClientRect();
          if (r.right > document.documentElement.clientWidth + 1) {
            li.setAttribute("data-hub-menu-flip", "");
          }
        });
      }
      emit(li, "menu", on ? "open" : "close");
    }

    function enhance(li) {
      if (parents.has(li)) return;
      const sub = childList(li);
      const ctl = control(li);
      if (!sub || !ctl) return;
      const p = { sub, ctl, toggler: ctl, open: false, active: false, timer: 0,
                  byHover: false };
      // A parent that is a real link keeps its link and gains a button for
      // the panel; one with no href becomes the button itself.
      if (ctl.matches("a[href]")) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "hub-menu-toggle";
        const text = document.createElement("span");
        text.className = "hub-menu-toggle-text";
        text.textContent = (ctl.textContent || "").trim();
        button.append(text);
        ctl.after(button);
        p.toggler = button;
      }
      parents.set(li, p);

      const toggler = p.toggler;
      toggler.addEventListener("click", (event) => {
        if (!p.active) return;
        event.preventDefault();
        // A pointer that opened the panel by arriving does not shut it by
        // pressing; the press turns a hover into a choice that stays.
        if (p.open && p.byHover) {
          p.byHover = false;
          return;
        }
        p.byHover = false;
        setOpen(li, !p.open);
      });
      toggler.addEventListener("keydown", (event) => {
        if (!p.active) return;
        if (event.key === "ArrowDown") {
          event.preventDefault();
          setOpen(li, true);
          const first = focusable(sub)[0];
          if (first) first.focus();
        } else if ((event.key === "Enter" || event.key === " ")
                   && toggler.tagName !== "BUTTON") {
          event.preventDefault();
          setOpen(li, !p.open);
        }
      });
      li.addEventListener("keydown", (event) => {
        if (!p.active) return;
        if (event.key === "Escape" && p.open) {
          event.preventDefault();
          event.stopPropagation();
          setOpen(li, false);
          toggler.focus();
        } else if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
          const keys = Array.from(parents.keys()).filter((k) => parents.get(k).active);
          const index = keys.indexOf(li);
          if (index === -1) return;
          const next = keys[(index + (event.key === "ArrowRight" ? 1 : -1)
                             + keys.length) % keys.length];
          if (next === li) return;
          event.preventDefault();
          const wasOpen = p.open;
          setOpen(li, false);
          parents.get(next).toggler.focus();
          if (wasOpen) setOpen(next, true);
        }
      });
      li.addEventListener("focusout", (event) => {
        if (!p.active || li.contains(event.relatedTarget)) return;
        setOpen(li, false);
      });
      // Hover opens at once and closes after a grace, so a pointer crossing
      // the gap between the item and its panel does not shut it. Touch has
      // no hover; a tap reaches the click above.
      li.addEventListener("pointerenter", (event) => {
        if (!p.active || event.pointerType !== "mouse") return;
        clearTimeout(p.timer);
        if (!p.open) {
          p.byHover = true;
          setOpen(li, true);
        }
      });
      li.addEventListener("pointerleave", (event) => {
        if (!p.active || event.pointerType !== "mouse" || !p.byHover) return;
        clearTimeout(p.timer);
        p.timer = setTimeout(() => {
          if (p.byHover) setOpen(li, false);
        }, HOVER_GRACE_MS);
      });
    }

    function activate(li, on) {
      const p = parents.get(li);
      if (!p || p.active === on) return;
      if (!on) setOpen(li, false);
      p.active = on;
      const t = p.toggler;
      li.classList.toggle("hub-menu-parent", on);
      if (on) {
        li.setAttribute("data-hub-menu-open", "false");
        t.setAttribute("aria-expanded", "false");
        t.setAttribute("aria-haspopup", "true");
        if (t.tagName !== "BUTTON") {
          t.setAttribute("role", "button");
          t.tabIndex = 0;
        }
      } else {
        li.removeAttribute("data-hub-menu-open");
        li.removeAttribute("data-hub-menu-flip");
        t.removeAttribute("aria-expanded");
        t.removeAttribute("aria-haspopup");
        if (t.tagName !== "BUTTON") {
          t.removeAttribute("role");
          t.removeAttribute("tabindex");
        }
      }
    }

    function sync() {
      Array.from(list.children).forEach(enhance);
      parents.forEach((p, li) => {
        if (!li.isConnected) { parents.delete(li); return; }
        activate(li, positioned(p.sub));
      });
    }

    // An outside press closes whatever is open. The one listener that has
    // to sit above the element, because outside is where the press lands.
    document.addEventListener("pointerdown", (event) => {
      if (el.contains(event.target)) return;
      parents.forEach((p, li) => setOpen(li, false));
    });
    // Items arrive and leave - the overflow behaviour moves them - and a
    // width change moves the lists between inline and positioned.
    new MutationObserver(() => sync()).observe(list, { childList: true });
    new ResizeObserver(() => sync()).observe(el);
    sync();
  },
  css: `
.hub-menu-parent[data-hub-menu-open="false"] > ul,
.hub-menu-parent[data-hub-menu-open="false"] > ol {
  opacity: 0 !important; pointer-events: none !important;
}
.hub-menu-parent[data-hub-menu-open="true"] > ul,
.hub-menu-parent[data-hub-menu-open="true"] > ol {
  opacity: 1 !important; pointer-events: auto !important;
}
.hub-menu-parent[data-hub-menu-flip] > ul,
.hub-menu-parent[data-hub-menu-flip] > ol {
  inset-inline-start: auto !important; inset-inline-end: 0 !important;
}
.hub-menu-toggle {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 44px; min-height: 44px; padding: 0; border: 0;
  background: none; color: inherit; font: inherit; cursor: pointer;
}
.hub-menu-toggle::after {
  content: ""; width: 0.4em; height: 0.4em;
  border-inline-end: 2px solid currentColor; border-block-end: 2px solid currentColor;
  transform: translateY(-0.15em) rotate(45deg);
}
.hub-menu-toggle-text {
  position: absolute; width: 1px; height: 1px; overflow: hidden;
  clip-path: inset(50%); white-space: nowrap;
}`,
});

/* --- overflow: the items that do not fit the row fold into one ----------- */
/* Markup: data-hub-module="overflow" on a <nav> holding a list, and
 * data-hub-overflow-label carrying the word for the folded item (default
 * "More"). The list's own stylesheet asks for the fold by setting the custom
 * property --hub-overflow to `more` on it - so the same markup on a rung, or
 * at a width, that wraps or scrolls instead is left alone, and with no
 * library the list is whatever the stylesheet made it.
 *
 * Items are MOVED, never cloned, from the end of the row into the folded
 * item's own list, and moved back in order when room returns; the folded
 * item is a parent like any other, so the menu behaviour opens it. Emits
 * hub:overflow:change with the number folded. It moves nothing on screen by
 * itself, so there is no motion to reduce.
 */
register("overflow", {
  setup(el) {
    const list = el.querySelector("ul, ol");
    if (!list) return;
    const label = el.getAttribute("data-hub-overflow-label") || "More";

    const more = document.createElement("li");
    more.className = "hub-overflow-more";
    more.hidden = true;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "hub-overflow-toggle";
    button.textContent = label;
    const bucket = document.createElement(list.tagName.toLowerCase());
    bucket.className = "hub-overflow-list";
    more.append(button, bucket);
    list.append(more);

    const active = () =>
      window.getComputedStyle(list).getPropertyValue("--hub-overflow").trim() === "more";
    const overflowing = () => list.scrollWidth > list.clientWidth + 1;
    let fitting = false;

    function restore() {
      while (bucket.firstElementChild) list.insertBefore(bucket.firstElementChild, more);
      more.hidden = true;
      list.style.flexWrap = "";
    }

    function fit() {
      if (fitting) return;
      fitting = true;
      try {
        if (!active()) { restore(); return; }
        list.style.flexWrap = "nowrap";
        // Give back first: whatever fits again comes out of the fold, in
        // order, until the row overflows.
        while (bucket.firstElementChild) {
          const item = bucket.firstElementChild;
          list.insertBefore(item, more);
          more.hidden = !bucket.firstElementChild;
          if (overflowing()) {
            bucket.prepend(item);
            more.hidden = false;
            break;
          }
        }
        // Then fold from the end until the row fits, the folded item
        // counted in.
        while (overflowing()) {
          const item = more.previousElementSibling;
          if (!item) break;
          more.hidden = false;
          bucket.prepend(item);
        }
      } finally {
        fitting = false;
      }
      emit(el, "overflow", "change", { folded: bucket.children.length });
    }

    new ResizeObserver(() => fit()).observe(el);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(fit);
    fit();
  },
  css: `
.hub-overflow-more[hidden] { display: none !important; }`,
});

/* --- shrink: a sticky bar that tightens once the page has scrolled ------- */
/* Markup: data-hub-module="shrink" on the bar, optional data-hub-shrink-after
 * in pixels (default: the bar's own height). Sets data-hub-shrink="scrolled"
 * on the bar past that point and removes it above; the bar's own stylesheet
 * decides what the state looks like. Acts only while the stylesheet has the
 * bar sticky or fixed. Emits hub:shrink:compact and hub:shrink:full. The
 * transition is the stylesheet's, so reduced motion is its to honour.
 */
register("shrink", {
  setup(el) {
    const after = Math.max(Number(el.getAttribute("data-hub-shrink-after")) || 0, 0);
    const sticky = () =>
      /^(sticky|fixed)$/.test(window.getComputedStyle(el).position);
    let threshold = after || el.offsetHeight || 64;
    let scrolled = false;
    let ticking = false;

    function update() {
      ticking = false;
      const on = sticky() && window.scrollY > threshold;
      if (on === scrolled) return;
      scrolled = on;
      if (on) el.setAttribute("data-hub-shrink", "scrolled");
      else el.removeAttribute("data-hub-shrink");
      emit(el, "shrink", on ? "compact" : "full");
    }

    window.addEventListener("scroll", () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(update);
    }, { passive: true });
    // The threshold is the bar's full height, never its shrunk one, or the
    // two states would hand the page back and forth at the boundary.
    new ResizeObserver(() => {
      if (!scrolled && !after) threshold = el.offsetHeight || threshold;
      update();
    }).observe(el);
    update();
  },
});

/* ----------------------------------------------------------------------- */

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => initAll());
} else {
  initAll();
}

window.HubBehaviours = { version: "1.4.0", initAll, register };
export { initAll, register };
