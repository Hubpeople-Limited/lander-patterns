# hero-bento

**What it is and when to use it.** A homepage or landing opener set in a grid
of tiles: the headline and one line in one tile, the join in another, and
beside them a photograph, a few live members, the brand's own interests, a
second photograph and, when the brand wants one, its membership figure. It
shows at once what the brand is, who is on it and what it is about, which no
single-picture opener can. It holds `signup-card` in place of its join button,
as the other openers do.

**Each tile reads best filled from the brand's own material.** Delete a tile's
whole `<li>` and the tiles beside it grow to close the row: every tile but the
headline and the join may go, and the grid reads best with at least one more.

| Tile | What fills it best |
|---|---|
| photograph | the brand's own picture, at least 1600px wide, or the library's placeholder |
| members | three members the platform writes in at render, with its own join tile; nothing authored |
| interests | the brand's own interest labels, one chip each, spelled as its join flow spells them |
| second photograph | a second picture of the brand's own, at least 800px square, or the placeholder |
| figure | the platform's own member count, rounded the way a sentence says it, when the brand wants a figure on the page |

The library ships no figure, name or label of its own: a sample figure on a
live page would read to a visitor as the brand's.

**The member loop** is the platform's, exactly as in `member-grid`: author it
empty, keep `data-members-strict="true"` in lowercase, and spell any country
or region as `lib/places` holds it (a wrong one is ignored, not refused). Below
three members the platform writes the empty-state sentence instead, so that
sentence needs to be true. Previews show sample members. Every setting the
loop takes is listed in `member-grid`'s `settings.json`.

**Three axes.** `words`: `start`, the headline and the join down the left with
the tiles to their right (the default); `end`, mirrored; `top`, the headline
and the join side by side across the top and the tiles in a band under them.
On a phone the headline and the join come first, then the tiles. `cells`:
`ruled`, one block divided by hairlines of `--color-rule`, like a printed
grid; `spaced`, separate cards in the brand's own card style
(`--card-radius`, `--card-border`, `--card-shadow`). `motion`: still by
default; on `moving` the tiles ease in one after another through the
behaviour library's `reveal`, never the headline or the join, and a member
lifts a little under the pointer, both inside the reduced-motion guard.

**Holding the card.** Put `signup-card` where the join button is. Its tile
sits under the headline (beside it on `top`), and on a phone the card's first
question is on the first screen below the site header. The tile is the card:
the form fills it edge to edge, and the tile's own edge is its one border. On a
laptop the headline keeps its height and the card's tile takes the rest, the
card at its top, so its question holds still from step to step.

**What it needs.** A headline and one sentence in the brand's words; the
photographs with alt text; the interest labels; the words for the members
tile's title, its links and its empty state; a figure as above. The first
photograph ships `fetchpriority="high"` and never takes `loading="lazy"`; set
`width` and `height` to the files' own pixels.

**Not on a page with another opener** (`hero-centred`, `hero-collage`,
`hero-overlay`, `hero-portrait`, `hero-split`, `hero-squeeze`, `hero-stated`,
`signup-steps`): each opens the page and carries its `h1`; a page opens once.

**Pairing.** `steps-plain` below it for how joining works, `faq-details`,
`cta-band` to close. On a landing page, `heading-block` and `benefit-tiles`.

**Brand adaptability.** Every ink is a stated pair: `--color-text` and
`--color-text-soft` on `--color-bg`, `--color-surface` or
`--color-surface-soft`, and `--color-on-primary` on the figure's
`--color-primary`. `--font-heading` carries the headline at up to 3.5rem and
the figure at up to 2.75rem; `--chip-radius` shapes the interest chips. Heights
come from the width, never the viewport.
