# stats-band

**What it is and when to use it.** A full-bleed inverted band carrying a
lattice of figures — three across on desktop, two on tablet, one on a phone.
It is the proof block: the place a page states what the brand can actually
count. Use it once, below the hero or above pricing. Do **not** use it twice
on one page, do **not** use it as a feature list with numbers bolted on, and
do **not** reach for it when the brand has fewer than three countable facts —
two lonely figures in a six-cell frame read as a gap where the evidence
should be.

**What it needs.** An eyebrow, a short band title, and the figures
themselves: for each one a `stat-figure` and a `stat-label`. **Every figure
is real brand data, taken from brand material, and is never invented,
rounded up for rhythm, or padded out to fill the row.** The figure is
written into the markup as text — `20+`, `24/7`, `50–65%`, `17` — because it
is a factual claim about the brand, so it must be right in the HTML with no
script, no data attribute and no animation involved. (The band this was
extracted from shipped `data-count="20"` with the literal text `0+`; a
visitor with JavaScript off was told the brand had zero years of trading.
That is the bug this pattern exists to not repeat.) Duplicate the
`stats-band-item` block once per figure and delete the sample one. Three or
six figures fill the rows flush; four or five leave a hole at the end.

**Pairing.** Sits well above `pricing-tiers` (proof, then price) and below
`hero-split` — proof belongs in the middle of a long page, after the claim and
before the price. Not on a page with `stat-rows`, which is the same claim in
a different shape — two sets of figures devalue both. Do not put
`heading-block` directly above it either: this band
carries its own eyebrow and `<h2>`, so two section openers land in a row and
one of them is doing nothing. That is a note about neighbours rather than an
`avoid-with` entry — `heading-block` elsewhere on the same page is right and
six patterns ask for it.

**Brand adaptability.** The band grounds on `--color-primary` and writes on
it with `--color-on-primary`. That pair, not a hand-picked navy, because the
contract guarantees only one inverted relationship: `--color-on-primary` is
≥ 4.5:1 against `--color-primary`. There is no dark-surface token, and
mixing one — darkening `--color-primary` toward `--color-heading`, say —
voids the guarantee the moment the mix moves. So the pattern inherits the
one pair that is safe on every brand and stays inside it: the labels are
full-strength `--color-on-primary`, separated from the figures by size and
weight rather than by opacity, because a faded label is exactly where the
contrast guarantee stops holding. Only the hairlines are translucent
(`--color-on-primary` at 24%), and they are decorative — the `<dl>` carries
the figure/label pairing structurally, so the lattice can be quiet.

**What a brand must check.** Whether its primary is *deep* enough to want
this treatment. A brand whose `--color-primary` is a bright yellow or a pale
mint gets a saturated light band with dark text — legible, still correct,
but it is no longer a dark band and it will shout next to the rest of the
page. Look at it before shipping. A brand that wants a deeper ground
overrides `background` on `.stats-band` in its own CSS **and re-tests
`--color-on-primary` against the new value at 4.5:1 itself** — that
override leaves the contract behind. `--card-radius` sets the frame's
corners; on a sharp brand (`--card-radius: 0`) the lattice reads as a
drawn table, on a rounded one `overflow: clip` tucks it inside the curve.

**Behaviour (gated).** The grid carries the `reveal` hook, so on platforms
serving the behaviour library the cells fade and rise in as the band scrolls
into view, staggered, and reduced-motion visitors get nothing. Without the
library the attributes are inert and the band renders fully visible and
complete — which is the only state the figures are allowed to depend on.
The count-up is the library's `counter` behaviour on the same hook: the authored
figure is the final figure, byte for byte, and under reduced motion the only one.
