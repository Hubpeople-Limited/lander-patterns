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
| `marquee` | v1.3 | Moves a rail along by itself and builds the control that stops it; clones the run once so the loop is seamless, with the copies hidden from assistive technology and out of the tab order; halts on hover, on focus, while a visitor drags it, and when it scrolls out of view. Does nothing at all under reduced motion, so no control appears either. With no library the block is the rail it was authored as. Emits `hub:marquee:paused` and `hub:marquee:resumed` | `data-hub-module="marquee"` on the block whose own list is the scroller; optional `data-hub-marquee-speed` in pixels per second (default 30) and `data-hub-marquee-pause-label` |
| `reveal` | v1 | Entrance animation as content scrolls into view; staggers direct children when `data-hub-reveal-children` is present; does nothing under reduced motion | `data-hub-module="reveal"` on the element, optional `data-hub-reveal-children` on a container |
| `drawer` | v1.2 | Closes a `<details>` drawer on `Escape` and on a press on its backdrop, and holds the page still behind it while it is open; with no library the drawer still opens, closes and takes the keyboard, because the disclosure is doing that. Modal only while the stylesheet has the panel fixed to the viewport, so the same markup at a width where the menu is an ordinary row is left alone. Emits `hub:drawer:open` and `hub:drawer:close`; it moves nothing itself | `data-hub-module="drawer"` on a `<details>` whose `<summary>` is the control and whose other element child is the panel; the backdrop is that `<details>`'s own `::before` |
| `tabs` | v1.1 | Builds a tablist from the panels' own labels and shows one panel at a time, with roving `tabindex`, arrow keys, Home and End; no tab control ships in the markup, so with no library every panel renders stacked under its own heading. Emits `hub:tabs:change`. Panel entrance is skipped under reduced motion | `data-hub-module="tabs"` on the panels container, `data-hub-tab-label="…"` on each direct-child panel, optional `data-hub-tabs-label` naming the tablist |
