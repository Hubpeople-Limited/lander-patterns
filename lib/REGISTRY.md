# Behaviour registry

One line per behaviour in `hub.js`. A pattern may declare a behaviour in its
`behaviours:` header field and hook it with `data-hub-module="<name>"` only if
the name is listed here — CI enforces both directions.

**Delivery is out of the pattern's hands.** A site may carry this file as its
own asset and reference it with a single `<script type="module">` tag, or a
platform may inject it. A pattern never carries a tag itself and never knows
which arrived; the
hooks are inert data attributes until the platform injects the library on
served pages. Behaviours must therefore always be pure enhancements — the
no-JS render is the page.

| Behaviour | Since | What it does | Markup contract |
|---|---|---|---|
| `reveal` | v1 | Entrance animation as content scrolls into view; staggers direct children when `data-hub-reveal-children` is present; does nothing under reduced motion | `data-hub-module="reveal"` on the element, optional `data-hub-reveal-children` on a container |
| `tabs` | v1.1 | Builds a tablist from the panels' own labels and shows one panel at a time, with roving `tabindex`, arrow keys, Home and End; no tab control ships in the markup, so with no library every panel renders stacked under its own heading. Emits `hub:tabs:change`. Panel entrance is skipped under reduced motion | `data-hub-module="tabs"` on the panels container, `data-hub-tab-label="…"` on each direct-child panel, optional `data-hub-tabs-label` naming the tablist |
