# benefit-tiles

**What it is and when to use it.** A run of four tall bordered tiles, each with
a small filled icon badge at the top and its title and copy pinned to the floor
of the tile, so tiles holding unequal amounts of copy still read as one set.
Use it for a benefit or feature set the brand has **no photography for** — that
is the gap it fills, and the only reason to reach for it over `media-card-grid`
or `steps-numbered`, both of which *are* the photograph and are the better
choice the moment real images exist. Do **not** use it for an ordered process
(the tiles are peers and nothing in them says first or last — that is
`steps-numbered`), for pricing tiers, or for a set of two, three or five: the
row is four wide and drops to two, so any other count leaves a hole in it. Do
not use it for more than a couple of sentences a tile either; the tall
proportion is there to give short copy air, not to hold a paragraph.

**What it needs.** Four real benefits or features, each with a short title and
one or two sentences the brand can stand behind. One real icon image per tile,
square and at least 44px (the badge renders it at 22px, so 2× for retina), each
with its own alt text — or `alt=""` where the title already says the same
thing, which is the usual case for a decorative glyph. **Set `width` and
`height` on each `<img>` to the icon's real intrinsic pixel size**; the shipped
`44`/`44` is a stand-in and stops layout shift only by accident. Duplicate the
single `<li>` to four. The badge is filled with `--color-primary`, so the glyph
must be supplied in the brand's `--color-on-primary` colour: the contract
states that pair at 4.5:1 and states nothing about any other ink on a brand
colour. The tiles carry no section heading of their own — their `<h3>`s expect
an `<h2>` above the section, which is what `heading-block` supplies.

**Pairing.** `heading-block` directly above it, carrying the eyebrow, the
section title and the intro line. Place the section early: it is the "what you
get" argument, and it reads best before the proof and the join. It sets no
`avoid-with` edge on purpose. It is the one card run in the library that costs
no photography, so ruling it out alongside the image-led runs would leave a
brand with no images nothing at all to use for a feature set. Keep it away from
them as a **neighbour** all the same: a run of bordered tiles directly under
`media-card-grid` or `steps-numbered` reads as the same section twice, because
the composition — tall card, copy driven to the floor — is the same one and
only the fill differs. `one-per-page: yes` for the same reason turned inward: a
second run of four identical bordered boxes on one page is the sign that two
sets are really one set.

**Brand adaptability.** `--card-border`, `--card-radius` and `--card-shadow`
set nearly all of the feel — hairline-and-square reads editorial, soft-and-
shadowed reads friendly. The tile is `--color-surface` with all three of those
on it rather than a border alone, which matters: a brand may legitimately set
`--card-border: 1px solid transparent` and hand the job to the shadow, and the
tile still has to be a tile. `--chip-radius` shapes the badge, from a circle at
`999px` to a hard square at `0`. Two dials belong to the pattern:
`--benefit-tiles-badge-fill` (defaults to `--color-primary` — `color-mix()` it
toward `--color-surface` for the softer pastel badge) and
`--benefit-tiles-badge-size` (3rem). `--font-heading` carries the tile titles;
their colour is `--color-text` rather than `--color-heading`, because the title
clamps down to 20px, below the 24px the heading token is contracted for, and
because it sits on a surface — `--color-heading` promises 3:1 against
`--color-bg` and nothing at all against a card, where two patterns have already
been caught at 2.36:1 and 2.71:1.

**The responsive cascade is three stages, not two.** Four up above 64rem; two
up from 48rem to 64rem, where the tile also gives back the height it needed as
a full-width card; and below 48rem a horizontal scroll-snap track. That last
stage bleeds deliberately: the section drops its right padding and the track
carries the trailing inset instead, so the next tile is cut by the viewport
edge rather than stopping neatly short of it. The cut tile is the affordance —
which is why the scrollbar is hidden — and it is the whole reason the phone
layout invites a swipe. Browsers make a scrolling region keyboard-reachable on
their own, so the track takes no `tabindex`, which would otherwise leave a dead
tab stop on the grid at every width above 48rem; it styles its own focus ring.

**Behaviour (gated).** The track carries the `reveal` hook: where the platform
serves the behaviour library the tiles fade and rise in as they scroll into
view, staggered, and reduced-motion visitors get nothing. Without the library
the attributes are inert and the section renders complete — the pattern ships
no hidden state of its own and must never gain one, because the no-JS render is
the page. The pattern's own CSS declares `motion: none`.
