/* hub-behaviours v1.15 — the controlled behaviour library.
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
   alongside it, for anyone inspecting the page. The record is the page's, not
   this copy's: a page that loads the file twice - its own tag and the
   platform's - still builds each block once. */
const live = window.__hubBehavioursLive || (window.__hubBehavioursLive = new WeakSet());
const INITIALISED = "data-hub-initialised";
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
/* Motion added for effect - easing in, counting up, gliding - is a choice a
 * page makes in its styles. A block that sets --hub-motion: none on itself,
 * or sits inside one that does, was built still, and reveal, counter and
 * marquee leave it exactly as authored. A page whose styles never mention it
 * moves as it always has. */
const heldStill = (el) => getComputedStyle(el).getPropertyValue("--hub-motion").trim() === "none";

/* Behaviour state styles are injected here, not shipped in page CSS: a page
 * whose script never loads must render exactly as authored, so no authored
 * stylesheet may hide content in anticipation of a behaviour. */
const stateStyles = [];

function register(name, { setup, css }) {
  if (registry.has(name)) return;
  registry.set(name, setup);
  if (css) stateStyles.push(css);
}

let styled = false;
function injectStyles() {
  // Once per copy of this file, not once per page: a page carrying two copies
  // gets both copies' rules, so a block set up by either is drawn by its own.
  if (!stateStyles.length || styled) return;
  styled = true;
  const style = document.createElement("style");
  if (!document.getElementById("hub-behaviour-styles")) style.id = "hub-behaviour-styles";
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
    if (reducedMotion.matches || heldStill(el)) return;
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
 *          data-hub-marquee-fit, or --hub-marquee-fit from the block's
 *          stylesheet: "still" leaves a run that fits its row as authored,
 *          with no copies and no control, until it no longer fits.
 *
 * Under reduced motion it does nothing at all: no movement, and so no control,
 * because there is nothing to stop.
 *
 * WCAG 2.2.2 is why the control is not optional. Content that starts moving by
 * itself and runs for more than five seconds needs a way to stop it, and
 * pause-on-hover is not one - it does nothing for a visitor on a phone or
 * using a keyboard. */
/* Doubled for the loop, a run that already fits its row scrolls part way
 * and stops, under a stop control with nothing to stop. A block that asks
 * for it waits instead, as authored, and starts the first time its run no
 * longer fits; a block that does not ask starts as it always has. */
function waitsWhileItFits(el, track, start) {
  const asked = (el.getAttribute("data-hub-marquee-fit")
    || getComputedStyle(el).getPropertyValue("--hub-marquee-fit") || "").trim().toLowerCase();
  const fits = () => track.scrollWidth <= track.clientWidth + 1;
  if (asked !== "still" || !fits()) return false;
  const watch = new ResizeObserver(() => {
    if (fits()) return;
    watch.disconnect();
    start();
  });
  watch.observe(track);
  return true;
}

register("marquee", {
  setup: function marquee(el) {
    if (reducedMotion.matches || heldStill(el)) return;
    const track = el.querySelector("ul, ol") || el.firstElementChild;
    if (!track || track.children.length < 2) return;
    if (waitsWhileItFits(el, track, () => marquee(el))) return;

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
    // A block that asks for the round look (data-hub-marquee-look="round", or
    // --hub-marquee-look: round from its stylesheet) gets a pause or play icon
    // with the word kept as the control's accessible name. Without it the
    // control is the worded one every earlier page was built with.
    const look = (el.getAttribute("data-hub-marquee-look")
      || getComputedStyle(el).getPropertyValue("--hub-marquee-look") || "").trim().toLowerCase();
    if (look === "round") {
      button.classList.add("hub-marquee-control--round");
      const text = document.createElement("span");
      text.className = "hub-marquee-control-text";
      text.textContent = label;
      button.append(text);
    } else {
      button.textContent = label;
    }
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
    // The browser holds a scroller's offset in whole pixels, so a step under
    // half a pixel rounds back to where it was: 30 pixels a second is a
    // quarter of a pixel a frame on a 120Hz screen, and the row never moved.
    // The position is kept here, in fractions, and handed over each frame. A
    // visitor who drags the rail moves it, and the glide carries on from there.
    let at = track.scrollLeft;

    function step(now) {
      if (stopped) return;
      const half = track.scrollWidth / 2;
      if (last !== null && !paused && onScreen && half > 0) {
        if (Math.abs(track.scrollLeft - at) > 1) at = track.scrollLeft;
        at += speed * ((now - last) / 1000);
        // The reset is a subtraction, never a jump to zero: at half width the
        // pixels are identical, so nothing moves on screen.
        if (at >= half) at -= half;
        track.scrollLeft = at;
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
/* The round look: two bars while it moves, a play triangle once stopped. */
.hub-marquee-control--round { width: 44px; padding: 0; justify-content: center; }
.hub-marquee-control--round .hub-marquee-control-text {
  position: absolute; width: 1px; height: 1px;
  overflow: hidden; clip-path: inset(50%); white-space: nowrap;
}
.hub-marquee-control--round::after {
  content: ""; box-sizing: border-box; width: 0.6rem; height: 0.75rem;
  border-inline: 3px solid currentColor;
}
.hub-marquee-control--round[aria-pressed="true"]::after {
  width: 0; height: 0; margin-inline-start: 0.2rem;
  border-block: 0.4rem solid transparent;
  border-inline-start: 0.7rem solid currentColor; border-inline-end: 0;
}
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
        // Turned around only when one of its edges leaves the viewport, and
        // only after the reveal has laid it out. Leaving by the end edge it
        // hangs from the parent's end edge; leaving by the start edge - a
        // panel already hung from its end edge, on a parent that a wrapped
        // row puts first on its line - it hangs from the parent's start edge.
        li.removeAttribute("data-hub-menu-flip");
        requestAnimationFrame(() => {
          if (!p.open) return;
          const r = p.sub.getBoundingClientRect();
          const w = document.documentElement.clientWidth;
          const rtl = window.getComputedStyle(p.sub).direction === "rtl";
          const pastEnd = rtl ? r.left < -1 : r.right > w + 1;
          const pastStart = rtl ? r.right > w + 1 : r.left < -1;
          if (pastEnd) li.setAttribute("data-hub-menu-flip", "");
          else if (pastStart) li.setAttribute("data-hub-menu-flip", "start");
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
.hub-menu-parent[data-hub-menu-flip=""] > ul,
.hub-menu-parent[data-hub-menu-flip=""] > ol {
  inset-inline-start: auto !important; inset-inline-end: 0 !important;
}
.hub-menu-parent[data-hub-menu-flip="start"] > ul,
.hub-menu-parent[data-hub-menu-flip="start"] > ol {
  inset-inline-start: 0 !important; inset-inline-end: auto !important;
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

/* --- counter: a figure that counts up as it arrives --------------------- */
/* Markup: data-hub-module="counter" on a <dl>, where every <dt> counts, or on
 * the figure element itself; data-hub-counter marks any other element inside.
 * The authored text IS the final figure: its prefix, separators, decimals and
 * suffix are kept, so "12,500+" counts from 0 and ends as "12,500+" exactly.
 * Text holding no number is left alone. Does nothing at all under reduced
 * motion, so the authored figure is what shows.
 * Options: data-hub-counter-duration, milliseconds, default 1200. */
function parseFigure(text) {
  const m = text.match(/^(\D*?)(\d[\d,.\s ]*\d|\d)(.*)$/s);
  if (!m) return null;
  const raw = m[2];
  let decimals = 0, decimalSep = "", groupSep = "";
  const seps = raw.replace(/\d/g, "");
  if (seps) {
    const last = seps[seps.length - 1];
    const after = raw.length - raw.lastIndexOf(last) - 1;
    const others = seps.slice(0, -1).replace(new RegExp(`[${last === "." ? "\\." : last}]`, "g"), "");
    if ((after === 1 || after === 2) && (last === "." || (last === "," && !seps.includes(".")))
        && !(seps.length > 1 && others === "")) {
      decimals = after;
      decimalSep = last;
      groupSep = others[0] || "";
    } else {
      groupSep = last;
    }
  }
  const digits = decimalSep ? raw.split(decimalSep) : [raw];
  const whole = digits[0].replace(/\D/g, "");
  const frac = decimalSep ? digits[1].replace(/\D/g, "") : "";
  const value = Number(`${whole}.${frac || "0"}`);
  return { prefix: m[1], suffix: m[3], value, decimals, decimalSep, groupSep };
}

function formatFigure(spec, n) {
  const fixed = n.toFixed(spec.decimals);
  let [whole, frac] = fixed.split(".");
  if (spec.groupSep) whole = whole.replace(/\B(?=(\d{3})+(?!\d))/g, spec.groupSep);
  return spec.prefix + whole + (spec.decimals ? spec.decimalSep + frac : "") + spec.suffix;
}

register("counter", {
  setup(el) {
    if (reducedMotion.matches || heldStill(el)) return;
    let targets = Array.from(el.querySelectorAll("[data-hub-counter]"));
    if (!targets.length) {
      targets = el.matches("dl") ? Array.from(el.querySelectorAll("dt")) : [el];
    }
    const duration = Math.min(
      Math.max(Number(el.getAttribute("data-hub-counter-duration")) || 1200, 200), 6000);
    const items = targets.map((target) => {
      const authored = target.textContent;
      const spec = parseFigure(authored.trim());
      return spec ? { target, authored, spec } : null;
    }).filter(Boolean);
    if (!items.length) return;

    // Nothing is touched until the figure is on screen: a page whose script
    // arrived shows the authored figure until then, which is the page.
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        observer.unobserve(entry.target);
        const item = items.find((i) => i.target === entry.target);
        if (item) run(item);
      });
    }, { threshold: 0.2 });
    items.forEach((item) => observer.observe(item.target));

    function run(item) {
      const { target, spec } = item;
      const start = performance.now();
      function frame(now) {
        const p = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - p, 3);
        if (p < 1) {
          target.textContent = formatFigure(spec, spec.value * eased);
          requestAnimationFrame(frame);
          return;
        }
        // The last write is the authored text, byte for byte, never a
        // formatted copy of it: the page's figure is the page's.
        target.textContent = item.authored;
        emit(target, "counter", "done");
      }
      requestAnimationFrame(frame);
    }
  },
});

/* --- scrollspy: the contents list follows the reader -------------------- */
/* Markup: data-hub-module="scrollspy" on a <nav> whose links are hashes to
 * headings on the page. The link whose heading the reader passed last
 * carries aria-current="true" and .hub-scrollspy-current; above the first
 * heading nothing is current. Nothing moves, so there is no motion to
 * reduce. Option: data-hub-scrollspy-offset, pixels from the top of the
 * viewport at which a heading counts as passed, default 96. */
register("scrollspy", {
  setup(el) {
    const links = Array.from(el.querySelectorAll('a[href^="#"]')).map((a) => {
      const id = decodeURIComponent(a.getAttribute("href").slice(1));
      return { a, target: id ? document.getElementById(id) : null };
    }).filter((l) => l.target);
    if (links.length < 2) return;
    const offset = Number(el.getAttribute("data-hub-scrollspy-offset")) || 96;
    let current = null, ticking = false;

    function update() {
      ticking = false;
      let next = null;
      links.forEach((l) => {
        if (l.target.getBoundingClientRect().top <= offset) next = l;
      });
      if (next === current) return;
      if (current) {
        current.a.removeAttribute("aria-current");
        current.a.classList.remove("hub-scrollspy-current");
      }
      current = next;
      if (current) {
        current.a.setAttribute("aria-current", "true");
        current.a.classList.add("hub-scrollspy-current");
      }
      emit(el, "scrollspy", "change", { target: current ? current.target : null });
    }
    const schedule = () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(update);
    };
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    update();
  },
  css: `
.hub-scrollspy-current {
  text-decoration: underline; text-decoration-thickness: 2px;
  text-underline-offset: 0.2em;
}`,
});

/* --- carousel: previous and next for a rail or a radio carousel --------- */
/* Markup: data-hub-module="carousel" on the block. Two shapes are FOUND, not
 * named. A radio group - the block's own radio inputs, one per slide - moves
 * by checking the next input, and wraps at the ends. A sideways scroller -
 * the block itself or a list inside it with overflow-x auto or scroll -
 * moves by one item, and the controls disable at the ends. The two controls
 * are BUILT, so the authored render carries none; they sit inside the block,
 * sticky to its start edge so a scroller keeps them in view.
 * Options: data-hub-carousel-prev-label and data-hub-carousel-next-label,
 * default Previous and Next. Scrolling is smooth only without reduced
 * motion. Emits hub:carousel:change with the index. */
register("carousel", {
  setup(el) {
    const radios = Array.from(el.querySelectorAll('input[type="radio"]'));
    const group = radios.length ? radios.filter((r) => r.name === radios[0].name) : [];
    const scrolls = (node) => /^(auto|scroll)$/.test(getComputedStyle(node).overflowX);
    const scroller = group.length >= 2 ? null
      : (scrolls(el) ? el : Array.from(el.querySelectorAll("ul, ol")).find(scrolls));
    if (group.length < 2 && !scroller) return;

    const prevLabel = el.getAttribute("data-hub-carousel-prev-label") || "Previous";
    const nextLabel = el.getAttribute("data-hub-carousel-next-label") || "Next";

    // Where the controls go: "under" a labelled row beneath the rail, "edges"
    // a pair of round controls over its left and right, "top" a pair above it,
    // "none" no controls at all, leaving the rail to swipe and keyboard. A word this does
    // not know is read as "under": a gallery that loses its controls to a typo
    // is worse than one that keeps them in the wrong place.
    //
    // A setting is read from the block's attribute first, then from a custom
    // property its stylesheet sets (--hub-carousel-controls and the others
    // below), so a pattern's variant class can choose it. A page built before
    // either existed carries neither and gets exactly what it always had.
    const blockStyle = getComputedStyle(el);
    const setting = (name) => (el.getAttribute(`data-hub-carousel-${name}`)
      || blockStyle.getPropertyValue(`--hub-carousel-${name}`) || "").trim().toLowerCase();
    // "top" is a pair at the right above the rail, which moves below it on a
    // phone, where the thumb is.
    let placement = setting("controls") || "under";
    if (!["none", "edges", "top"].includes(placement)) placement = "under";
    // Edges lays the controls over the rail, and top sets them above it; both
    // need a block that holds still. Where the block IS the scroller they
    // would ride away with the photographs, so the row goes back underneath.
    // The attribute below says which placement is on the page, so the answer
    // is readable rather than guessed at.
    if ((placement === "edges" || placement === "top") && scroller === el) placement = "under";
    // The round look draws each control as a chevron in a circle, its word
    // kept as the accessible name; it also takes the pair away while the rail
    // has nothing to scroll. "hide" on a phone leaves swipe alone there.
    const round = setting("look") === "round";
    const phoneHide = setting("phone") === "hide";
    el.setAttribute("data-hub-carousel-controls-used", placement);
    if (placement === "none") return;
    // Edges positions the controls against the block, so the block has to be a
    // containing block. Set ON THE ELEMENT for the same reason the marquee
    // turns snapping off there: the injected stylesheet may not name anything
    // outside .hub*, and a class could not be guaranteed to outrank whatever
    // selector the page already used. Only where the page left it static, so a
    // block the page positioned itself is left exactly as it found it.
    if (placement === "edges" && getComputedStyle(el).position === "static") {
      el.style.position = "relative";
    }

    const controls = document.createElement("div");
    controls.className = `hub-carousel-controls hub-carousel-controls--${placement}`;
    if (round) controls.classList.add("hub-carousel-controls--round");
    if (phoneHide) controls.classList.add("hub-carousel-controls--phone-hide");
    const make = (cls, label) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = `hub-carousel-control ${cls}`;
      // The label is the control's accessible name in every placement. Edges
      // hides the span and draws an arrow in its place, so what a screen
      // reader announces does not change with the look.
      const text = document.createElement("span");
      text.className = "hub-carousel-control-text";
      text.textContent = label;
      b.append(text);
      controls.append(b);
      return b;
    };
    const prev = make("hub-carousel-prev", prevLabel);
    const next = make("hub-carousel-next", nextLabel);
    if (placement === "top") {
      // Above the rail from a tablet up, below it on a phone.
      const wide = window.matchMedia("(min-width: 48rem)");
      const place = () => {
        controls.classList.toggle("hub-carousel-controls--below", !wide.matches);
        if (wide.matches) el.prepend(controls); else el.append(controls);
      };
      place();
      wide.addEventListener("change", place);
    } else {
      el.append(controls);
    }

    if (group.length >= 2) {
      const indexOf = () => Math.max(group.findIndex((r) => r.checked), 0);
      const go = (step) => {
        const index = (indexOf() + step + group.length) % group.length;
        group[index].checked = true;
        group[index].dispatchEvent(new Event("change", { bubbles: true }));
        emit(el, "carousel", "change", { index });
      };
      prev.addEventListener("click", () => go(-1));
      next.addEventListener("click", () => go(1));
      return;
    }

    const list = scroller.matches("ul, ol") ? scroller
      : (scroller.querySelector("ul, ol") || scroller);
    const items = Array.from(list.children);
    const stepSize = () => (items.length > 1
      ? items[1].getBoundingClientRect().left - items[0].getBoundingClientRect().left
      : scroller.clientWidth);
    const ends = () => {
      const atStart = scroller.scrollLeft <= 1;
      const atEnd = scroller.scrollLeft + scroller.clientWidth >= scroller.scrollWidth - 1;
      prev.setAttribute("aria-disabled", String(atStart));
      next.setAttribute("aria-disabled", String(atEnd));
      // Two dead controls under a rail that fits say "there is more" when
      // there is not; the round look takes them away until there is.
      if (round) controls.hidden = atStart && atEnd;
    };
    const go = (step) => {
      const behavior = reducedMotion.matches ? "auto" : "smooth";
      scroller.scrollBy({ left: step * stepSize(), behavior });
      emit(el, "carousel", "change", { index: Math.round(scroller.scrollLeft / stepSize()) + step });
    };
    prev.addEventListener("click", () => { if (prev.getAttribute("aria-disabled") !== "true") go(-1); });
    next.addEventListener("click", () => { if (next.getAttribute("aria-disabled") !== "true") go(1); });
    scroller.addEventListener("scroll", ends, { passive: true });
    new ResizeObserver(ends).observe(scroller);
    ends();
  },
  css: `
/* The row spans the scrollport and centres its own contents, rather than being
 * a max-content box centred by auto margins. Auto margins resolve once against
 * the visible width, and the sticky offset takes over the moment the rail
 * moves, so the two place the row in different spots and it shifts under the
 * reader's thumb as they scroll. Full width has one placement at every scroll
 * position: sticky holds the row over the scrollport, justify-content centres
 * the controls inside it. */
.hub-carousel-controls { display: flex; gap: 0.5rem; }
.hub-carousel-controls--under {
  position: sticky; left: 0;
  justify-content: center; width: 100%; margin: 0.75rem 0 0;
}
/* Edges lays the pair over the rail. The row takes no pointer events, so the
 * rail underneath is still swipeable between the two controls; the controls
 * take them back. Shape and place are all this sets: the ground a control
 * needs to stay legible over a photograph is the page's to give, like every
 * other colour on it. */
.hub-carousel-controls--edges {
  position: absolute; inset: 0; margin: 0;
  align-items: center; justify-content: space-between;
  pointer-events: none;
}
.hub-carousel-controls--edges .hub-carousel-control {
  pointer-events: auto; width: 44px; padding: 0;
  justify-content: center; margin-inline: 0.5rem;
}
.hub-carousel-controls--edges .hub-carousel-control-text {
  position: absolute; width: 1px; height: 1px;
  overflow: hidden; clip-path: inset(50%); white-space: nowrap;
}
.hub-carousel-controls--edges .hub-carousel-control::after {
  content: ""; width: 0.55rem; height: 0.55rem;
  border-top: 2px solid currentColor; border-right: 2px solid currentColor;
}
.hub-carousel-controls--edges .hub-carousel-prev::after {
  transform: rotate(-135deg); margin-inline-start: 0.25rem;
}
.hub-carousel-controls--edges .hub-carousel-next::after {
  transform: rotate(45deg); margin-inline-end: 0.25rem;
}
.hub-carousel-control {
  display: inline-flex; align-items: center; min-height: 44px; min-width: 44px;
  padding: 0 1rem; border: 1.5px solid currentColor; border-radius: 999px;
  background: transparent; color: inherit;
  font: inherit; font-size: 0.85rem; font-weight: 700; cursor: pointer;
}
.hub-carousel-control[aria-disabled="true"] { opacity: 0.4; cursor: default; }
.hub-carousel-control:focus-visible { outline: 3px solid currentColor; outline-offset: 2px; }
/* Top: the pair at the right above the rail, and below it on a phone. */
.hub-carousel-controls--top { justify-content: flex-end; margin: 0 0 0.75rem; }
.hub-carousel-controls--top.hub-carousel-controls--below { margin: 0.75rem 0 0; }
.hub-carousel-controls[hidden] { display: none; }
/* Round: a chevron in a circle, the word kept for assistive technology. */
.hub-carousel-controls--round .hub-carousel-control {
  width: 44px; padding: 0; justify-content: center;
}
.hub-carousel-controls--round .hub-carousel-control-text {
  position: absolute; width: 1px; height: 1px;
  overflow: hidden; clip-path: inset(50%); white-space: nowrap;
}
.hub-carousel-controls--round .hub-carousel-control::after {
  content: ""; width: 0.55rem; height: 0.55rem;
  border-top: 2px solid currentColor; border-right: 2px solid currentColor;
}
.hub-carousel-controls--round .hub-carousel-prev::after {
  transform: rotate(-135deg); margin-inline-start: 0.25rem;
}
.hub-carousel-controls--round .hub-carousel-next::after {
  transform: rotate(45deg); margin-inline-end: 0.25rem;
}
@media (max-width: 47.99rem) {
  .hub-carousel-controls--phone-hide { display: none; }
}`,
});

/* --- signup: the sign-up opener, one question at a time ----------------- */
/* Markup: data-hub-module="signup" on a signup-card (the card set inside an
 * opener) or a signup-steps section (the full-width block), whose form holds
 * fieldsets marked data-hub-signup-part = iam, seeking, dob and email. A brand
 * whose members can give only one answer to "iam" or "seeking" carries a
 * hidden mt or lf input in place of that fieldset: the question is not asked
 * and the value is sent. The
 * authored form works as it stands and sends what a form can send without
 * script. This turns it into steps and adds what only script can send
 * correctly: several "looking for" answers, interests and a first name. The
 * hand-off URL is built by hand, because a form's own encoding writes a space
 * as "+" and the join flow reads interests as a ";" list with "%20" spaces.
 * Built pieces carry the block's own prefix (signup-card-* or signup-steps-*),
 * so the pattern's stylesheet draws them; this file decides only what shows
 * and when.
 * Options, all data-hub-signup-*: every setting and every word, with the
 * values it takes, its default and whether it has a -wide twin read from
 * 60rem, is listed in patterns/signup-card/settings.json, which
 * ci/check_signup_settings.py holds to this file. A card that sets none of
 * the settings added since 1.14 behaves exactly as it did on 1.14.0.
 * Emits hub:signup:step and hub:signup:handoff. */
const SIGNUP_WORDS = {
  "next": "Next", "back": "Back", "skip": "Skip this one", "step": "{n} of {total}",
  "seeking-help": "Pick as many as you like.",
  "intent-question": "What are you looking for?", "intent-help": "Pick any that fit.",
  "enjoy-question": "What do you enjoy?", "enjoy-help": "Pick up to {max}.",
  "tally-none": "None chosen yet.", "tally": "{n} of {max} chosen.",
  "tally-full": "{n} of {max}, the most you can pick.",
  "more": "Show {n} more",
  "name-label": "First name",
  "error-one": "Choose one to carry on.", "error-some": "Choose at least one.",
  "error-date": "Add your full date of birth.", "error-age": "You need to be 18 or over to join.",
  "error-details": "Add your first name and email, and tick the box.",
  "members": "{who} aged {ages}, here now", "who": "Men;Women;Couples;Non-binary members;Members",
  "summary-seeking": "looking for", "summary-interests": "{n} interests",
  "signs": "Capricorn;Aquarius;Pisces;Aries;Taurus;Gemini;Cancer;Leo;Virgo;Libra;Scorpio;Sagittarius",
  "done": "That's your profile started", "going": "Taking you on to finish signing up",
  "location-question": "Where do you live?", "location-help": "So we can match you with people nearby.",
  "country-label": "Country", "region-label": "Region", "town-label": "Town or city",
  "town-hint": "Type your town, or scroll the list",
  "zip-label": "ZIP code", "zip-to-lists": "Or choose your state and town",
  "zip-to-code": "Or enter your ZIP code instead", "error-zip": "Enter your 5-digit ZIP code, or choose your state and town.",
  "zip-unknown": "We don't know that ZIP code. Check it, or choose your state and town.", "largest": "Largest", "a-to-z": "A to Z",
  "places-count": "{n} towns, biggest first", "places-found": "{n} found",
  "places-more": "Keep typing to find the rest",
  "choose": "Choose\u2026", "loading": "Loading\u2026", "places-none": "No town by that name. Check the spelling.",
  "error-place": "Choose your town from the list, or skip this one.",
  "members-near": "{who} aged {ages}, near {place}", "members-in": "{who} aged {ages}, in {place}",
};
// The places files: the platform's location reference with coordinates, made by
// ci/make_places.py and published beside this file under their edition.
const SIGNUP_PLACES_EDITION = "2026-08-18.3";
// What a region is called in each of the platform's countries; region-label
// overrides it.
const SIGNUP_REGION_WORDS = {
  Argentina: "Province", Australia: "State", Brazil: "State", Canada: "Province",
  Ireland: "County", "New Zealand": "Region", "South Africa": "Province", Spain: "Region",
  UK: "County", USA: "State",
};
// Rows drawn in the town list at most; the list itself shows four and a half,
// the half row saying it scrolls.
const SIGNUP_PLACES_SHOWN = 200;
// The encouraging lines, published beside this file under their edition.
const SIGNUP_MESSAGES_EDITION = "2026-09-29.1";
const SIGNUP_PLATFORMS = ["excite", "affinity"];
// The platform's region names start with their nation where a country has
// several ("England: Avon"); the list groups them under it, spelled out here.
const SIGNUP_NATIONS = { "N.ireland": "Northern Ireland" };
const SIGNUP_LARGEST = 5;
// A region with this many towns or fewer offers them as a list to pick from;
// a bigger one is typed into, its biggest towns offered from the first tap.
const SIGNUP_PLACES_PICK = 12;
const SIGNUP_SCREENS = {
  narrow: [["iam"], ["seeking"], ["location"], ["dob"], ["intent"], ["enjoy"], ["email"]],
  wide: [["iam", "seeking"], ["location"], ["dob", "intent"], ["enjoy"], ["email"]],
};
const SIGNUP_MAX = 6;
const SIGNUP_SHOWN = 8;
// Who is ticked for "looking for" from the "I am" answer, when a page asks.
const SIGNUP_SEEKING = { opposite: { 1: [2], 2: [1], 4: [4] }, same: { 1: [1], 2: [2], 4: [4] } };
const SIGNUP_TYPES = { 1: "male", 2: "female", 4: "couple", 16: "other" };
const SIGNUP_SIGN_CUTS = [120, 219, 320, 420, 521, 621, 722, 823, 923, 1023, 1122, 1222];
const SIGNUP_GLYPHS = "♑♒♓♈♉♊♋♌♍♎♏♐";

register("signup", {
  setup(el) {
    const form = el.querySelector("form");
    // Built pieces take the class prefix of the block they are built into.
    const P = el.classList.contains("signup-card") ? "signup-card" : "signup-steps";
    const parts = {};
    if (form) {
      form.querySelectorAll("[data-hub-signup-part]").forEach((p) => {
        parts[p.getAttribute("data-hub-signup-part")] = p;
      });
    }
    // Not the markup this was written for: leave the page exactly as it is.
    if (!form || !parts.dob || !parts.email) return;
    const fixed = (n) => form.querySelector(`input[type="hidden"][name="${n}"]`);
    if ((!parts.iam && !fixed("mt")) || (!parts.seeking && !fixed("lf"))) return;

    const opt = (k) => el.getAttribute(`data-hub-signup-${k}`);
    const say = (k, vars = {}) => (opt(k) || SIGNUP_WORDS[k])
      .replace(/\{(\w+)\}/g, (m, v) => (v in vars ? vars[v] : m));
    const make = (tag, cls, text) => {
      const n = document.createElement(tag);
      if (cls) n.className = cls;
      if (text != null) n.textContent = text;
      return n;
    };
    const wide = matchMedia("(min-width: 60rem)");
    // A setting with a -wide twin: the twin from 60rem where the page gives
    // one, the setting itself everywhere else.
    const optAt = (k) => (wide.matches && el.hasAttribute(`data-hub-signup-${k}-wide`)
      ? opt(`${k}-wide`) : opt(k));
    // Which date of birth the visitor sees at this width, and where the year
    // wheel opens: an age from 18 to 90, or 0 for blank.
    const dobWay = () => (optAt("dob") === "wheel" ? "wheel" : "boxes");
    const dobStart = () => {
      const n = Number(optAt("dob-start"));
      return Number.isInteger(n) && n >= 18 && n <= 90 ? n : 0;
    };
    const calm = () => reducedMotion.matches;

    /* ---- build everything first, detached: if any of it fails, the page
       is still exactly the authored form ---- */
    const top = make("div", `${P}-top`);
    const back = make("button", `${P}-back`);
    back.type = "button";
    back.setAttribute("aria-label", say("back"));
    const bar = make("div", `${P}-bar`);
    bar.setAttribute("role", "progressbar");
    bar.setAttribute("aria-valuemin", "1");
    const count = make("span", `${P}-count`);
    count.setAttribute("aria-hidden", "true");
    top.append(back, bar, count);

    const chipStep = (key) => {
      const labels = (opt(key) || "").split(";").map((s) => s.trim()).filter(Boolean);
      if (!labels.length) return null;
      const set = make("fieldset", `${P}-step`);
      set.setAttribute("data-hub-signup-part", key);
      set.append(make("legend", `${P}-q`, say(`${key}-question`)),
        make("p", `${P}-help`, say(`${key}-help`, { max: SIGNUP_MAX })));
      const ul = make("ul", `${P}-chips`);
      ul.setAttribute("role", "list");
      labels.forEach((label, n) => {
        const box = make("input");
        box.type = "checkbox";
        box.value = label;
        const lab = make("label");
        lab.append(box, make("span", null, label));
        const li = make("li", `${P}-chip`);
        li.append(lab);
        if (n >= SIGNUP_SHOWN) li.hidden = true;
        ul.append(li);
      });
      set.append(ul);
      if (labels.length > SIGNUP_SHOWN) {
        const more = make("button", `${P}-more`, say("more", { n: labels.length - SIGNUP_SHOWN }));
        more.type = "button";
        more.addEventListener("click", () => {
          ul.querySelectorAll("li[hidden]").forEach((li) => { li.hidden = false; });
          const first = ul.children[SIGNUP_SHOWN].querySelector("input");
          more.remove();
          first.focus();
        });
        set.append(more);
      }
      if (key === "enjoy") {
        const tally = make("p", `${P}-tally`, say("tally-none"));
        tally.setAttribute("aria-live", "polite");
        set.append(tally);
      }
      return set;
    };
    parts.intent = chipStep("intent");
    parts.enjoy = chipStep("enjoy");

    /* Where the visitor lives, as far as the page's scope leaves open. The
       names are the platform's own, so the member search narrows by them
       exactly; the join flow is sent the chosen town's coordinates. */
    const scope = (opt("places") || "").split("/").map((x) => x.trim()).filter(Boolean);
    const everywhere = scope.length === 1 && scope[0].toLowerCase() === "world";
    const where = { country: everywhere ? "" : scope[0] || "", region: scope[1] || "",
      town: scope[2] || "", at: null };
    const fixedWhere = { country: !!where.country, region: !!where.region, town: !!where.town };
    // Whether the visitor is giving a postal code rather than picking from the lists.
    let zipMode = false;
    const placesUrl = (file) => new URL(file, opt("places-from")
      ? new URL(opt("places-from"), location.href)
      : new URL(`../places/${SIGNUP_PLACES_EDITION}/`, import.meta.url));
    const loaded = {};
    // Anything that goes wrong reaching the places - a bad address, the host,
    // the file - is one rejection, and the step goes quietly.
    const loadPlaces = (file) => {
      if (!loaded[file]) {
        loaded[file] = Promise.resolve().then(() => fetch(placesUrl(file), { credentials: "omit" }))
          .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))));
      }
      return loaded[file];
    };
    const countryFile = (c) => `${c.toLowerCase().replace(/ /g, "-")}.json`;
    const nationOf = (r) => (r.includes(": ") ? r.split(": ")[0] : "");
    // Shown names only: the value sent is always the platform's own spelling,
    // stray punctuation and all ("Puerto Rico,").
    const plainRegion = (r) => (r.includes(": ") ? r.split(": ").slice(1).join(": ") : r).replace(/[\s,]+$/, "");
    const regionName = (r) => (nationOf(r)
      ? `${plainRegion(r)}, ${SIGNUP_NATIONS[nationOf(r)] || nationOf(r)}` : plainRegion(r));
    let townsHere = {};
    const loc = {};
    if (scope.length && !where.town) {
      const set = make("fieldset", `${P}-step`);
      set.setAttribute("data-hub-signup-part", "location");
      set.append(make("legend", `${P}-q`, say("location-question")),
        make("p", `${P}-help`, say("location-help")));
      const pick = (key) => {
        const field = make("label", `${P}-field`);
        const select = make("select", `${P}-select`);
        field.append(make("span", null, say(`${key}-label`)), select);
        field.hidden = true;
        set.append(field);
        return select;
      };
      if (!fixedWhere.country) loc.country = pick("country");
      // The postal code: a field and its two links, shown only where the
      // country has codes the join flow reads.
      if (!fixedWhere.region) {
        const zipField = make("label", `${P}-field`);
        const zip = make("input");
        zip.inputMode = "numeric";
        zip.autocomplete = "postal-code";
        zip.maxLength = 5;
        zipField.append(make("span", null, say("zip-label")), zip);
        const zipNote = make("p", `${P}-place-note`, say("zip-unknown"));
        zipNote.setAttribute("aria-live", "polite");
        zipNote.hidden = true;
        const toLists = make("button", `${P}-switch`, say("zip-to-lists"));
        toLists.type = "button";
        const toCode = make("button", `${P}-switch`, say("zip-to-code"));
        toCode.type = "button";
        const zipBlock = make("div", `${P}-postal`);
        zipBlock.append(zipField, zipNote, toLists);
        zipBlock.hidden = true;
        toCode.hidden = true;
        set.append(zipBlock);
        Object.assign(loc, { zip, zipBlock, zipNote, toLists, toCode });
      }
      if (!fixedWhere.region) loc.region = pick("region");
      loc.townPick = pick("town");
      const field = make("label", `${P}-field`);
      const town = make("input");
      const drop = make("div", `${P}-places`);
      const count = make("p", `${P}-places-count`);
      const list = make("ul", `${P}-places-list`);
      const rest = make("p", `${P}-places-count`, say("places-more"));
      drop.append(count, list, rest);
      const id = `hub-signup-places-${Math.random().toString(36).slice(2, 8)}`;
      list.id = id;
      list.setAttribute("role", "listbox");
      drop.hidden = true;
      town.setAttribute("role", "combobox");
      town.setAttribute("aria-autocomplete", "list");
      town.setAttribute("aria-expanded", "false");
      town.setAttribute("aria-controls", id);
      town.autocomplete = "off";
      town.spellcheck = false;
      town.placeholder = say("town-hint");
      field.append(make("span", null, say("town-label")), town);
      // The field and its list together, so the list opens over the card
      // rather than lengthening it.
      const place = make("div", `${P}-place`);
      place.append(field, drop);
      place.hidden = true;
      const none = make("p", `${P}-place-note`, say("places-none"));
      none.setAttribute("data-hub-signup-warn", "");
      none.hidden = true;
      set.append(place, none);
      // The region and town lists together, so a postal code can stand in for them.
      loc.lists = make("div", `${P}-lists`);
      [loc.region && loc.region.closest("label"), loc.townPick.closest("label"), place, none]
        .filter(Boolean).forEach((n) => loc.lists.append(n));
      set.append(loc.lists);
      if (loc.toCode) set.append(loc.toCode);
      loc.town = town;
      loc.townField = place;
      loc.list = list;
      loc.drop = drop;
      loc.count = count;
      loc.rest = rest;
      loc.none = none;
      parts.location = set;
    }

    const nameField = make("label", `${P}-field`);
    const nameInput = make("input");
    nameInput.autocomplete = "given-name";
    nameInput.setAttribute("autocapitalize", "words");
    nameField.append(make("span", null, say("name-label")), nameInput);

    const errors = {};
    Object.keys(parts).forEach((k) => {
      if (!parts[k]) { delete parts[k]; return; }
      errors[k] = make("p", `${P}-error`);
      errors[k].setAttribute("role", "alert");
      errors[k].hidden = true;
    });

    const prize = make("p", `${P}-reward`);
    prize.setAttribute("aria-live", "polite");
    prize.hidden = true;

    // What the visitor has built so far, in their own answers' words.
    const summary = make("p", `${P}-summary`);
    summary.setAttribute("aria-live", "polite");
    summary.hidden = true;

    const next = make("button", `${P}-next`, say("next"));
    next.type = "button";
    const skip = make("button", `${P}-skip`, say("skip"));
    skip.type = "button";

    // The member strip: in the card on a phone, beside it on a wide screen.
    const guid = (/\/register\/([0-9a-f-]{36})/i.exec(form.action) || [])[1] || opt("guid");
    const strip = guid ? make("div", `${P}-members`) : null;
    const wall = guid ? make("div", `${P}-wall`) : null;
    [strip, wall].forEach((box) => { if (box) { box.hidden = true; box.setAttribute("aria-live", "polite"); } });

    // The wheel, when asked for: it writes into the authored boxes, so every
    // answer is read the same way whichever the visitor used.
    const boxes = ["dd", "dm", "dy"].map((n) => form.elements[n]);
    let wheels = null;
    // Each wheel's list, rows and reader, filled in once they listen.
    const wheelCols = [];
    let wheelsPlaced = false;
    // The wheels take their place once, the first time they show at a width
    // where they are the date of birth.
    function wheelsShown() {
      if (!wheelCols.length || wheelsPlaced || dobWay() !== "wheel" ||
          !parts.dob.hasAttribute("data-hub-signup-on")) return;
      wheelsPlaced = true;
      placeWheels();
    }
    /* Turn each wheel to what the box under it holds - a date typed at the
       other width - or, where it is empty, to where the page asks the year to
       open. A typed value no wheel holds is left as typed. */
    function placeWheels() {
      wheelCols.forEach(({ ul, rows, step, pick }, k) => {
        const have = boxes[k] ? boxes[k].value.trim() : "";
        const want = have || (k === 2 && dobStart() ? String(new Date().getFullYear() - dobStart()) : "");
        const i = rows.findIndex((li) => (want === "" ? li.dataset.hubSignupValue === ""
          : li.dataset.hubSignupValue !== "" && +li.dataset.hubSignupValue === +want));
        if (i < 0 || Math.round(ul.scrollTop / step()) === i) return;
        ul.scrollTo({ top: i * step(), behavior: "instant" });
        pick();
      });
    }
    if (opt("dob") === "wheel" || opt("dob-wide") === "wheel") {
      wheels = make("div", `${P}-wheels`);
      const labels = Array.from(parts.dob.querySelectorAll(`.${P}-field > span`))
        .map((s) => s.textContent.trim());
      const year = new Date().getFullYear();
      const lang = document.documentElement.lang || undefined;
      [Array.from({ length: 31 }, (_, i) => [i + 1, i + 1]),
        Array.from({ length: 12 }, (_, i) => [i + 1, new Date(2000, i, 1).toLocaleString(lang, { month: "short" })]),
        Array.from({ length: 73 }, (_, i) => [year - 18 - i, year - 18 - i]),
      ].forEach((items, k) => {
        const col = make("div", `${P}-wheel-col`);
        const ul = make("ul", `${P}-wheel`);
        ul.setAttribute("role", "listbox");
        ul.setAttribute("aria-label", labels[k] || "");
        ul.tabIndex = 0;
        // Two blank rows at each end let the first and last values reach
        // the band in the middle.
        const spacer = () => { const s = make("li"); s.setAttribute("aria-hidden", "true"); return s; };
        ul.append(spacer(), spacer());
        [["", "–"]].concat(items).forEach(([v, t]) => {
          const li = make("li", null, String(t));
          li.setAttribute("role", "option");
          li.dataset.hubSignupValue = v;
          ul.append(li);
        });
        ul.append(spacer(), spacer());
        col.append(make("span", `${P}-wheel-label`, labels[k] || ""), ul);
        wheels.append(col);
      });
    }

    /* ---- reading the answers ---- */
    const val = (n) => ((form.elements[n] && form.elements[n].value) || "").trim();
    const mt = () => (form.querySelector('input[name="mt"]:checked') || fixed("mt") || {}).value || "";
    const lf = () => (parts.seeking
      ? Array.from(parts.seeking.querySelectorAll('input[name="lf"]:checked'))
        .reduce((sum, r) => sum + Number(r.value), 0)
      : Number((fixed("lf") || {}).value) || 0);
    const picked = (key) => (parts[key]
      ? Array.from(parts[key].querySelectorAll("input:checked")).map((b) => b.value) : []);
    const consent = parts.email.querySelector('input[type="checkbox"]');
    const age = () => {
      const d = +val("dd"); const m = +val("dm"); const y = val("dy");
      if (!d || !m || !/^\d{4}$/.test(y)) return null;
      const born = new Date(+y, m - 1, d);
      if (born.getMonth() !== m - 1 || born.getDate() !== d) return null;
      const now = new Date();
      let years = now.getFullYear() - +y;
      if (now < new Date(now.getFullYear(), m - 1, d)) years -= 1;
      return years;
    };
    const problem = {
      iam: () => (mt() ? "" : "error-one"),
      seeking: () => (lf() ? "" : "error-some"),
      dob: () => { const a = age(); return a == null ? "error-date" : a < 18 ? "error-age" : ""; },
      intent: () => (picked("intent").length ? "" : "error-some"),
      enjoy: () => "",
      location: () => (zipMode ? (where.zip ? "" : "error-zip") : where.town ? "" : "error-place"),
      email: () => (nameInput.value.trim() && val("em") && form.elements.em.checkValidity() &&
        (!consent || consent.checked) ? "" : "error-details"),
    };

    /* ---- the steps ---- */
    let screens = [];
    let at = 0;
    let byPointer = false;
    const plan = () => (wide.matches ? SIGNUP_SCREENS.wide : SIGNUP_SCREENS.narrow)
      .map((s) => s.filter((p) => parts[p])).filter((s) => s.length);

    function ready() {
      const ok = screens[at].every((p) => !problem[p]());
      next.toggleAttribute("data-hub-signup-ready", ok);
    }

    function show(to, dir) {
      const before = form.offsetHeight;
      at = Math.max(0, Math.min(to, screens.length - 1));
      const on = screens[at];
      Object.keys(parts).forEach((k) => {
        const here = on.includes(k);
        parts[k].toggleAttribute("data-hub-signup-on", here);
        parts[k].classList.remove("hub-signup-fwd", "hub-signup-back");
        if (here && dir) parts[k].classList.add(dir > 0 ? "hub-signup-fwd" : "hub-signup-back");
      });
      // A wheel can only be turned once it is drawn.
      wheelsShown();
      el.classList.toggle("hub-signup-first", at === 0);
      el.classList.toggle("hub-signup-last", at === screens.length - 1);
      bar.replaceChildren(...screens.map((_, k) => {
        const seg = make("span", `${P}-seg`);
        if (k < at) seg.setAttribute("data-hub-signup-done", "");
        if (k === at) seg.setAttribute("data-hub-signup-now", "");
        if (dir > 0 && k === at - 1) seg.setAttribute("data-hub-signup-just", "");
        return seg;
      }));
      const words = say("step", { n: at + 1, total: screens.length });
      bar.setAttribute("aria-valuemax", String(screens.length));
      bar.setAttribute("aria-valuenow", String(at + 1));
      bar.setAttribute("aria-valuetext", words);
      count.textContent = words;
      skip.hidden = !(on.length === 1 && (on[0] === "enjoy" || on[0] === "location"));
      // The line answers what the visitor just did: going back, it is not
      // about the step they return to, so it goes until the next answer.
      if (dir < 0) cheer.hidden = true;
      next.removeAttribute("data-hub-signup-ready");
      recap();
      ready();
      if (dir) {
        if (!calm() && before) {
          const after = form.offsetHeight;
          form.style.height = `${before}px`;
          form.style.overflow = "hidden";
          void form.offsetHeight;
          form.style.transition = "height .34s cubic-bezier(.2,.8,.2,1)";
          form.style.height = `${after}px`;
          setTimeout(() => { form.style.height = form.style.overflow = form.style.transition = ""; }, 380);
        }
        const legend = parts[on[0]].querySelector("legend");
        legend.tabIndex = -1;
        legend.focus({ preventScroll: true });
        // A phone brings the card up at every step; a wide screen only when
        // the step's button would otherwise sit below the fold.
        if (at > 0 && opt("settle") !== "off") {
          const card = form.getBoundingClientRect();
          const low = (at === screens.length - 1 ? form.querySelector(`.${P}-submit`) : next).getBoundingClientRect();
          if (!wide.matches || card.top < 0 || low.bottom > window.innerHeight) {
            form.scrollIntoView({ block: "start", behavior: calm() ? "auto" : "smooth" });
          }
        }
        members();
      }
      if (dir > 0 && at === screens.length - 1) speak("last");
      emit(el, "signup", "step", { step: at + 1, of: screens.length });
    }

    function check() {
      let first = null;
      screens[at].forEach((p) => {
        const fault = problem[p]();
        errors[p].hidden = !fault;
        errors[p].textContent = fault ? say(fault) : "";
        parts[p].querySelectorAll("input, select").forEach((i) => i.toggleAttribute("aria-invalid", !!fault));
        if (fault && !first) first = Array.from(parts[p].querySelectorAll("input, select")).find((i) => !i.closest("[hidden]") && (!i.value || i.type === "radio" || i.type === "checkbox")) || parts[p];
      });
      if (first) first.focus();
      return !first;
    }

    /* ---- the encouraging lines: one after each answer, never the same twice ---- */
    const cheer = make("p", `${P}-cheer`);
    cheer.setAttribute("aria-live", "polite");
    cheer.hidden = true;
    const talk = P === "signup-card" && opt("messages") !== "off";
    const platform = SIGNUP_PLATFORMS.includes(opt("platform")) ? opt("platform") : "";
    const replaceLines = opt("say-mode") === "replace";
    // The published lines are English: a page in another language speaks only
    // its own, and keeps its answers' capitals.
    const pageLang = (el.closest("[lang]") || document.documentElement).lang || "";
    const english = !pageLang || /^en(-|$)/i.test(pageLang);
    const own = (k) => (opt(`say-${k}`) || "").split(";").map((x) => x.trim()).filter(Boolean);
    const ownLabels = {};
    (opt("say-labels") || "").split(";").forEach((pair) => {
      const i = pair.indexOf(":");
      if (i > 0) {
        ownLabels[pair.slice(0, i).trim().toLowerCase()] = pair.slice(i + 1).split("|")
          .map((x) => x.trim()).filter(Boolean);
      }
    });
    const saidLines = new Set();
    let lineBook = null;
    const messagesUrl = (file) => new URL(file, opt("messages-from")
      ? new URL(opt("messages-from"), location.href)
      : new URL(`../messages/${SIGNUP_MESSAGES_EDITION}/`, import.meta.url));
    const getJson = (file) => Promise.resolve().then(() => fetch(messagesUrl(file), { credentials: "omit" }))
      .then((r) => (r.ok ? r.json() : {})).catch(() => ({}));
    // An interest's lines are its own platform's: a file that says it is
    // another's is not used, because Excite's are written for adults.
    const loadLines = () => lineBook || (lineBook = Promise.all([
      getJson("steps.json"), platform ? getJson(`${platform}.json`) : Promise.resolve({}),
    ]).then(([steps, own2]) => {
      const interests = {};
      if (own2.platform === platform) {
        Object.entries(own2.interests || {}).forEach(([k, v]) => { interests[k.toLowerCase()] = v; });
      }
      return { steps: steps.steps || {}, interests };
    }));
    const fillLine = (line, vars) => line.replace(/\{(who|Who|place|Place|interest|Interest)\}/g, (m, k) => {
      const v = vars[k.toLowerCase()] || "";
      return k[0] === k[0].toUpperCase() ? v.charAt(0).toUpperCase() + v.slice(1) : v;
    });
    const fits = (line, vars) => Array.from(line.matchAll(/\{(\w+)\}/g)).every((m) => vars[m[1].toLowerCase()]);
    function speak(moment, vars = {}, label = "") {
      if (!talk) return;
      (english ? loadLines() : Promise.resolve({ steps: {}, interests: {} })).then((book) => {
        const mine = own(moment);
        let pool;
        if (moment === "interest") {
          const mineHere = ownLabels[label.toLowerCase()] || [];
          const bookHere = book.interests[label.toLowerCase()] || [];
          pool = replaceLines && mineHere.length ? mineHere : mineHere.concat(bookHere);
          if (!pool.length) pool = replaceLines && mine.length ? mine : mine.concat(book.steps.interest || []);
        } else {
          pool = replaceLines && mine.length ? mine : mine.concat(book.steps[moment] || []);
        }
        pool = pool.filter((l) => fits(l, vars));
        const fresh = pool.filter((l) => !saidLines.has(l));
        const from = fresh.length ? fresh : pool;
        if (!from.length) return;
        const line = from[Math.floor(Math.random() * from.length)];
        saidLines.add(line);
        cheer.textContent = fillLine(line, vars);
        cheer.hidden = false;
        cheer.removeAttribute("data-hub-signup-said");
        void cheer.offsetWidth;
        cheer.setAttribute("data-hub-signup-said", "");
      });
    }
    // A place is said once when it is settled, however it was given: picked,
    // typed in full, or found from a ZIP code.
    let placeSaid = "";
    const sayPlace = (place) => {
      if (place && place !== placeSaid) {
        placeSaid = place;
        speak("location", { place });
      }
    };
    const whoWords = () => (parts.seeking ? Array.from(parts.seeking.querySelectorAll('input[name="lf"]:checked'))
      .map((i) => (i.closest("label") ? i.closest("label").textContent.trim() : "")).filter(Boolean)
      .join(" & ")[english ? "toLowerCase" : "toString"]() : "");

    // English answers read on in lower case; a page in another language keeps
    // its answers' capitals, as German nouns need.
    function recap() {
      const words = (input) => {
        const label = input && input.closest("label");
        return label ? label.textContent.trim() : "";
      };
      const who = parts.iam ? words(form.querySelector('input[name="mt"]:checked')) : "";
      const seek = parts.seeking ? Array.from(parts.seeking.querySelectorAll('input[name="lf"]:checked'))
        .map(words).filter(Boolean).join(" & ")[english ? "toLowerCase" : "toString"]() : "";
      const a = age();
      const liked = picked("intent").length + picked("enjoy").length;
      const bits = [[who, seek ? `${say("summary-seeking")} ${seek}` : ""].filter(Boolean).join(" "),
        parts.location && (where.town || where.zip) ? where.town || where.zip : "",
        a && a >= 18 ? String(a) : "", liked ? say("summary-interests", { n: liked }) : ""].filter(Boolean);
      const text = bits.join(" \u00b7 ");
      summary.textContent = text ? text.charAt(0).toUpperCase() + text.slice(1) : "";
      summary.hidden = at === 0 || !text;
    }

    function reward() {
      const kind = opt("reward") || "sign";
      const a = age();
      prize.hidden = kind === "none" || a == null || a < 18;
      if (prize.hidden) return;
      const m = +val("dm"); const d = +val("dd");
      let i = SIGNUP_SIGN_CUTS.findIndex((c) => m * 100 + d < c);
      if (i < 0) i = 0;
      const text = kind === "age" ? String(a) : `${a} · ${say("signs").split(";")[i] || ""} ${SIGNUP_GLYPHS[i]}`;
      if (prize.textContent === text) return;
      prize.textContent = text;
      prize.removeAttribute("data-hub-signup-pop");
      void prize.offsetWidth;
      prize.setAttribute("data-hub-signup-pop", "");
    }

    function tally() {
      if (!parts.enjoy) return;
      const all = Array.from(parts.enjoy.querySelectorAll("input"));
      const n = all.filter((b) => b.checked).length;
      all.forEach((b) => { b.disabled = !b.checked && n >= SIGNUP_MAX; });
      parts.enjoy.querySelector(`.${P}-tally`).textContent =
        say(n === 0 ? "tally-none" : n >= SIGNUP_MAX ? "tally-full" : "tally", { n, max: SIGNUP_MAX });
      skip.hidden = n > 0 || !(screens[at].length === 1 && screens[at][0] === "enjoy");
    }

    /* ---- members, live: the brand's own, never older than the visit ---- */
    let asked = "";
    let painted = false;
    // When each face was last shown: a new answer shows faces not seen yet, then
    // the ones seen longest ago, so the strip changes wherever the brand has
    // more than four to choose from.
    const seenFaces = new Map();
    let paints = 0;
    // A full date of birth brings members of that age as it is typed, not at
    // the next step.
    let dobWait;
    function dobChanged() {
      clearTimeout(dobWait);
      dobWait = setTimeout(() => { const a = age(); if (a && a >= 18) members(); }, 350);
    }
    // One of the two shows, by width: the faces in the card on a phone, the
    // row beside the card on a wide screen.
    const place = () => {
      // A card set inside another opener has no row beside it: its faces stay.
      const beside = Boolean(wall && wall.isConnected);
      if (strip) strip.hidden = !painted || (wide.matches && beside);
      if (wall) wall.hidden = !painted || !wide.matches;
    };
    function members() {
      const want = lf();
      if (!strip) return;
      const a = age();
      const levels = [["country", where.country], ["region", where.region], ["city", where.town]]
        .filter(([, v]) => v);
      const query = (band, depth) => {
        // Two dozen to choose four from, so each answer can bring new faces.
        const q = new URLSearchParams({ guid, myBrandMembersOnly: "TRUE", results: "24", imageSize: "160" });
        // Before "looking for" is answered: every member the brand has.
        if (want) q.set("membertypes", Object.keys(SIGNUP_TYPES).filter((b) => want & b).map((b) => SIGNUP_TYPES[b]).join(","));
        if (band && a) { q.set("ageMin", String(Math.max(18, a - 8))); q.set("ageMax", String(Math.min(90, a + 8))); }
        levels.slice(0, depth).forEach(([k, v]) => q.set(k, v));
        return q;
      };
      const key = query(true, levels.length).toString();
      if (key === asked) return;
      asked = key;
      const get = (q) => fetch(`https://api.hub-cdn.com/api/hs/quicksearch?${q}`, { credentials: "omit" })
        .then((r) => (r.ok ? r.json() : [])).then((d) => (Array.isArray(d) ? d : []));
      // A thin result widens a step at a time rather than showing one lonely
      // face: the age band goes first, then the town, then the region. The
      // country a page is about is never dropped.
      const tries = [[true, levels.length]];
      if (a) tries.push([false, levels.length]);
      for (let d = levels.length - 1; d >= (fixedWhere.country ? 1 : 0); d -= 1) tries.push([false, d]);
      // The line under the faces names the widest place any of them came from,
      // never a narrower claim than the faces make.
      const widen = (found, n) => (found.length >= 4 || n >= tries.length ? Promise.resolve(found)
        : get(query(...tries[n])).then((more) => {
          if (more.length) near = Math.min(near, tries[n][1]);
          return widen(found.concat(more), n + 1);
        }));
      let near = levels.length;
      get(query(...tries[0]))
        .then((found) => widen(found, 1))
        .catch(() => [])
        .then((found) => { if (key === asked) paint(found, levels[near - 1]); });
    }

    function paint(found, around) {
      const liked = new Set(picked("intent").concat(picked("enjoy")).map((s) => s.toLowerCase()));
      const seen = new Set();
      const shown = found.filter((m) => m && m.MemberImage && !seen.has(m.MemberImage) && seen.add(m.MemberImage))
        .map((m, i) => ({ m, i, score: String(m.Interests || "").split(",")
          .filter((s) => liked.has(s.trim().toLowerCase())).length }))
        .sort((x, y) => (seenFaces.get(x.m.MemberImage) ?? -1) - (seenFaces.get(y.m.MemberImage) ?? -1) || y.score - x.score || x.i - y.i)
        .slice(0, 4).map((x) => x.m);
      paints += 1;
      shown.forEach((m) => seenFaces.set(m.MemberImage, paints));
      painted = shown.length > 0;
      el.toggleAttribute("data-hub-signup-members", painted);
      place();
      if (!shown.length) return;
      const want = lf();
      const ages = shown.map((m) => +m.MemberAge).filter(Boolean);
      const low = Math.min(...ages); const high = Math.max(...ages);
      const who = say("who").split(";")[{ 1: 0, 2: 1, 4: 2, 16: 3 }[want] ?? 4] || "";
      const ages2 = low === high ? low : `${low}–${high}`;
      // Named for the narrowest place the faces came from, never a wider claim.
      const caption = !around || around[0] === "country" || !parts.location ? say("members", { who, ages: ages2 })
        : around[0] === "region" ? say("members-in", { who, ages: ages2, place: regionName(around[1]) })
          : say("members-near", { who, ages: ages2, place: around[1] });
      const photo = (m, size) => {
        const img = make("img");
        img.src = m.MemberImage;
        img.alt = "";
        img.width = img.height = size;
        img.loading = "lazy";
        return img;
      };
      const faces = make("span", `${P}-faces`);
      shown.forEach((m) => { const f = make("span", `${P}-face`); f.append(photo(m, 72)); faces.append(f); });
      strip.replaceChildren(faces, make("p", null, caption));
      const ul = make("ul");
      ul.setAttribute("role", "list");
      shown.forEach((m) => {
        const li = make("li");
        li.append(photo(m, 160), make("b", null, m.MemberName || ""), make("span", null, m.MemberAge || ""));
        ul.append(li);
      });
      wall.replaceChildren(make("p", `${P}-wall-title`, caption), ul);
      [strip, wall].forEach((box) => {
        box.removeAttribute("data-hub-signup-new");
        void box.offsetWidth;
        box.setAttribute("data-hub-signup-new", "");
      });
    }

    /* ---- the hand-off ---- */
    function handoff() {
      // The link every join link on the platform carries, then the answers on
      // top: each parameter the visitor arrived with (the first of each), the
      // page's attribution (pn), and its language where the page's differs
      // from the brand's -- as the platform's own script writes them onto the
      // page's join links, which a form is not.
      const params = new Map();
      const first = (k, v) => { if (!params.has(k)) params.set(k, v); };
      const action = new URL(form.action, location.href);
      action.searchParams.forEach((v, k) => first(k, v));
      new URLSearchParams(location.search).forEach((v, k) => first(k, v));
      const info = window.templateInfo;
      if (info && info.is_prod === true) {
        const kind = location.href.includes("/amp") ? "aiamp" : "ai";
        const name = info.template_name ? `~${String(info.template_name).replace(/ /g, "-").toLowerCase()}` : "";
        params.set("pn", `${kind}${name}~${info.page_guid}~${location.pathname}`);
      }
      const set = (k, v) => { if (v !== "" && v != null) params.set(k, String(v)); };
      form.querySelectorAll('input[type="hidden"][name]').forEach((h) => set(h.name, h.value));
      if (info && info.template_lang && info.template_lang !== info.template_brand_lang) {
        params.set("culture", info.template_lang);
      }
      set("mt", mt());
      set("lf", lf() || "");
      set("dd", String(+val("dd")));
      set("dm", String(+val("dm")));
      set("dy", val("dy"));
      set("firstname", nameInput.value.trim());
      set("em", btoa(String.fromCharCode(...new TextEncoder().encode(val("em")))));
      const chosen = picked("intent").concat(picked("enjoy"));
      if (chosen.length) params.set("interests", chosen);
      // A town with coordinates skips the join flow's own location step; one
      // without leaves it to ask.
      if (where.zip) set("zipCode", where.zip);
      else if (where.at) { set("lat", where.at[0]); set("long", where.at[1]); }
      const query = Array.from(params, ([k, v]) => `${encodeURIComponent(k)}=${
        Array.isArray(v) ? v.map(encodeURIComponent).join("%3B") : encodeURIComponent(v)}`)
        .join("&").replace(/%7E/gi, "~").replace(/%2F/gi, "/");
      const url = `${action.origin}${action.pathname}?${query}`;
      const done = make("div", `${P}-finish`);
      done.setAttribute("role", "status");
      done.innerHTML = '<svg viewBox="0 0 64 64" width="64" height="64" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="32" cy="32" r="28"/><path d="M20 33l8 8 16-17"/></svg>';
      done.append(make("p", null, say("done")), make("small", null, say("going")));
      form.append(done);
      el.classList.add("hub-signup-going");
      emit(el, "signup", "handoff", { url });
      setTimeout(() => location.assign(url), calm() ? 200 : 1100);
      // Back from the join flow restores this page as it was left: give the
      // visitor the form again rather than the finish.
      setTimeout(() => { el.classList.remove("hub-signup-going"); done.remove(); }, 3000);
    }

    /* ---- commit: put it all in, and only then switch the steps on ---- */
    if (parts.seeking) parts.seeking.querySelectorAll('input[name="lf"]').forEach((r) => {
      const v = Number(r.value);
      // A summed answer is what several ticks make; it is not offered twice.
      if (v & (v - 1)) r.closest("li").setAttribute("data-hub-signup-sum", "");
      r.type = "checkbox";
      r.required = false;
      r.checked = false;
    });
    if (parts.seeking) parts.seeking.querySelector("legend").after(make("p", `${P}-help`, say("seeking-help")));
    const anchor = parts.dob;
    [parts.enjoy, parts.intent].forEach((p) => { if (p) anchor.after(p); });
    if (parts.location) parts.dob.before(parts.location);
    parts.email.querySelector("legend").after(nameField);
    parts.dob.append(prize);
    if (wheels) {
      parts.dob.querySelector(`.${P}-dob`).after(wheels);
      parts.dob.toggleAttribute("data-hub-signup-wheel", dobWay() === "wheel");
    }
    Object.keys(parts).forEach((k) => parts[k].append(errors[k]));
    const actions = form.querySelector(`.${P}-actions`) || form;
    actions.prepend(next, skip);
    form.prepend(top);
    top.after(summary);
    summary.after(cheer);
    if (strip) summary.after(strip);
    const beside = el.querySelector(`.${P}-aside`) || el.querySelector(`.${P}-copy`);
    if (wall && beside) beside.append(wall);
    form.noValidate = true;
    el.classList.add("hub-signup-live");

    screens = plan();
    show(0, 0);
    members();

    /* ---- listening, inside the block only ---- */
    form.addEventListener("pointerdown", () => { byPointer = true; });
    form.addEventListener("keydown", () => { byPointer = false; });
    let seekingTouched = false;
    const seekingFrom = SIGNUP_SEEKING[opt("seeking")];
    const seekFrom = () => {
      if (!seekingFrom || seekingTouched || !parts.seeking) return;
      const want = seekingFrom[mt()] || [];
      parts.seeking.querySelectorAll('input[name="lf"]').forEach((r) => {
        r.checked = want.includes(Number(r.value));
      });
      members();
      ready();
    };
    // A fixed "I am" is answered before anyone arrives.
    if (!parts.iam) seekFrom();
    form.addEventListener("change", (e) => {
      if (e.target.name === "lf") seekingTouched = true;
      if (e.target.name === "mt") seekFrom();
      if (parts.enjoy && parts.enjoy.contains(e.target)) tally();
      if (e.target.name === "lf") members();
      if (e.target.name === "mt") speak("iam");
      if (e.target.name === "lf" && whoWords()) speak("seeking", { who: whoWords() });
      if (e.target.checked && e.target.type === "checkbox" &&
          ((parts.intent && parts.intent.contains(e.target)) || (parts.enjoy && parts.enjoy.contains(e.target)))) {
        speak("interest", { interest: e.target.value }, e.target.value);
      }
      // A tapped single answer moves on once its tick has been seen; a
      // keyboard never moves on by itself.
      recap();
      if (e.target.name === "mt" && byPointer && screens[at].length === 1 && !problem.iam()) {
        setTimeout(() => show(at + 1, 1), calm() ? 0 : 420);
      }
      ready();
    });
    form.addEventListener("input", (e) => {
      reward(); recap(); ready();
      if (parts.dob.contains(e.target)) dobChanged();
    });
    boxes.forEach((box, k) => {
      if (!box) return;
      box.addEventListener("input", () => {
        box.value = box.value.replace(/\D/g, "");
        const full = k === 2 ? box.value.length === 4 : box.value.length === 2 || +box.value > (k ? 1 : 3);
        if (full && k < 2 && boxes[k + 1]) boxes[k + 1].focus();
      });
      box.addEventListener("keydown", (e) => {
        if (e.key === "Backspace" && !box.value && k) boxes[k - 1].focus();
      });
    });
    if (wheels) {
      wheels.querySelectorAll(`.${P}-wheel`).forEach((ul, k) => {
        const rows = Array.from(ul.querySelectorAll('[role="option"]'));
        const step = () => rows[0].getBoundingClientRect().height || 44;
        const pick = () => {
          const i = Math.round(ul.scrollTop / step());
          rows.forEach((li, n) => li.setAttribute("aria-selected", String(n === i)));
          boxes[k].value = (rows[i] && rows[i].dataset.hubSignupValue) || "";
          reward();
          ready();
          dobChanged();
        };
        let wait;
        ul.addEventListener("scroll", () => { clearTimeout(wait); wait = setTimeout(pick, 90); });
        ul.addEventListener("keydown", (e) => {
          if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
          e.preventDefault();
          ul.scrollBy({ top: e.key === "ArrowDown" ? step() : -step() });
        });
        rows.forEach((li, n) => li.addEventListener("click", () => ul.scrollTo({ top: n * step() })));
        wheelCols.push({ ul, rows, step, pick });
        // Read only where the wheel is what shows: where the boxes show, they
        // keep what they hold.
        if (dobWay() === "wheel") pick();
      });
      wheelsShown();
    }
    /* ---- the places: loaded once, asked as far as the scope leaves open ---- */
    // Without its places the step cannot be answered: it goes, and the join
    // flow asks for the location itself.
    const dropPlaces = () => {
      if (!parts.location) return;
      const was = screens[at] && screens[at][0];
      parts.location.remove();
      delete parts.location;
      screens = plan();
      const i = screens.findIndex((sc) => sc.includes(was));
      show(i < 0 ? Math.min(at, screens.length - 1) : i, 0);
    };
    const fill = (select, names, label) => {
      select.replaceChildren(new Option(say("choose"), ""),
        ...names.slice().sort((x, y) => label(x).localeCompare(label(y))).map((n) => new Option(label(n), n)));
      select.closest("label").hidden = false;
    };
    const fillRegions = (select, data) => {
      const names = Object.keys(data.regions);
      const size = (n) => (data.sizes || {})[n] || 0;
      const group = (label, list, show) => {
        const g = document.createElement("optgroup");
        g.label = label;
        list.forEach((n) => g.append(new Option(show(n), n)));
        return g;
      };
      const az = (list, show) => list.slice().sort((x, y) => show(x).localeCompare(show(y)));
      const kids = [new Option(say("choose"), "")];
      const long = names.length > SIGNUP_PLACES_PICK && Object.keys(data.sizes || {}).length;
      if (long) {
        kids.push(group(say("largest"), names.slice().sort((x, y) => size(y) - size(x)).slice(0, SIGNUP_LARGEST),
          regionName));
      }
      const nations = [...new Set(names.map(nationOf))];
      if (nations.length > 1) {
        const total = (nat) => names.filter((n) => nationOf(n) === nat).reduce((t, n) => t + size(n), 0);
        nations.sort((x, y) => total(y) - total(x)).forEach((nat) => kids.push(group(
          SIGNUP_NATIONS[nat] || nat || say("a-to-z"), az(names.filter((n) => nationOf(n) === nat), plainRegion),
          plainRegion)));
      } else if (long) {
        kids.push(group(say("a-to-z"), az(names, regionName), regionName));
      } else {
        az(names, regionName).forEach((n) => kids.push(new Option(regionName(n), n)));
      }
      select.replaceChildren(...kids);
      select.disabled = false;
      select.closest("label").hidden = false;
    };
    const chooseTown = (name) => {
      where.town = name || "";
      where.at = name ? townsHere[name] || null : null;
      if (loc.town && name) loc.town.value = name;
      if (loc.list) closeList();
      sayPlace(name);
      members();
      recap();
      ready();
    };
    const showRegion = (name) => {
      where.region = name;
      townsHere = (name && country && country.regions[name]) || {};
      chooseTown("");
      if (!loc.town) return;
      const names = Object.keys(townsHere);
      const few = names.length > 0 && names.length <= SIGNUP_PLACES_PICK;
      loc.town.value = "";
      loc.none.hidden = true;
      if (few) fill(loc.townPick, names, (n) => n);
      loc.townPick.closest("label").hidden = !few;
      loc.townField.hidden = !name || few || !names.length;
    };
    let country = null;
    const postalWay = ["first", "lists", "off"].includes(opt("postal")) ? opt("postal") : "first";
    // Which the visitor sees: the code or the lists. Either clears the other's answer.
    const useCode = (on) => {
      if (!loc.zip) return;
      const offered = !!(country && country.postal) && postalWay !== "off";
      zipMode = offered && on;
      loc.zipBlock.hidden = !zipMode;
      loc.lists.hidden = zipMode;
      loc.toCode.hidden = zipMode || !offered;
      loc.zip.value = "";
      loc.zipNote.hidden = true;
      where.zip = "";
      if (loc.region) loc.region.value = "";
      showRegion("");
      recap();
      ready();
    };
    const readCode = () => {
      loc.zip.value = loc.zip.value.replace(/\D/g, "").slice(0, 5);
      const code = loc.zip.value;
      where.zip = "";
      where.region = "";
      where.town = "";
      where.at = null;
      loc.zipNote.hidden = true;
      recap();
      ready();
      if (code.length < 5 || !country || !country.postal) return;
      loadPlaces(country.postal.replace("{}", code[0])).then((data) => {
        if (loc.zip.value !== code) return;
        const hit = data.codes[code];
        if (!hit) {
          loc.zipNote.textContent = say("zip-unknown");
          loc.zipNote.setAttribute("data-hub-signup-warn", "");
          loc.zipNote.hidden = false;
          return;
        }
        where.zip = code;
        where.region = data.regions[hit[0]];
        where.town = hit[1] || "";
        // The place the code was read as, so the visitor sees it understood.
        loc.zipNote.textContent = [where.town, regionName(where.region)].filter(Boolean).join(", ");
        loc.zipNote.removeAttribute("data-hub-signup-warn");
        loc.zipNote.hidden = false;
        sayPlace(where.town || regionName(where.region));
        members();
        recap();
        ready();
      }).catch(() => {
        loc.zipNote.textContent = say("zip-unknown");
        loc.zipNote.setAttribute("data-hub-signup-warn", "");
        loc.zipNote.hidden = false;
      });
    };
    const showCountry = (name) => {
      where.country = name;
      country = null;
      showRegion(fixedWhere.region ? where.region : "");
      if (loc.region) {
        // The field stays in place while the country's places arrive, saying so,
        // rather than vanishing and coming back.
        loc.region.replaceChildren(new Option(say("loading"), ""));
        loc.region.disabled = true;
        loc.region.closest("label").hidden = !name;
      }
      if (!name) return Promise.resolve();
      if (loc.zip) useCode(false);
      return loadPlaces(countryFile(name)).then((data) => {
        if (where.country !== name) return;
        country = data;
        if (loc.zip) useCode(postalWay === "first");
        if (loc.region) {
          const regionWord = opt("region-label") || SIGNUP_REGION_WORDS[name] || say("region-label");
          loc.region.closest("label").firstChild.textContent = regionWord;
          fillRegions(loc.region, data);
        }
        if (fixedWhere.region) {
          if (!data.regions[where.region]) throw new Error(`no region ${where.region}`);
          showRegion(where.region);
        }
      });
    };
    let active = -1;
    const closeList = () => {
      loc.drop.hidden = true;
      loc.list.replaceChildren();
      loc.town.setAttribute("aria-expanded", "false");
      loc.town.removeAttribute("aria-activedescendant");
      active = -1;
    };
    const mark = (i) => {
      const rows = Array.from(loc.list.children);
      active = rows.length ? (i + rows.length) % rows.length : -1;
      rows.forEach((li, n) => li.setAttribute("aria-selected", String(n === active)));
      if (active >= 0) {
        loc.town.setAttribute("aria-activedescendant", rows[active].id);
        rows[active].scrollIntoView({ block: "nearest" });
      }
    };
    const suggest = () => {
      const typed = loc.town.value.trim().toLowerCase();
      const names = Object.keys(townsHere);
      const exact = names.find((n) => n.toLowerCase() === typed);
      where.town = exact || "";
      where.at = exact ? townsHere[exact] || null : null;
      sayPlace(exact);
      // Nothing typed yet: every town in the region, biggest first, while the
      // field has focus - a list that scrolls, not a sample that looks whole.
      if (!typed) {
        loc.none.hidden = true;
        if (document.activeElement !== loc.town) { closeList(); return; }
      }
      const score = (n) => { const l = n.toLowerCase(); return l.startsWith(typed) ? 0 : l.split(/[\s-]/).some((w) => w.startsWith(typed)) ? 1 : l.includes(typed) ? 2 : 3; };
      // The places files list each region's towns biggest first; within a kind
      // of match, that order stands.
      const found = typed ? names.filter((n) => score(n) < 3).sort((x, y) => score(x) - score(y)) : names;
      const hits = found.slice(0, SIGNUP_PLACES_SHOWN);
      loc.none.hidden = hits.length > 0;
      loc.count.textContent = say(typed ? "places-found" : "places-count", { n: found.length });
      loc.rest.hidden = found.length <= hits.length;
      loc.list.replaceChildren(...hits.map((n, i) => {
        const li = make("li", null, n);
        li.id = `${loc.list.id}-${i}`;
        li.setAttribute("role", "option");
        li.setAttribute("aria-selected", "false");
        li.addEventListener("pointerdown", (e) => e.preventDefault());
        li.addEventListener("click", () => { chooseTown(n); loc.town.focus(); });
        return li;
      }));
      const open = hits.length > 0 && !(hits.length === 1 && hits[0] === exact);
      loc.drop.hidden = !open;
      loc.list.scrollTop = 0;
      loc.town.setAttribute("aria-expanded", String(open));
      active = -1;
    };
    if (parts.location) {
      if (loc.town) {
        loc.town.addEventListener("input", () => { suggest(); members(); });
        loc.town.addEventListener("focus", () => { if (!loc.town.value.trim()) suggest(); });
        loc.townPick.addEventListener("change", () => chooseTown(loc.townPick.value));
        loc.town.addEventListener("keydown", (e) => {
          if (loc.drop.hidden) return;
          if (e.key === "ArrowDown" || e.key === "ArrowUp") {
            e.preventDefault();
            mark(active + (e.key === "ArrowDown" ? 1 : -1));
          } else if (e.key === "Enter" && active >= 0) {
            e.preventDefault();
            chooseTown(loc.list.children[active].textContent);
          } else if (e.key === "Escape") {
            closeList();
          }
        });
        loc.town.addEventListener("blur", () => setTimeout(() => { if (loc.list) closeList(); }, 150));
      }
      if (loc.region) loc.region.addEventListener("change", () => showRegion(loc.region.value));
      if (loc.zip) {
        loc.zip.addEventListener("input", readCode);
        loc.toLists.addEventListener("click", () => { useCode(false); if (loc.region) loc.region.focus(); });
        loc.toCode.addEventListener("click", () => { useCode(true); loc.zip.focus(); });
      }
      if (loc.country) loc.country.addEventListener("change", () => showCountry(loc.country.value).catch(dropPlaces));
      const start = fixedWhere.country ? showCountry(where.country)
        : loadPlaces("index.json").then((index) => fill(loc.country, Object.keys(index.countries), (n) => n));
      start.catch(dropPlaces);
    } else if (where.town) {
      // A town given in full is not asked: its coordinates still go.
      loadPlaces(countryFile(where.country)).then((data) => {
        where.at = ((data.regions[where.region] || {})[where.town]) || null;
      }).catch(() => {});
    }

    next.addEventListener("click", () => { if (check()) show(at + 1, 1); });
    back.addEventListener("click", () => show(at - 1, -1));
    skip.addEventListener("click", () => show(at + 1, 1));
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      if (at < screens.length - 1) { if (check()) show(at + 1, 1); return; }
      if (check()) handoff();
    });
    wide.addEventListener("change", () => {
      place();
      if (wheels) {
        // Wheel at one width, boxes at the other: the boxes keep the answer,
        // and a wheel coming into view is turned to it.
        const hadWheel = parts.dob.hasAttribute("data-hub-signup-wheel");
        parts.dob.toggleAttribute("data-hub-signup-wheel", dobWay() === "wheel");
        if (!hadWheel && dobWay() === "wheel") wheelsPlaced = false;
      }
      const was = screens[at][0];
      screens = plan();
      show(Math.max(0, screens.findIndex((s) => s.includes(was))), 0);
    });
  },
  css: `
.hub-signup-live :is(.signup-steps-card-title, .signup-card-title),
.hub-signup-live [data-hub-signup-part]:not([data-hub-signup-on]),
.hub-signup-live [data-hub-signup-sum],
.hub-signup-live [data-hub-signup-wheel] :is(.signup-steps-dob, .signup-card-dob),
.hub-signup-live [data-hub-signup-part]:not([data-hub-signup-wheel]) > :is(.signup-steps-wheels, .signup-card-wheels),
.hub-signup-live:not(.hub-signup-last) :is(.signup-steps-submit, .signup-card-submit),
.hub-signup-live:not(.hub-signup-last) :is(.signup-steps-note, .signup-card-note),
.hub-signup-last :is(.signup-steps-next, .signup-card-next),
.hub-signup-going form > :not(:is(.signup-steps-finish, .signup-card-finish)),
.hub-signup-live [hidden] { display: none !important; }
.hub-signup-first :is(.signup-steps-back, .signup-card-back) { visibility: hidden; }
@media (prefers-reduced-motion: no-preference) {
  .hub-signup-fwd { animation: hub-signup-fwd .36s cubic-bezier(.2,.8,.2,1) both; }
  .hub-signup-back { animation: hub-signup-back .36s cubic-bezier(.2,.8,.2,1) both; }
  @keyframes hub-signup-fwd { from { opacity: 0; transform: translateX(32px); } }
  @keyframes hub-signup-back { from { opacity: 0; transform: translateX(-32px); } }
  .hub-signup-live [data-hub-signup-just]::after { animation: hub-signup-shine .8s .15s ease-out both; }
  @keyframes hub-signup-shine { from { transform: translateX(-100%); } to { transform: translateX(100%); } }
  .hub-signup-live [data-hub-signup-new] img { animation: hub-signup-rise .45s cubic-bezier(.2,.8,.2,1) both; }
  .hub-signup-live [data-hub-signup-new] :nth-child(2) > img { animation-delay: .07s; }
  .hub-signup-live [data-hub-signup-new] :nth-child(3) > img { animation-delay: .14s; }
  .hub-signup-live [data-hub-signup-new] :nth-child(4) > img { animation-delay: .21s; }
  @keyframes hub-signup-rise { from { opacity: 0; transform: translateY(8px) scale(.94); } }
  .hub-signup-live [data-hub-signup-pop] { animation: hub-signup-pop .4s cubic-bezier(.3,1.6,.5,1); }
  .hub-signup-live [data-hub-signup-said] { animation: hub-signup-said .4s ease-out both; }
  @keyframes hub-signup-said { from { opacity: 0; transform: translateY(4px); } }
  @keyframes hub-signup-pop { from { transform: scale(.6); } }
  .hub-signup-live [data-hub-signup-ready]::after { animation: hub-signup-nudge .7s ease-in-out 2; }
  @keyframes hub-signup-nudge { 50% { translate: 5px 0; } }
  .hub-signup-going circle { stroke-dasharray: 176; animation: hub-signup-ring .55s cubic-bezier(.2,.8,.2,1) both; }
  .hub-signup-going path { stroke-dasharray: 44; animation: hub-signup-tick .35s .5s ease-out both; }
  @keyframes hub-signup-ring { from { stroke-dashoffset: 176; } to { stroke-dashoffset: 0; } }
  @keyframes hub-signup-tick { from { stroke-dashoffset: 44; } to { stroke-dashoffset: 0; } }
  .hub-signup-live :is(.signup-steps-wheel, .signup-card-wheel) { scroll-behavior: smooth; }
}`,
});

/* ----------------------------------------------------------------------- */

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => initAll());
} else {
  initAll();
}

window.HubBehaviours = { version: "1.15.0", initAll, register };
export { initAll, register };
