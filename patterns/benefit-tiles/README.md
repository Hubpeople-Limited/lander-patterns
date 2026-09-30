# benefit-tiles

**What it is and when to use it.** A run of two to six tall bordered tiles,
each with a small filled icon badge at the top and its title and copy pinned to
the floor of the tile, so tiles holding unequal amounts of copy still read as
one set. Use it for a benefit or feature set the brand has **no photography
for** — that is the gap it fills, and the only reason to reach for it over
`media-card-grid` or `steps-numbered`, both of which *are* the photograph and
are the better choice the moment real images exist. Do **not** use it for an
ordered process (the tiles are peers and nothing in them says first or last —
that is `steps-numbered`), for pricing tiers, or for a set of more than six,
which is two sets rather than one. Do not use it for more than a couple of
sentences a tile either; the tall proportion is there to give short copy air,
not to hold a paragraph.

**What it needs.** Two to six real benefits or features, each with a short
title and one or two sentences the brand can stand behind. One real icon image
per tile, square and at least 44px (the badge renders it at 22px, so 2× for
retina), each with its own alt text — or `alt=""` where the title already says
the same thing, which is the usual case for a decorative glyph. **Set `width`
and `height` on each `<img>` to the icon's real intrinsic pixel size**; the
shipped `44`/`44` is a stand-in and stops layout shift only by accident.
Duplicate the single `<li>` once per benefit. The badge is filled with
`--color-primary`, so the glyph must be supplied in the brand's
`--color-on-primary` colour: the contract states that pair at 4.5:1 and states
nothing about any other ink on a brand colour. The tiles carry no section
heading of their own — their `<h3>`s expect an `<h2>` above the section, which
is what `heading-block` supplies.

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
second run of identical bordered boxes on one page is the sign that two
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

**The layout follows the count.** Below 48rem every count is a horizontal
scroll-snap track. From 48rem the count decides the grid, with no hole in it:
two sit side by side, and above 64rem keep the width a tile has in a row of
three; three are one row; four are two by two, then four up above 64rem; five
are three over two, the two centred; six are three over three. Tiles are 24rem
tall from 48rem, and take the tall height again above 64rem only in a single
row. A browser without `:has()` gets the four-tile grid for any count. The phone
track bleeds deliberately: the section drops its right padding and the track
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
