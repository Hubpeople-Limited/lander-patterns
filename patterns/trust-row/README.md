# trust-row

**What it is and when to use it.** A centred strip of assurance marks bracketed
by a hairline above and below: a membership lockup beside a row of
icon-over-label compliance badges. Its job is to answer *is this outfit
legitimate* at the moment a reader is deciding whether to sign up, so it belongs
at the foot of whatever section has just asked for something — under
`pricing-tiers`, under a sign-up block, at the end of a homepage. For a dating
brand that question is not decoration: age assurance, moderation and payment
security are live objections, and until now the library had no component that
answered any of them.

Do **not** use it as a logo garden of partners, press mentions or payment-card
brands — those are a different claim and want their own pattern. Do not use it
twice on a page; `one-per-page: yes` because the marks are the page's single
answer to one question, and a second strip reads as padding rather than as more
assurance. And do not place it immediately above the site footer, which on most
brands already carries the same legal furniture. That last one is a note about
neighbours, not an `avoid-with` edge.

**What it needs.** Real, verifiable compliance marks or memberships the brand
actually holds, and nothing else. A badge a brand has not earned is a false
claim on a public page — a visitor, a regulator or a card scheme can all check
it, and the page is what they will check it against. Nothing here may be
invented to fill the row, borrowed from a competitor's footer, aspirational, or
"in progress". If the brand can evidence one mark, ship one badge; if it can
evidence none, do not use this pattern.

Concretely: the membership logo as a supplied image file (`membership-mark`)
with real alt text, the association's real name (`membership-name`) and the real
status held (`membership-status` — *Member*, *Accredited*, whatever the
association actually grants). Then one label per certification or regulation
(`badge-1-label` … `badge-3-label`), named as the scheme names itself. Delete
the `<li>` blocks you do not fill, and delete the whole membership block if
there is no membership. The membership mark is an image slot rather than drawn
markup on purpose: a real association logo is issued as an asset with its own
usage rules, and redrawing one is both a trademark problem and a guaranteed
mismatch.

**Pairing.** Reads well directly after `pricing-tiers` (price, then the reasons
to believe the price is safe to pay) and after `faq-details`, where it closes
out a page of answers with the ones that are certified rather than written.
It carries no heading of its own, so `heading-block` above it is fine when the
strip needs introducing — usually it does not, since the marks explain
themselves. No `avoid-with` entry: it fights nothing on the page, being a quiet
strip with no image, no ground and no competing call to action.

**Brand adaptability.** `--color-rule` draws the two brackets and is the only
decorative token here. Brands may set it as soft as they like and the strip
still reads: the fluid `padding-block` is what holds the marks apart from their
neighbours, and the labels carry all the meaning, so nothing is lost if the
hairlines all but disappear. `--chip-radius` shapes the status chip — pill on a
soft brand, squared on a sharp one. The icons are `--color-primary-dark` mixed
65% into `--color-text`. The bare token is contracted as a dark ink for light
grounds, and on the sample brands it runs 8.68 / 13.64 / 3.61 against the page
ground — clearing the 3:1 an icon needs, but with almost nothing to spare on a
dark brand and no promise behind it. The mix pulls it toward the one ink the
contract guarantees against every page ground and gives 11.23 / 15.30 / 6.14,
which is headroom rather than a pass. Re-derive from `preview/tokens-*.css`
before changing it. The icons are
`aria-hidden` in any case — decoration beside their labels, never standing in
for them, so a badge always keeps its words.

Text is grounded only where the contract guarantees it: labels are
`--color-text-soft` on the page ground, and the status chip is `--color-text` on
`--color-surface-soft`, the one tinted fill that ink is promised against. The
dimming on the labels is a token, never `opacity` — a faded ink is exactly where
a contrast guarantee stops holding. Nothing is set in `--color-heading`, so the
strip renders the same on a brand whose heading colour is a display tint.

Two dials worth knowing: `--trust-row-mark-height` (default `2.375rem`) sizes
the membership logo, and the strip stacks to a centred column below `35rem` and
sits as a wrapping row above it. A brand that does not want the outer spacing
overrides `margin-block` on `.trust-row` in its own CSS.
