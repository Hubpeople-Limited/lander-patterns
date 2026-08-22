# stat-rows

**What it is and when to use it.** A short run of full-width editorial rows,
one per statistic: the figure large on the left, a hairline across the middle,
one supporting sentence right-aligned. It is proof, not decoration — use it
where the brand has two to four numbers it genuinely publishes and can stand
behind. Do **not** use it as a filler band under a hero, do **not** stretch
three real numbers into four rows, and do **not** use it for numbers that are
really features (a list of what is included is a list, not a statistic). One
strip per page; a second one reads as padding.

**What it needs.** Each figure exactly as the brand states it — same rounding,
same unit, same currency — and one sentence per figure saying what it is. Both
come from real material with a source behind them. **A number nobody publishes
does not go on the page**: no estimates, no "roughly", no figure written to fit
the column. The section also needs a short label for its `aria-label`, naming
what the strip is ("Membership in numbers"), because the pattern ships no
visible heading of its own. Each row is a `<dt>`/`<dd>` pair inside a `<dl>`, so
the figure and its sentence stay bound together when the layout is stripped
away — a screen reader, reader mode or a print stylesheet all still read "12,400
members" *and* the sentence that explains it. The source this came from used
loose paragraphs in a `<div>`, where that pairing existed only as a visual
coincidence of the grid.

**Pairing.** `heading-block` above it supplies the section's visible heading, so
the strip stays a bare list of facts. It sits well directly under a hero, where
the rows are the first thing that substantiates the claim. Keep it away from
`stats-band` — two sets of statistics on one page devalue both, and a reader
who has met one stops reading the second.

**Brand adaptability.** `--font-heading` on the figures does most of the work:
a serif reads as an annual-report statistic, a tight grotesque as a product
metric. `--color-rule` sets both the row borders and the hairline, so the whole
strip lightens or hardens from that one token — the hairline is drawn as a
gradient that fades toward the sentence, at the ratio the source used, because
a flat line reads as a table border rather than a gesture. Both the figure and
the sentence are set at `--stat-rows-weight` (300), which is what makes the
number read as editorial; a brand whose heading face has no light weight sets
that one property to 400 rather than accepting a synthesised one. The two
sizes are tuned as a pair at roughly 1.4:1, so the sentence is copy set
against the figure and not a caption beneath it. Below 48rem the row stacks and
the hairline is not drawn at all — brands wanting figures and sentences side by
side on phones can lower the breakpoint when they append the CSS.

**Behaviour (gated).** The list carries the `reveal` hook: where the platform
serves the behaviour library, rows fade in as they scroll into view and, within
each row, the figure, the hairline and the sentence arrive in that order.
`--stat-rows-row-index` is the pattern's own property rather than a brand
token — it carries each row's position so one row's parts do not arrive in
lockstep with the row above. Duplicate a row and increment it. Without the
library every attribute is inert and the strip renders complete, which is how
it is designed to be read; the animation is never load-bearing.

**The figure and its sentence are sized as a pair, and both carry
`--type-scale`.** Scaling one half of a documented pair is how a ratio gets
broken by accident: the figure would grow with the brand's dial while the
sentence beside it stayed put, and the relationship the pattern is built on
would quietly come apart on exactly the brands that had customised most.
