# signup-steps

**Deprecated: use `signup-card`.** The same card, set inside an opener in place
of its join button, so the page keeps a normal opener around it. Pages already
using this block keep working. It refuses `signup-card`: one sign-up card to a
page.

**What it is and when to use it.** An opener that starts the sign-up on the
page: a headline beside a card that asks who the visitor is, who they are
looking for, their date of birth and their email, then hands everything to the
brand's own join flow, which skips every step those answers settle.

With the behaviour library the card asks **one question at a time** — two side
by side from `60rem` — adds two interest steps and a first name, shows live
members of the brand as the visitor answers, and draws a tick before handing
off. Without it the card is a short plain form that still submits correctly.

Use it on a homepage or landing page whose job is sign-ups, in place of another
opener. Where the opening has to sell with a photograph first, `hero-split` or
`hero-overlay` do that better, and a page for members has no use for it.

**It sends only what the visitor gave.** Nothing is pre-ticked or pre-filled: a
default nobody changed would be sent as their answer and end up on their
profile. There is no password field; the join flow asks for it itself.

**What it needs.** A headline and one sentence; the card's title; the brand's
wording for every answer; a line on the age limit; a line saying the password
comes next; the consent sentence HubPeople supplies, with the brand's terms and
privacy links; and for the steps, the brand's interest labels, the two interest
questions and the first-name label.

**The interest labels are the join flow's own.** `data-hub-signup-intent` and
`-enjoy` take them `;`-separated, spelled exactly as the brand's join flow
spells them: a label it does not know is dropped without a word. Leave one
empty to drop that step. Six can be picked on the second. Each step shows
eight; any more wait behind a "show more" control in the same step, so a long
list never pushes the step off a phone.

**The answers are the brand's; the values are the join flow's.** `mt` is who
the visitor is: `1` a man, `2` a woman, `16` anyone else, `4` a couple on
**Excite brands only** (elsewhere it is ignored, so leave it out). `lf` is who
they are looking for, the same values summed for more than one. Drop answers a
brand does not offer and word the rest its way, but only as far as the value
honestly carries: the join flow keeps the number and later shows its own word
for it, so an answer it would contradict does not belong here. Where only one
answer is possible, as on a single-sex brand, replace the question's fieldset
with a hidden `mt` or `lf` input: nobody is asked it, the value is sent, and with
`seeking` set a fixed "I am" ticks "looking for" before the visitor arrives.
`culture` is the join flow's language — `en`, `es`, `pt`, `fr` or `de`.

**Options on the section**, all `data-hub-signup-*`: `seeking` — `none`, the
default, leaves "looking for" empty; `opposite` ticks it from "I am" (a woman,
men), and `same` does so for a brand whose members meet their own sex; the
visitor's own tick always wins. `dob` — `boxes`, the default, or `wheel`;
`reward` for a complete date — `sign` (age and star sign, the default), `age` or
`none`; `settle="off"` stops a phone scrolling the card up at each step; `guid`
where the join link carries no site GUID, without which there is no member
strip. Every visible word has an English default and an option of its own —
`next`, `back`, `skip`, `step`, `seeking-help`, `intent-help`, `enjoy-help`,
`tally`, `tally-none`, `tally-full`, `more`, the five `error-*`, `members`,
`who`, `signs`, `done`, `going` — so a brand in another language sets them all.

**The members are the brand's own, fetched live** as the visitor answers, never
stored: faces in the card on a phone, a row under the headline when wide.
Nothing shows when there are none or the search fails.

**Pairing.** `member-grid` below it, `steps-plain` for how joining works, and
`cta-band` to close. It refuses `picker-chips` — two opening questions is no
opening question — and every other opener (`article-masthead`, `hero-bento`,
`hero-centred`, `hero-collage`, `hero-overlay`, `hero-portrait`, `hero-split`,
`hero-squeeze`, `hero-stated`).

**Brand adaptability.** `--btn-radius` shapes the answer rows, fields and
buttons together; `--chip-radius` the interest pills, the progress bar and the
member strip. `--color-primary` marks every chosen answer and the progress.
Every ink on the card is `--color-text`: `--color-heading` is promised against
the page ground only, so the headline beside the card is its one use.

The date of birth is three number boxes, not dropdowns: a list of years goes
out of date every January, and a phone brings up the number keypad.
