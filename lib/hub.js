/* hub-behaviours v1.1 — the controlled behaviour library.
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

/* ----------------------------------------------------------------------- */

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => initAll());
} else {
  initAll();
}

window.HubBehaviours = { version: "1.1.0", initAll, register };
export { initAll, register };
