# anchored-split

**What it is and when to use it.** Two columns of unequal weight. A short panel
stays put on the left while the evidence for it scrolls past on the right, so
the claim is still in view when the reader reaches the fourth thing that
supports it.

Use it where the reader needs the claim held while they read the case — safety
commitments and what actually happens behind each one, a promise and the
mechanics of it, a position and the reasons for it. It is the section for
material that is genuinely one argument rather than a set of peers, which is
what separates it from an index or a card run.

Do **not** use it for peers. If the items on the right would read the same in
any order and the panel on the left is only a heading, this is a heading and a
list, and `heading-block` plus `listing-rows` says so with less machinery. Do
not use it below three items: a sticky panel beside two paragraphs never moves,
so the whole device is invisible and the reader is left with a narrow column for
no reason. And do not put a second one on the same page — two panels competing
to stay put is the layout arguing with itself.

**What it needs.** One claim, as a title and at most two sentences. Then three or
more real items, each with its own subheading and a paragraph from real
material.

**The length of the anchor is the gate, and it is the one failure this cannot
recover from.** A panel taller than the viewport sticks at the top and its own
foot can never be scrolled to — the reader simply never sees the end of it, on
any screen shorter than the panel. There is no CSS test for "does this fit", so
the constraint lives in `needs` instead: a title and two sentences fits a phone
in landscape, which is the shortest viewport that reaches the two-column layout
at all.

**Pairing.** `heading-block` above it only where the section needs an
introduction its own anchor does not already give — usually it does not, since
the anchor *is* the introduction. `cta-band` or `cta-assurance` after it, where
the case has been made. On a safety page it reads well before
`safety-protections`: the argument first, then the categorised detail.

**Brand adaptability.** Two ground modifiers — `--plain` on the page ground and
`--soft` on the tinted fill — from the library's ground ladder.

**There is deliberately no `--brand` or `--deep` rung.** Both sides share one
ground, and they have to: a sticky panel on a different ground from the column
beside it draws a vertical seam that moves as the page scrolls, which is the one
thing a reader's eye follows instead of the words. On the two dark rungs the
seam would be the most prominent thing in the section.

`--color-rule` draws the hairline between entries; a brand may set it as soft as
it likes and the entries are still separated by their own padding.
`--type-scale` moves the claim and the entry headings together.

`--container-max` matters more here than in most patterns, because the split is
`4fr 6fr` of whatever it is given. On a brand with a wide container the evidence
column gets a long measure, which is why the paragraph is held to `62ch`
independently.

**The asymmetry is the design.** 40/60, never 50/50, which reads as indecision
rather than as a choice — and the narrow side is the one that stays, so the page
does not feel like it is holding half of itself still.

**`align-self: start` is load-bearing.** Without it the grid stretches the panel
to the full row height, so it is already as tall as the content beside it and
sticky has nothing to do. This is the mistake that makes a sticky column look
like it simply does not work.

Below `60rem` the two stack and nothing sticks. That is the correct behaviour
rather than a fallback: on a phone there is no second column for the anchor to
stay beside, and a panel pinned over a single column of text covers the text.
