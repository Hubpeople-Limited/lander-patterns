# heading-block

**What it is and when to use it.** The opening block of a section: a small
rule-flanked eyebrow, a tightly set display title, and one supporting line.
Use it wherever a section needs to announce itself — above a testimonial
grid, a pricing table, a feature set. Do **not** use it at the top of a page
in place of an `<h1>`: this is an `<h2>` section opener, and a page has one
`<h1>` in its hero. Do not stack two of them in one section.

**What it needs.** Three pieces of real copy: an eyebrow of two or three
words, a title, and one supporting sentence. The intro is optional — delete
the paragraph rather than padding it, and never let the eyebrow repeat the
title in different words.

**Not directly above `stats-band`.** That band carries its own eyebrow and
`<h2>`, so two section openers land in a row and one of them is doing nothing.
Anywhere else on the same page is fine, which is why this is written here
rather than as an `avoid-with` entry — that field is about the page, not about
neighbours.

**Pairing.** Sits above `testimonial-grid`, `pricing-tiers` or any card
section. Two section headers in a row means one of the sections should not
be separate.

**Brand adaptability.** `--font-heading` and the title's negative tracking
carry nearly all the character; the eyebrow's rules are drawn from
`--color-primary` at 45% so they read as an accent rather than a second
colour. The block is left-aligned on phones and centres from 48rem up —
brands that want it left-aligned throughout can drop the media query when
they append the CSS.
