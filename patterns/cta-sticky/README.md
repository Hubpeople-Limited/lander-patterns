# cta-sticky

**What it is and when to use it.** A fixed bar at the bottom of the phone
viewport carrying one join button, so the primary action stays in the thumb
zone however far the visitor scrolls. One of the best-evidenced mobile
conversion patterns. Use it on any conversion page longer than about two
mobile screens. Do **not** use it on short pages where the hero CTA is already
visible (it duplicates), on pages whose job is not conversion (an article a
reader is studying can carry it, a support page should not), or twice on one
page.

**What it needs.** Nothing content-wise — the button is the platform's join
placeholder. The one obligation is mechanical: the page-bottom clearance rule
ships in the CSS so the bar never covers the footer's last links.

**Pairing.** This is page furniture, not a section: it is decided once for any
page longer than about two screens, rather than chosen to follow something. It
carries no `pairs-with` for that reason. The one thing it cannot share a page
with is `cta-curtain` — a full-screen finale and a fixed bar fight for the same
moment and the same thumb. Only one fixed bottom element per page in general,
so if the site adds a cookie bar, one of them has to move.

**Brand adaptability.** `--btn-radius` and the primary-colour pair are the
whole look. The bar sits on `--color-surface` and is separated from the
content behind it twice over — a hairline and a soft upward shadow — because
`--color-rule` is decorative by contract and a brand may set it to almost
nothing, and a fixed bar that blends into the page is a bar nobody can see the
edge of. Hidden from 60rem up — desktop relies on the page's inline CTAs.

One implementation note: the stylesheet uses media *range* syntax
(`@media (width < 60rem)`) because a min/max pair leaves a fractional-pixel
gap under browser zoom. Range syntax has been Baseline widely-available since
2025; on anything older the bar degrades to a plain in-page link.
