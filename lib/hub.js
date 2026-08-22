/* hub-behaviours v1 — the platform-controlled behaviour library.
 *
 * Delivery is the platform's job: pages never carry this file or any script
 * tag for it. Markup opts in with data-hub-module="<name>" attributes, which
 * are inert until the platform injects this module — so a page written today
 * works today, and gains behaviour the day delivery ships.
 *
 * Contract (see CONTRIBUTING.md, "Behaviours"):
 *   - every behaviour is a progressive enhancement over working HTML/CSS;
 *   - init is idempotent and error-contained per element;
 *   - one global (window.HubBehaviours), events as hub:<name>:<event>,
 *     options only from data-hub-* attributes;
 *   - all motion honours prefers-reduced-motion.
 */

const registry = new Map();
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
    if (el.hasAttribute(INITIALISED)) return;
    el.setAttribute(INITIALISED, "");
    new Set(el.getAttribute("data-hub-module").split(/\s+/)).forEach((name) => {
      const setup = registry.get(name);
      if (!setup) return; // unknown module: inert, never an error
      try {
        setup(el);
      } catch (err) {
        // One broken element never takes down the page or its siblings.
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

/* ----------------------------------------------------------------------- */

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => initAll());
} else {
  initAll();
}

window.HubBehaviours = { version: "1.0.0", initAll, register };
export { initAll, register };
