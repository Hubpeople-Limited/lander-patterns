# portrait-wall

**What it is and when to use it.** A lattice of portrait tiles three rows deep
and three, five or seven columns across, the centre one of which gets its own
slot for the strongest photograph — the same size as its neighbours and where
the eye lands. A full-section
wall whose only job is scale — "there are a lot of people here" — and it has no
heading, no copy and no link. **It is decorative and carries no message on its
own, so it needs a section around it that does**: a heading block above it, or a
CTA below it, saying who these people are and what the visitor should do. Drop
it onto a page by itself and you have shipped a screen of faces that argues
nothing. It makes a poor hero (there is nothing to read) and no substitute for
`media-card-grid` (those tiles are links to somewhere), and it reads best on a
page with no other set of image cards — a second grid of photographs is where
a page stops looking designed.

**What it needs.** Nine, fifteen or twenty-one **real** member photographs,
all different, portrait-crop and at least 420px wide (tiles render around 220px
at the widest, so 2× for retina). Those counts fill the lattice — three rows of
an odd number of columns — so with twelve, use nine. The markup ships fifteen:
delete the outer ring for nine, or duplicate it as a fourth layer for
twenty-one, numbering its slots on from `tile-15`. This is the library's
hungriest pattern and the obvious place to reach for stock; it works best
without. Bought smiles read as bought smiles, and the one claim the wall makes — that these are
members — is the one it then can't support. With fewer than nine, a smaller set
belongs in `gallery-scroll` or `media-card-grid`. Also needed: a short label
for `wall-label` naming what the wall shows, and real content around it.

**What shows where.** Phones show nine: the centre column and the inner ring.
The outer ring joins from 48rem and a fourth from 64rem, so put the weakest
photographs outermost and the strongest in the centre column and the focal
cell. Nine keeps three columns at the tile size fifteen would have. `width` and
`height` ship as `600`/`800`; set both to each real image's intrinsic pixels.

**The wall is one image, and every alt is empty.** The tiles are decorative
individually even though the wall is not: no single face carries information the
page needs, and a description of every stranger on it is a wall of noise
rather than an equivalent. So the grid is `role="img"` with one `aria-label`,
the composite-image treatment, and every `<img>` inside it takes `alt=""`. A
screen reader announces the wall once, in the terms the design actually means —
"members of <brand>" — and moves on. Keep `wall-label` filled: an `img` role
with no accessible name is worse than no role at all.

**Not on a page with `member-strip`.** That pattern is these specific people by name, beside the ask; this one is scale and atmosphere with every face anonymous. A page carrying both makes the same gesture twice, and the anonymous version undercuts the named one.

**Pairing.** `heading-block` directly above it is the intended shape: the
heading makes the claim, the wall is the evidence. It sits equally well
immediately above a closing CTA. No `avoid-with` edge is declared, but treat it
as one page's worth of photography — putting it on a page that also carries
`media-card-grid`, `gallery-scroll`, `steps-numbered` or `testimonial-grid`
gives you two runs of portraits competing, and neither reads as deliberate.
`one-per-page: yes`.

**Brand adaptability.** `--card-radius` restyles every tile at once, and it is
the dial that decides whether the wall reads soft or editorial.
`--card-shadow` lifts the tiles; a wall of shadows at close spacing can muddy, so
the pattern reads `--portrait-wall-shadow` first — set that to `none` on the
brand to flatten the wall without touching its cards elsewhere. Two more of the
pattern's own dials: `--portrait-wall-ratio` (3 / 4) changes the tile crop, and
`--portrait-wall-gap` the spacing. Width follows `--container-max`.

**Layout, and what must not be edited.** The layers are separate elements
stacked on the wall's own tracks with `grid-template-columns: subgrid` /
`grid-template-rows: subgrid`, each spanning `1 / -1`. That is the whole idea:
each ring is addressed as a unit by `:nth-of-type` instead of every tile being
positioned by hand. Keep the order — centre column, then rings outward, then
the focal cell last — and the counts: two in the centre, six in every ring.
Every column counts from `--portrait-wall-mid`, the centre column; the wall
widens by moving that one number when a ring is present (`:has()`), and a
browser without `:has()` keeps the nine-tile wall. The focal cell has no ratio
of its own — it takes its height from the tiles beside it and its photograph is
laid over it, which is why that image is absolutely positioned. Browsers
without `subgrid` fall back to `display: contents` on the layers plus dense
auto-placement, which resolves the identical lattice at every count.

**Behaviour (gated).** The grid carries the `reveal` hook with
`data-hub-reveal-children`, which staggers the rings outward from the centre
and then the focal image where the platform serves the behaviour library.
Without it the attributes are inert and the wall renders in full — nothing
here is hidden by default, and nothing should be.
