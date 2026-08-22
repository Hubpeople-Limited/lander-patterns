# faq-details

**What it is and when to use it.** An FAQ accordion built on native
`<details>`/`<summary>` — hairline rows, and a plus that rotates into a cross
when a row opens. **No JavaScript at all**: the browser gives keyboard
operation, the expanded/collapsed announcement, and find-in-page that opens
the matching row. Use it where a page genuinely has to answer repeated
questions — end of a landing page, below pricing. Do **not** use it to hide
material the visitor needs to make the decision the page is asking for: an
accordion is for the long tail, not for the case. Do not use it for two
questions (write them out), for navigation, or for a step-by-step sequence.

**What it needs.** A section heading, and the real questions people ask with
true answers in the brand's own words. Every row is one `<details>` — duplicate
the block in `pattern.html` per question. An answer may be several paragraphs;
put them inside the answer slot as `<p>` elements.

**Pairing.** `heading-block` above it when the section needs a proper opener
instead of the bare `h2`. Nothing fights with it — it is quiet and constrained
to a reading measure, so it sits anywhere the questions are worth answering,
which is usually late, after a visitor has read enough to have them.

**Brand adaptability.** `--color-rule` sets the whole character: a faint rule
reads editorial, a strong one reads utilitarian. `--font-heading` on the
questions is what makes the set look like part of the brand rather than a
generic accordion. The icon is drawn from `--color-text-soft` at 2px, so it
stays legible on any ground; it is a shape, never a colour cue.

**Two judgement calls.** *Every row ships closed.* An open first row shifts
everything below it, makes the set read unevenly, and implies question one
matters most when it usually just happens to be first. The plus icon already
signals the rows open. If a brand has one question that genuinely dominates,
add `open` to that row and say why in the page notes. *Rows are independent
— no `name` attribute.* Grouping `<details>` by `name` closes the previous row
automatically, which moves content the visitor did not touch. That is the
thing this pattern is careful not to do.
