# portrait-wall

**What it is and when to use it.** A five-by-three lattice of portrait tiles
with a larger focal photograph in the centre cell. It is a full-section image
wall whose only job is scale — "there are a lot of people here" — and it has no
heading, no copy and no link. **It is decorative and carries no message on its
own, so it needs a section around it that does**: a heading block above it, or a
CTA below it, saying who these people are and what the visitor should do. Drop
it onto a page by itself and you have shipped a screen of faces that argues
nothing. Do not use it as a hero (there is nothing to read), as a substitute for
`media-card-grid` (those tiles are links to somewhere), or on any page that
already runs a set of image cards — a second grid of photographs is where a page
stops looking designed.

**What it needs.** Fifteen **real** member photographs, all different, portrait-
crop and at least 600px wide (tiles render around 300px at the widest, so 2× for
retina). This is the library's hungriest pattern and the obvious place to reach
for stock: don't. Fifteen bought smiles read as fifteen bought smiles, and the
one claim the wall makes — that these are members — is the one it then can't
support. If the brand has fewer than fifteen real photographs, this is the wrong
pattern; a smaller set belongs in `gallery-scroll` or `media-card-grid`. Also
needed: a short label for `wall-label` naming what the wall shows, and real
content in the sections around it.

The six tiles in the first layer are hidden below 48rem, so put the weakest six
there and the strongest in the centre column and the focal cell. `width` and
`height` ship as `600`/`800`; set both to each real image's intrinsic pixels.

**The wall is one image, and every alt is empty.** The tiles are decorative
individually even though the wall is not: no single face carries information the
page needs, and fifteen descriptions of fifteen strangers is a wall of noise
rather than an equivalent. So the grid is `role="img"` with one `aria-label`,
the composite-image treatment, and every `<img>` inside it takes `alt=""`. A
screen reader announces the wall once, in the terms the design actually means —
"members of <brand>" — and moves on. Keep `wall-label` filled: an `img` role
with no accessible name is worse than no role at all.

**Pairing.** `heading-block` directly above it is the intended shape: the
heading makes the claim, the wall is the evidence. It sits equally well
immediately above a closing CTA. No `avoid-with` edge is declared, but treat it
as one page's worth of photography — putting it on a page that also carries
`media-card-grid`, `gallery-scroll`, `steps-numbered` or `testimonial-grid`
gives you two runs of portraits competing, and neither reads as deliberate.
`one-per-page: yes`.

**Brand adaptability.** `--card-radius` restyles all fifteen tiles at once, and
it is the dial that decides whether the wall reads soft or editorial.
`--card-shadow` lifts the tiles; fifteen shadows at close spacing can muddy, so
the pattern reads `--portrait-wall-shadow` first — set that to `none` on the
brand to flatten the wall without touching its cards elsewhere. Two more of the
pattern's own dials: `--portrait-wall-ratio` (3 / 4) changes the tile crop, and
`--portrait-wall-gap` the spacing. Width follows `--container-max`.

**Layout, and what must not be edited.** The three layers are separate elements
stacked on the wall's own tracks with `grid-template-columns: subgrid` /
`grid-template-rows: subgrid`, each spanning `1 / -1`. That is the whole idea:
each ring is addressed as a unit by `:nth-of-type` instead of every tile being
positioned by hand. Keep the layers, their order, and their 6 / 6 / 2 counts.
`--portrait-wall-offset` reflows five columns to three by shifting the
centre-column references, so the mobile layout is one number rather than a
restated grid. Browsers without `subgrid` fall back to `display: contents` on
the layers plus dense auto-placement, which resolves the same lattice.

**Behaviour (gated).** The grid carries the `reveal` hook with
`data-hub-reveal-children`, which staggers the three rings and the focal image
where the platform serves the behaviour library. Without it the attributes are
inert and the wall renders in full — nothing here is hidden by default, and
nothing should be.
