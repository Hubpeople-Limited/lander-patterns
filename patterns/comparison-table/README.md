# comparison-table

**What it is and when to use it.** A real `<table>` comparing two or three things
against the same criteria. Tier names across the top, one criterion per row, and
one column optionally named as the recommended one — in words, above the tint.

Use it when the reader's question is *what is the difference between these*, and
the answer is a grid. That is a narrow case and it is worth being strict about
it: a comparison is only a table when every row genuinely applies to every
column. Three things that differ in kind rather than in degree are not a
comparison, and a table of them invents a symmetry the brand does not have.

Do **not** use it where the tiers differ only in price and term. A matrix whose
every row reads the same across all three columns tells a reader nothing and
takes a screen to do it — that is a sentence, not a table. Do not use it as a
feature list for one thing; that is `benefit-tiles` or `steps-plain`. And do not
rebuild it out of `div`s: a comparison laid out as boxes has lost the row and
column relationships that make it readable by anything other than an eye.

**What it needs.** Two or three real things the brand offers, the criteria they
are genuinely measured against, and what each one actually gives against each
criterion — in the brand's own words. A recommended column only where the brand
recommends one; the flag is deleted otherwise, and the tint with it.

Ticks are the trap. A tick is a claim that the whole criterion is met, and it is
the cheapest cell to write and the easiest to copy from a competitor. Where the
answer is a number, a limit or a condition, write it.

**Pairing.** On a pricing page it sits below `pricing-tiers`, which carries the
prices and the controls, and it must not repeat them: two prices on one page
that disagree is the failure worth designing against. On a features page it is
the whole tier section and there are no prices and no controls anywhere near it
— that page describes what tiers unlock and hands the reader on. `heading-block`
or `opener-split` above it where the section wants a fuller introduction than its
own `h2`. `faq-details` reads well after it, for the questions a grid raises.

**Brand adaptability.** `--card-radius` rounds the scroll container, so the table
reads soft or sharp with the rest of the brand. `--color-rule` draws every row
line and the head's bottom edge; a brand may set it as soft as it likes, and the
table survives it disappearing entirely because the columns still align and the
head still sticks. `--type-scale` moves the section title and the tier names
together.

The recommended column is a 7% mix of the brand colour into the surface, so it
tints on any brand without a second token. **It is never the only thing saying
which column is recommended** — the flag above it carries the brand's own word,
and that is what reaches a screen reader, a monochrome print and anyone who does
not see the tint. Delete both together or neither.

**Every contract token here carries a fallback to another contract token**, so
the table renders on a brand that has not adopted the role names: the heading
ink falls back to `--color-text`, the rule to `--color-surface-soft`, the head's
ground to `--color-bg`, the focus ring to `--color-primary`. Nothing falls back
to a literal colour, and nothing falls back to something that would land ink on
a ground it does not clear.

**The scroll container is focusable on purpose.** Firefox and Safari do not let a
keyboard user scroll a container that cannot take focus, so without `tabindex`
the right-hand columns are unreachable without a mouse. The `role` and the label
are what stop that focus stop being a mystery to a screen-reader user, and the
ring is drawn on the container rather than suppressed.

The head sticks only because the container has a real height. `overflow: auto`
on both axes with a `max-block-size` is deliberate: setting only `overflow-x`
makes the vertical axis scrollable too, and the head then sticks to something
that never scrolls.
