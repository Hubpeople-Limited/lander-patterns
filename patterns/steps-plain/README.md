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
page. Two designers independently built a text-only version, and this is it.

Choose between the two on one question: **does the brand have a real photograph
for every step?** If it does, use `steps-numbered` — the pictures do work no
lattice can. If it does not, use this, and do not go looking for stock to
qualify for the other one.

Do **not** use it for a peer set. Numbering things that have no order is
decoration pretending to be structure; `benefit-tiles` is the pattern for
capabilities that happen in no particular sequence.

**What it needs.** Three to five real steps in the order they actually happen,
each with a short title and one or two sentences. Two steps is a list rather
than a sequence; beyond five nobody remembers the shape. A section heading, and
optionally an eyebrow and a supporting line — both deleted rather than padded
when nothing true fills them.

**Never type a number.** The numeral is a CSS counter off the `<ol>`, so
duplicating, reordering or deleting a step renumbers the set on its own. One of
the designer pages this came from used a hand-typed number in each card, which
means deleting the second of four silently leaves a page reading 1, 3, 4 — and
gives assistive technology three unrelated blocks instead of an ordered list.

The closing note is for something true and useful — what it costs, how long it
takes, what happens next. Delete it otherwise; it is not a place for
reassurance.

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

**The lattice is drawn by the grid gap, not by cell borders**, and that is worth
knowing before anyone changes it. Cell borders double up wherever two cells
meet, so a four-up run shows a hairline of one weight down the outside and two
weights between — which is exactly the kind of thing nobody notices until a
brand sets `--color-rule` dark. A 1px gap over a ruled background gives one
weight everywhere and survives cells being reordered.

`--color-rule` is decorative here, as everywhere: a brand may set it as soft as
it likes and the numerals and titles still carry the structure. `--card-radius`
shapes the box, `--chip-radius` the numeral badge.

Two dials: `--steps-plain-cell-min` (default `15rem`) sets how tall a cell
stands before its copy pushes it, and `--steps-plain-badge-size` (default
`2.75rem`) sizes the numeral and the phone gutter together, so changing one
moves both.

**The desktop grid is `auto-fit`, not a fixed column count.** Three steps and
five both fill their row rather than leaving a hole at one width and orphaning a
cell at another — which is the failure a fixed four-up has whenever the brand
turns out to have three things to say.
