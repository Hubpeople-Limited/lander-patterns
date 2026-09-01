# cta-band

**What it is and when to use it.** A full-bleed band carrying a centred claim,
one supporting line and one control, on a choice of four grounds. It is the
ordinary way a page ends. The alternatives are `cta-curtain`, a full-viewport
pinned panel uncovered by the section above it, and `cta-sticky`, a mobile bar;
a page wanting a plain finale takes this.

Reach for it when the page has made its case and needs to ask. Reach for
`cta-image` instead when a photograph is doing the asking, and for `cta-curtain`
only when the uncovering is genuinely the point rather than a way of ending.

Do **not** use it as a mid-page break. It paints a full-width ground, which
reads as an ending wherever it is put; a band in the middle of a page tells a
reader they have reached the bottom when they have not. That holds on every
rung — `--plain` is quieter, not less final.

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

**Brand adaptability. `ground` takes the library's four rungs**, and this is the
axis worth turning: the band closes almost every page in the library's shells,
so a brand that never varies it ends every page the same way.

| Rung | Ground | The control |
|---|---|---|
| `plain` | `--color-bg` | brand-coloured fill |
| `soft` | `--color-surface-soft` | brand-coloured fill |
| `brand` | `--color-primary` | the pair inverted |
| `deep` | `--color-scrim` | the pair inverted |

Every rung grounds on a token whose ink the contract states a ratio for, which
is what lets the supporting line sit here at body size. On `plain` and `soft`
that ink is `--color-text`; on `brand` and `deep` it is the stated partner, and
the control inverts the pair — contrast is symmetric, so the ratio holds either
way round, and on a painted band an inverted fill is the only one that reads.
The title takes the rung's ink, never `--color-heading`: that token is promised
against `--color-bg`, and three of the four rungs paint a ground of their own.

`--brand` is the default and the loudest. Take it where signing up is the point,
and something quieter where the page has already asked once.

**The focus ring is per rung, and the reason is measured.** Every other pattern
draws `outline: … var(--color-focus)`, which works because the ring lands on a
page ground — so that is what `plain` and `soft` use. On `brand` the ring would
land on `--color-primary`, and `--color-focus` is itself a brand colour: across
the five sample token sets it measures **1.00, 1.14, 1.34, 1.58 and 1.75**
against the band, against a 3:1 bar — invisible on all five. Those two rungs use
the ground's own stated partner instead, which measures **5.14, 6.28, 7.59, 7.93
and 9.26**, and the `4px` offset leaves a band-coloured gap so the guaranteed
pair sits on both sides of it. Re-derive from `preview/tokens-*.css` before
changing a ring.

`--btn-radius` shapes the control and `--container-max` holds the measure. The
supporting line is capped at `46ch` independently of that, because one centred
sentence running the full width of a wide container is hard to read however much
room there is.
