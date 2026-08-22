# capability-tabs

**What it is and when to use it.** A topic switcher: a rail of pill tabs above
one tinted rounded panel that pairs a claim, a ticked list of what is included,
and a half-panel image. It compresses several "what you get" stories into one
screen so a reader picks the one they came for. Use it where a brand has three
to five genuinely different stories that a reader self-selects between —
monetisation, safety, infrastructure — and where each one earns a photograph.

Do not use it for a sequence (`steps-numbered`), for questions and answers
(`faq-details`), or for one story dressed as several. Do not use it where the
reader needs all of it: everything off the open panel is one interaction away,
and most readers never take it.

**What a reader sees without the behaviour library.** Every panel, stacked,
each led by its own `<h3>` — a complete, readable section, just longer. There
are no tab buttons in the markup, so nothing in the page is dead or empty. The
`tabs` behaviour then builds the rail from each panel's `data-hub-tab-label`
and shows one panel at a time. That means the tab label is invisible until the
library loads, so it never carries content the `<h3>` does not already say.
Write the label as two or three words and the `<h3>` as the claim.

**What it needs.** A section heading, one supporting line, and three to five
real capability stories the brand can stand behind. Each story needs a short
tab label, a claim heading, one or two sentences, three to five true points,
and its own photograph with alt text. Points are `<li>` elements inside the
list slot and need no class. Do not pad a set to four; two panels is a valid
set and a fifth is the ceiling.

**Pairing.** `heading-block` above it when the section wants a proper opener
instead of the bare `h2`; delete the `h2` and its `aria-labelledby` if you do.
It sits well after a hero and before pricing, where a reader is choosing what
matters to them. One per page: two rails on one page leave a reader unsure
which one they are steering. Not on a page with `zigzag-rows`, which answers
the same "what you get" question as a run of image-and-copy rows — between them
the section appears twice with different furniture. It reads badly directly above another image-led
run — the panel image and the run's images compete — so give it a text-only
section in between.

**Brand adaptability.** `--card-radius` decides most of the character: at
`1rem` the panel reads soft and the image curves into it, at `0` it reads
editorial and the image squares off. `--chip-radius` does the same for the
rail, so a brand with `999px` chips gets true pills. `--color-surface-soft` is
the panel tint and the resting pill fill; a brand that sets it close to
`--color-bg` gets a quieter section. The tick is a rotated CSS mark on a
`--color-primary` disc with `--color-on-primary` ink, so it stays legible on
any brand and needs no icon file.

**The mobile rail.** Below `48rem` the rail bleeds to the screen edge while
keeping the page gutter as padding and as `scroll-padding-inline`, so the first
and last tab still line up with the text column. The three values are one
pattern-local property; keep them in step or the rail drifts off the column.
