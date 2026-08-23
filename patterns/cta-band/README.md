# cta-band

**What it is and when to use it.** A full-bleed band on the brand colour
carrying a centred claim, one supporting line and one control. It is the
ordinary way a page ends, and until now the library had no answer for it: the
only closing patterns were `cta-curtain`, a full-viewport pinned panel uncovered
by the section above it, and `cta-sticky`, a mobile bar. Every page wanting a
plain finale had to take the curtain, which is an elaborate thing to place and
`one-per-page` besides.

Reach for it when the page has made its case and needs to ask. Reach for
`cta-image` instead when a photograph is doing the asking, and for `cta-curtain`
only when the uncovering is genuinely the point rather than a way of ending.

Do **not** use it as a mid-page break. It paints the brand colour across the
full width, which reads as an ending wherever it is put; a band in the middle of
a page tells a reader they have reached the bottom when they have not.

**What it needs.** A closing headline and one supporting line, both saying
something the page has earned the right to say. That is a lower bar than most
patterns here and it is still a bar: a band repeating the hero's words has added
a screen of brand colour and no argument. The supporting line is the place to
answer the last objection — what it costs, what happens next, what the reader is
not committing to — and it should be deleted rather than padded if there is
nothing true to put there. The eyebrow is optional and usually unnecessary.

The control is `{{join.url}}` with `{{join.text}}` and there is exactly one. A
second control on a closing band splits the decision it exists to make.

**Pairing.** Sits well after `pricing-tiers`, after `faq-details`, and after
`safety-protections` — in each case the reader has just been given the facts and
this is the ask. `avoid-with` names `cta-curtain` and `cta-image` because all
three close a page, and a page that closes three times has not decided how it
ends.

It deliberately does **not** avoid `cta-sticky`. A mobile bar and a closing band
are not the same job: the bar is for the visitor who never reaches the bottom,
the band for the one who does. `cta-curtain` refuses the bar because the bar
sits over the panel through the whole reveal, which is a mechanical conflict
this pattern does not have.

**Brand adaptability.** The section grounds on `--color-primary` and every ink
is `--color-on-primary`, one of the three pairs carrying a stated ratio — that
is what lets the supporting line sit here at body size, where a band grounded on
any other token could not promise it. The title takes `--color-on-primary` too,
not `--color-heading`: that token is promised against `--color-bg`, and this
section paints its own ground.

The button inverts the pair — `--color-on-primary` fill, `--color-primary` ink.
Contrast is symmetric, so the stated ratio holds either way round, and on a band
of the brand colour it is the only fill that reads.

**The focus ring is the one place this pattern departs from the library's habit,
and the reason is measured.** Every other pattern draws
`outline: … var(--color-focus)`, which works because the ring lands on a page
ground. Here it would land on `--color-primary`, and `--color-focus` is itself a
brand colour: across the four sample token sets that ring measures **1.00, 1.14,
1.58 and 1.75** against the band, against a 3:1 bar — invisible on all four.
The ring is therefore `--color-on-primary`, which measures **5.14, 6.28, 7.59
and 9.26**
on the same brands, and the `4px` offset leaves a band-coloured gap so the
guaranteed pair sits on both sides of it. Re-derive from `preview/tokens-*.css`
before changing either value.

`--btn-radius` shapes the control and `--container-max` holds the measure. The
supporting line is capped at `46ch` independently of that, because one centred
sentence running the full width of a wide container is hard to read however much
room there is.
