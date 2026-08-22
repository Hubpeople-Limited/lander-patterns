# steps-plain

**What it is and when to use it.** A "how it works" sequence built as a hairline
lattice of text cells: a counter numeral, a short title and a line or two of
copy per step, with no photography anywhere in it. On phones it is a divided
list with the numeral in its own left gutter; from the tablet band up it becomes
one bordered box whose cells are separated by the grid gap showing the ground
through.

It exists because `steps-numbered` cannot be used without pictures. That pattern
requires a real photograph per step — portrait-crop, at least 1020px wide, with
its own alt text — which is the right bar for what it is and leaves a brand with
no photography holding nothing at all for the commonest section on a landing
page.

Choose between the two on one question: **does the brand have a real photograph
for every step?** If it does, use `steps-numbered` — the pictures do work no
lattice can. If it does not, use this, and do not go looking for stock to
qualify for the other one.

Do **not** use it for a peer set: numbering things with no order is decoration
pretending to be structure, and `benefit-tiles` is the pattern for those.

**What it needs.** Three to five real steps in the order they actually happen,
each with a short title and one or two sentences. Two is a list rather than a
sequence; beyond five nobody remembers the shape. A section heading, plus an
optional eyebrow and supporting line — both deleted rather than padded when
nothing true fills them.

**Never type a number.** The numeral is a CSS counter off the `<ol>`, so
duplicating, reordering or deleting a step renumbers the set on its own. A
hand-typed number means deleting the second of four silently leaves a page
reading 1, 3, 4, and gives assistive technology three unrelated blocks instead
of an ordered list.

The closing note is for something true and useful — what it costs, how long it
takes, what happens next. Delete it otherwise.

**Pairing.** `opener-split` or `heading-block` above it, in which case delete
this pattern's own `h2` and the `aria-labelledby` pointing at it. `cta-band`
after it, which is the natural next beat once a reader has seen how it works.

`avoid-with` names `steps-numbered` alone, and it is the same reason as the
choice above: two sequences on one page is one sequence told twice with
different furniture.

**Brand adaptability.** Everything is a pair the contract states.
`--color-text` carries the step titles on `--color-surface` and the numeral on
`--color-surface-soft`, the one tinted fill that ink is promised against;
`--color-text-soft` carries the body, the eyebrow, the intro and the note. The
section title is the one use of `--color-heading`, with both halves of that
token's contract met deliberately: the section paints no ground, so it sits on
`--color-bg`, and the `clamp()` floor is 28px, above the 24px the token is
promised at.

**The hairline is drawn per cell with `box-shadow`, not by painting the list
and letting the cells mask it.** Painting the container is the obvious way to
get one-weight hairlines out of a 1px gap, and it has a failure that only
appears with the right number of steps: `auto-fit` collapses an empty *track*
but not the empty *areas* left in a wrapped final row, so four or five steps at
a width that gives three columns would draw a cell-height slab of rule colour
where nothing sits. A per-cell shadow leaves uncovered areas on the ground.

**`--color-rule` is doing real work here and a brand may set it very soft.** At
that point the cells stop reading as separate boxes and the section becomes a
run of numbered blocks — still ordered, still readable, still complete, because
the numerals and titles carry the sequence and the rule never carries meaning on
its own. `--card-radius` shapes the box, `--chip-radius` the numeral badge.

Two dials: `--steps-plain-cell-min` (default `15rem`) sets how tall a cell
stands before its copy pushes it, and `--steps-plain-badge-size` (default
`2.75rem`) sizes the numeral and the phone gutter together, so changing one
moves both.

**The desktop grid is `auto-fit`, not a fixed column count**, so the row is as
wide as the viewport allows rather than always four across — which is the
failure a fixed count has whenever the brand turns out to have three things to
say. Four or five steps will still wrap, leaving a gap in the last row; the
per-cell hairline above is what makes that gap read as space rather than as a
mistake.
