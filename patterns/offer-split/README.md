# offer-split

**What it is and when to use it.** A mid-page conversion beat with no
photography in it: the argument set as two or three short paragraphs on one
side, and the offer as a filled panel carrying its own heading, one line and the
join control on the other. Below the wide band it stacks, argument first, panel
second.

The library had no mid-page ask. `hero-split` is the opener and `one-per-page`;
`cta-band` and `cta-image` are finales that read as endings wherever they are
put; `pricing-tiers` is a reference table. A page that needs to make one offer
halfway down — after the how-it-works, before the questions — had nothing, and a
designer had nothing to reach for.

It is also, with `benefit-tiles` and `steps-plain`, one of the three sections a
brand with no usable photography can actually build a page out of.

Do **not** use it as a section opener. The panel makes a specific offer and
takes the eye immediately; put it at the top of a page and the argument beside
it never gets read. It belongs where a reader has been given enough to be
deciding.

**What it needs.** Two or three short paragraphs making **one** argument, and a
panel heading with one line saying plainly what is on offer. Everything here is
words — there is no photograph to carry a weak paragraph — so they have to be
the brand's real ones.

Keep the prose to three paragraphs at the outside. The panel is what a scanning
reader stops at, so anything past the third is not being read; if the argument
genuinely needs more room, it is a section of its own and this is the beat after
it.

The panel line is the place to be concrete — what it costs, what happens next,
what the reader is not committing to. A panel repeating the heading in different
words has taken the most conspicuous block on the page and put nothing in it.

**Pairing.** After `steps-plain` or `benefit-tiles`, where a reader has just
seen how the thing works. `opener-split` or `heading-block` above it if the
section wants a fuller opener than its own `h2` — delete the `h2` and its
`aria-labelledby` if you do. `faq-details` after it.

No `avoid-with` entry. It carries no image, paints its ground only inside the
panel, and its control is one of several a page may legitimately hold — unlike
the three closing patterns, which all claim the same slot.

**Brand adaptability.** The prose side is `--color-heading` for the title —
page ground, `clamp()` floor at 28px, so both halves of that token's contract
hold — and `--color-text-soft` for the paragraphs.

The panel grounds on `--color-primary` with every ink `--color-on-primary`,
which is one of the three pairs carrying a stated ratio. That is what lets the
panel's supporting line sit at body size: on any other ground a 16px line
against a brand colour has nothing promising it. The panel heading takes
`--color-on-primary` too, never `--color-heading`, because the panel paints its
own ground.

The control inverts the pair — `--color-on-primary` fill, `--color-primary`
ink. Contrast is symmetric, so the stated ratio holds either way round.

**The focus ring is `--color-on-primary`, not `--color-focus`, and the reason is
measured.** The control sits inside a panel of the brand colour, and
`--color-focus` is itself a brand colour: across the five sample token sets
that ring measures **1.00, 1.14, 1.34, 1.58 and 1.75** against a
`--color-primary` ground, against a 3:1 bar. `--color-on-primary` measures
**5.14, 6.28, 7.59, 7.93 and 9.26** on the
same brands, and the `4px` offset leaves a panel-coloured gap so the guaranteed
pair sits either side of the ring. `cta-band` does the same thing for the same
reason. Re-derive from `preview/tokens-*.css` before changing either value.

`--card-radius` shapes the panel and `--btn-radius` the control. One dial:
`--offer-split-panel-min` (default `18rem`) is the panel's floor height, which
stops a short offer collapsing to a strip beside three paragraphs.

**The columns are `1.15fr` to `1fr`, not equal.** The prose needs the wider half
to hold a readable measure, and a panel given exactly half a wide container ends
up with one word per line in its heading. The split only applies from `64rem`;
below that the stacked order is argument first, which is the right reading order
as well as the right visual one.
