# link-cluster

**What it is and when to use it.** A wrapping run of plain links to real pages —
places, categories, topics — with a heading above them and nothing else. No
photograph, no figure, no icon, no copy per link.

Use it to route a reader, and a search engine, from the page that has the most
attention to the pages that have the least: city and region pages, niche and
category pages, the advice hub. It answers *is there anything here for me,
where I am* without claiming a single number.

**It is the cheapest section in the library to fill honestly**, and that is the
reason it exists. Every other way of presenting a set of destinations in this
library demands a photograph: `media-card-grid` and `photo-cards` both require
one per card, and both require a sentence of copy as well. A brand with forty
city pages and no photography of forty cities either buys stock for all of them
or shows none of them. This costs nothing and cannot be faked.

Do **not** use it as a navigation menu. The site chassis carries the menu; this
is a content block that belongs where a reader has finished reading, not at the
top of the page.

**What it needs.** Real destination pages that **already exist and already have
content on them**, and the brand's own name for each.

Every link must resolve. A cluster pointing at missing or empty pages is worse
than no cluster: it tells a reader the brand is bigger than it is, and it is the
one failure here that a visitor discovers by clicking. This is the whole gate,
and it is a content-production commitment rather than a design decision — the
pattern is trivial and the forty pages behind it are not.

Ten to twenty-five links is the range. Below ten it reads as a short menu rather
than a map of the estate; above twenty-five nobody scans it.

**Two clusters on one page work well**, on different grounds, holding different
kinds of thing — cities on one, regions or categories on the other. That is the
one case where the repetition is the point: it shows the shape of the estate
rather than a list from it.

**Pairing.** After `faq-details` or before `cta-band`, where a reader is either
finished or deciding. `heading-block` or `opener-split` above it when the
cluster wants a fuller introduction than its own `h2`. No `avoid-with` entry: it
carries no image, makes no ask and states no figure, so it fights nothing.

**Brand adaptability.** Three ground modifiers — `--plain` on the page ground,
`--soft` on the tinted fill, `--brand` on the brand colour. Each names its own
ink, face and edge, and every rule reads that set rather than a token, so
nothing in the file knows which ground it is on. Same technique as
`feature-panels` and `hero-stated`.

Every pairing is one the contract states. On `--brand` the pill is
`--color-on-primary` faced with `--color-primary` ink — the stated pair
reversed, which holds because contrast is symmetric — and the heading and intro
take `--color-on-primary`. On the two light grounds the ink is `--color-text`,
promised against every page ground.

**The pill carries a drawn edge, and it is not decoration.** On `--soft` the
face is `--color-surface` against a `--color-surface-soft` ground, and on some
brands those two are within a few per cent of each other — the pills would
dissolve into the band. The hairline is what keeps a pill a pill. It is
`--color-rule`, so a brand may set it soft, and if it disappears entirely the
links are still links: underlined on hover, focusable, and carrying their own
words.

**The focus ring is each ground's own ink**, so one rule is correct on all
three. `--color-focus` would be wrong on `--brand`, where it measures 1.00, 1.14,
1.58 and 1.75 against the brand colour across the sample sets, against a 3:1 bar.

`--chip-radius` shapes the pills — pill-shaped on a soft brand, squared on a
sharp one — and the 44px minimum height is a target size rather than a
proportion, so it does not move with the radius.
