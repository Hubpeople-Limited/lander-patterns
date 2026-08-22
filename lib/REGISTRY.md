# Behaviour registry

One line per behaviour in `hub.js`. A pattern may declare a behaviour in its
`behaviours:` header field and hook it with `data-hub-module="<name>"` only if
the name is listed here — CI enforces both directions.

**Delivery is gated on the platform**: pages never carry a script tag; the
hooks are inert data attributes until the platform injects the library on
served pages. Behaviours must therefore always be pure enhancements — the
no-JS render is the page.

| Behaviour | Since | What it does | Markup contract |
|---|---|---|---|
| `reveal` | v1 | Entrance animation as content scrolls into view; staggers direct children when `data-hub-reveal-children` is present; does nothing under reduced motion | `data-hub-module="reveal"` on the element, optional `data-hub-reveal-children` on a container |
