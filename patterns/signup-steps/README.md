# signup-steps

**What it is and when to use it.** An opener that starts the sign-up on the
page: a headline beside a short card asking who the visitor is, who they are
looking for, their date of birth and their email. Submitting sends those
answers to the brand's own join flow, which skips every step they settle, so
the visitor arrives already part-way through with nothing to type twice.

Use it on a homepage or a landing page whose job is sign-ups, in place of
another opener. It is an opener, not a component: the headline is its own, so
it refuses every other hero. Do **not** use it where the opening has to sell
with a photograph first — `hero-split` or `hero-overlay` with a join control
does that better — and do not use it on a page whose visitors are mostly
already members.

**The form sends only what the visitor gave.** Nothing is pre-ticked or
pre-filled: a default nobody changed would be sent as their answer and end up
on their profile. There is no password field: the join flow asks for it on its
own screen, which is what the password note says.

**What it needs.** A headline and one sentence in the brand's own words; the
card's title; the brand's wording for every answer; one line on the age limit;
one line saying the password comes next; and the consent sentence HubPeople
supplies, with the brand's own terms and privacy links. The consent box is
never ticked in advance and carries no `name`: it is the visitor's agreement,
not an answer.

**The answers are the join flow's own values** — keep every `name` and `value`
exactly as they are. `mt` is who the visitor is: `1` a man, `2` a woman, `16`
something else, and `4` a couple on **Excite brands only**; anywhere else a
couple answer is ignored without a word, so it is left out. `lf` is who they
are looking for, with the same values and the sum for more than one (`3` is
men and women). Without script each question takes one answer. `culture` is
the join flow's language — `en`, `es`, `pt`, `fr` or `de` — and must match
the page's.

The date of birth is three number boxes, not dropdowns: a list of years goes
out of date every January, and a phone brings up the number keypad for them.

**Pairing.** `member-grid` below it, so the members the card promises are on
the page. `steps-plain` for how joining works, and `cta-band` to close, whose
control goes to the same join flow. It refuses `picker-chips` — two opening
questions is no opening question — and every other opener
(`article-masthead`, `hero-centred`, `hero-overlay`, `hero-split`,
`hero-squeeze`, `hero-stated`).

**Brand adaptability.** `--btn-radius` shapes the answer rows, the fields and
the button together, so the card reads as one set of controls. `--card-radius`,
`--card-border` and `--card-shadow` decide whether it floats or sits flat.
`--color-primary` marks the chosen answer, its tick and the button.

Every ink is `--color-text` on the card: `--color-heading` is promised against
the page ground only, so the card's title and questions do not use it; the
headline beside the card does.

On a phone the card follows the headline and the supporting sentence is left
out — the card is the message there. From `60rem` the headline, its sentence
and the card sit side by side.
