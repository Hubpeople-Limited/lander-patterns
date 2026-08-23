# listing-rows

**What it is and when to use it.** An index: full-width rows separated by
hairlines, each carrying a linked title, one real sentence, and up to two true
attributes that align down their own columns across the whole list. Five items
upward.

Use it for a set of things a reader scans rather than reads — guides, articles,
city or category pages, a run of features, a directory. It carries more per item
than a card ever fits and it needs no photograph, so a brand with forty
destinations and pictures of none of them can still show all forty.

**This is the section the library was missing.** For a set of five or more peers
the alternatives here all want pictures: `photo-cards` and `media-card-grid`
require one per card, `zigzag-rows` a picture and a paragraph per row. A brand
with words and no imagery had a card grid or nothing, and a card grid of forty
text-only boxes is the sameness this library exists to avoid.

Do **not** use it below five items. Three or four rows read as a stub of a list
rather than a list, and at that size the honest answers are a short run of cards
or a sentence naming them. Do not use it where the items are not peers — an
index states that everything on it is the same kind of thing. And do not use it
as a menu: the site chassis carries navigation, and this belongs where a reader
has finished reading.

**What it needs.** Five or more real entries of one kind, each with the brand's
own title, one true sentence, and at least one genuine attribute. Every link
resolves to a page that already has content on it.

The attributes are the gate. Two columns ship, and a column the material cannot
fill honestly is deleted from every row rather than filled — a date invented to
square off a column is a fabricated publication date, and a column of blanks
says the brand does not know its own catalogue. One attribute is a perfectly
good index; none is a list, and a list is fine too.

**Pairing.** `heading-block` or `opener-split` above it where the section wants
a fuller introduction than its own `h2`. It reads well before `cta-band`, where
a reader has finished scanning. `link-cluster` does a different job and the two
sit together well: this one carries a sentence per destination, that one carries
none, so a page can index its best twelve here and route to the other forty
there.

**Brand adaptability.** Three ground modifiers — `--plain` on the page ground,
`--soft` on the tinted fill, `--brand` on the brand colour. The names are
`link-cluster`'s on purpose: a reader of this library should meet one ground
vocabulary rather than one per pattern. Each names its own ink set and every
rule reads that set, so nothing in the file knows which ground it is on.

On `--brand` the hairline is the ground's own ink held back to 35%, not
`--color-rule`. The contract calls that token decorative and promises it against
nothing in particular, so a brand may set it as soft as it likes — which is fine
on a page ground and invisible on a brand one.

`--type-scale` moves the section title and the row titles together, and the
attributes deliberately do not move with them: they are the quiet edge of the
row and a brand turning its display type up is not asking for larger dates.

**The rules are the device.** No shadow, no radius, no card. A row that becomes
a box has become a card, and the alignment is what makes the set look
maintained by people rather than generated — which is the whole argument for
choosing this over a grid.

**`subgrid` is what buys that alignment**, and it applies only above 48rem.
Below it the row is one column and the attributes fall to their own lines in
source order, which reads correctly and needs no alignment to do it. The column
count lives in one rule; change it there and in the markup together.

The title is the only focusable thing in a row, and it is first in the source.
The summary and the attributes are moved by grid placement rather than by
`order`, and they carry nothing focusable, so what a keyboard user tabs through
is what they see.
