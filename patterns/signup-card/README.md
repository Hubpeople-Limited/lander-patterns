# signup-card

**What it is and when to use it.** A sign-up card that sits in an opener in
place of its join button. It asks who the visitor is, who they are looking for,
their date of birth and their email, then hands everything to the brand's own
join flow, which skips every step those answers settle. The opener keeps its
own headline, sentence and picture.

It goes in `hero-overlay`, `hero-split`, `hero-stated` or `hero-squeeze`,
inside the element that held the join button. Each of those openers makes room
for it: on a wide screen the words sit on one side and the card on the other,
with the first step and its button above the fold on a laptop; on a phone the
card follows the headline. Anything else that was beside the button — a second
link, a reassurance line — comes out: the card is the one control.

With the behaviour library the card asks **one question at a time** — two side
by side from `60rem` — adds interest steps and a first name, shows live members,
and draws a tick before handing off; without it, it is a plain form that still
submits. **It sends only what the visitor gave**: nothing is pre-ticked or
pre-filled, and the join flow asks for the password itself.

**What it needs.** An opener to sit in; the card's title; the brand's wording
for every answer; a line on the age limit; a line saying the password comes
next; the consent sentence HubPeople supplies, with the brand's terms and
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

**Options on the card**, all `data-hub-signup-*`: `seeking` — `none`, the
default, leaves "looking for" empty; `opposite` ticks it from "I am" (a woman,
men), and `same` does so for a brand whose members meet their own sex; the
visitor's own tick always wins. `dob` — `boxes`, the default, or `wheel`;
`reward` for a complete date — `sign` (age and star sign, the default), `age`
or `none`; `settle="off"` stops the card scrolling into view at a step; `guid`
where the join link carries no site GUID, without which there are no members.
Every visible word has an English default and an option of its own, named in
`lib/hub.js`'s `SIGNUP_WORDS`, so a page in another language sets them all. The
interest labels and place names are the exception: they stay as the join flow
spells them.

**Where the visitor lives.** `data-hub-signup-places` says where the page's
visitors are, in the platform's own location names: `world`, a country (`UK`),
a region (`UK/England: Avon`) or a town (`UK/England: Avon/Bristol`). Straight
after "looking for" the card asks whatever that leaves open — country, region,
then the town: a list in a small region, typed in a big one, its biggest towns
offered from the first tap — narrows the members to the answer and
sends the join flow the town's latitude and longitude, from the places files
beside the behaviour. A town given in full is not asked; without the option, or
if the places cannot be reached, there is no location step.

**The members are the brand's own, fetched live**, never stored: a strip of
faces in the card from the moment the page arrives, narrowed to who the visitor
is looking for once they say. Nothing shows when there are none or the search
fails. Under the progress bar a line gathers the answers so far. **Pairing.**
`member-grid` below the opener, `steps-plain` for how joining works. It refuses
`signup-steps`, the block it replaces, and `picker-chips`.

**Brand adaptability.** `--btn-radius` shapes the answer rows, fields and
buttons; `--chip-radius` the pills, the progress bar and the member strip.
`--color-primary` marks every chosen answer. Every ink on the card is
`--color-text` on `--color-surface`, whatever the opener's ground. The date of
birth is number boxes, not dropdowns: a list of years goes stale every January.
