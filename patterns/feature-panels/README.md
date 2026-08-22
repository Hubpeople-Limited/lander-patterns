# feature-panels

**What it is and when to use it.** A run of full-bleed panels, edge to edge with
no gutters and no radius, each carrying a small mark and label at the top, one
large claim, and a link pinned to its floor. The panels climb a **ground
ladder** — light, then the brand colour, then dark — and that climb is the whole
point of the pattern.

Use it for two to four things the brand offers that genuinely sit in an order:
membership tiers, levels of visibility, degrees of access. The ladder says
*these are ranked* before a word is read, which is work no card grid does.

Do **not** use it for a peer set — `benefit-tiles` is that, and unranked things
on a ladder tell a reader there is a hierarchy they have missed. Nor as a price
table: `pricing-tiers` carries the figures and the aligned CTAs, this one a
claim and a route, and the two read well on one page in that order.

**What it needs.** Two to four real offerings that are genuinely ranked, each
with a short label, one claim of a few words, and a simple line mark drawn
inline. A section heading, and a supporting line only where there is something
true to say.

The claim is a few words, not a sentence. It sits at display size with a whole
panel around it, so a full sentence there wraps to four lines and the ladder
stops reading as a ladder.

**Three panels ship and their order is fixed.** Each carries one ground
modifier, running `--light`, `--brand`, `--deep`. Never reorder them and never
give two panels the same modifier. For two panels, delete the middle one. For
four, repeat `--brand` only where the brand genuinely has two middle tiers.
**There is no fourth ground and one must not be invented** — that is the rule
this pattern exists to hold.

**Pairing.** `opener-split` or `heading-block` above it where the section wants
a fuller opener than its own head block — delete the `h2` and its
`aria-labelledby` if you do. `pricing-tiers` after it, where the ladder has
established the shape and the table gives the numbers. `faq-details` after that.
No `avoid-with` entry: it paints its own grounds, carries no image and its links
go where every link goes.

**Brand adaptability — and the thing to understand before editing it.** Each
panel names a ground and an ink as two custom properties, and **every rule in
the pattern reads those two rather than naming a colour**. That is why nothing
in the file knows which panel it is on, and why adding a ground means adding one
three-line block and nothing else.

The three pairs are the three the contract states: `--color-text` on
`--color-surface-soft`, `--color-on-primary` on `--color-primary`, and
`--color-on-scrim` on `--color-scrim`. So every panel's ink is guaranteed
against its own ground on every brand, with no per-brand measurement.

**That property does the focus ring's work too.** The ring is
`--feature-panels-ink` — by definition the one colour the contract promises
against that panel's ground — so a single rule is safe on all three.
`--color-focus` would not be: on a `--color-primary` ground it measures **1.14,
1.58 and 1.75** across the three sample token sets against a 3:1 bar, which is
invisible. Re-derive from `preview/tokens-*.css` before changing it.

**The claim never takes `--color-heading`.** Every panel paints its own ground
and that token is promised against `--color-bg` alone. Only the section title
above the panels uses it, where the ground genuinely is the page's and the
`clamp()` floor is 28px.

**Why the ladder rather than three brand colours.** The obvious design is a
distinct colour per panel, and it is the one thing the token contract cannot
give: there is no second or third brand colour in it, and any colour mixed on
the spot carries no promised ink. A ladder of three tints of the one brand
colour was measured instead and separates neighbouring panels by only **1.6 to
2.2** — three near-identical rectangles. These three grounds separate
neighbours by **2.1 to 8.5** on the same brands, so the panels read as three
things while every ink stays guaranteed.

The mark's badge is the panel ink at 16% over its own ground — decorative, and
`aria-hidden`, with the label beside it carrying the meaning. The link is
underlined rather than tinted: colour is never the only thing marking a link,
and across three different grounds a tint could not be one anyway.

`--chip-radius` shapes the badge. Two dials: `--feature-panels-min` (default
`20rem`) is the narrowest a panel gets before the row wraps, and
`--feature-panels-height` sets how tall the panels stand.
