# signup-card

**What it is and when to use it.** A sign-up card that sits in an opener in
place of its join button. It asks who the visitor is, who they are looking for,
their date of birth and their email, then hands everything to the brand's own
join flow, which skips every step those answers settle. The opener keeps its
own headline, sentence and picture.

It goes in `hero-overlay`, `hero-split`, `hero-stated`, `hero-squeeze`,
`hero-portrait` or `hero-bento`, inside the element that held the join button:
words one side and card the other on a wide screen, the first step above a
laptop's fold; on a phone it follows the headline. Anything beside it goes.

With the behaviour library it asks **one question at a time** (two from
`60rem`), adds interest steps and a first name, shows live members; without it,
it is a plain form that still submits. **It sends only what the visitor gave**,
and the join flow asks for the password itself.

**What it needs.** An opener; the card's title; the brand's wording for every
answer; the age-limit and password-next lines; HubPeople's consent sentence
with the brand's terms and privacy links; the brand's interest labels, the two
interest questions and the first-name label.

**The interest labels are the join flow's own.** `data-hub-signup-intent` and
`-enjoy` take them `;`-separated, spelled as the join flow spells them (it drops
one it does not know). Empty drops the step; six can be picked on the second;
past eight the rest wait behind "show more".

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

**Options on the card** are `data-hub-signup-*` attributes, each listed with
its values and default in `settings.json` beside this file, every word too
(its English default and the `{tokens}` it may carry): the date of birth as
`boxes` or a `wheel` (a `-wide` twin from `60rem`), where the year wheel
opens, what a complete date shows (`reward`), whether "looking for" starts
ticked. Interest labels and place names stay as the join flow spells them.

**Where the visitor lives.** `data-hub-signup-places` says where the page's
visitors are, in the platform's own location names: `world`, a country (`UK`),
a region (`UK/England: Avon`) or a town (`UK/England: Avon/Bristol`). Straight
after "looking for" the card asks what that leaves open — country, region, town
(a list in a small region, a scrolling list narrowed as typed in a big one) — or
in the USA the ZIP code first, the lists a tap away (`-postal`: `first`, `lists`,
`off`). It narrows the members and hands the join flow the ZIP or the town's
coordinates. A town given in full is not asked; without the option, or if the
places cannot be reached, there is no location step.

**The members are the brand's own, fetched live**, never stored: faces from
arrival, narrowed as the visitor answers; none when there are none. Under the
progress bar a line gathers the answers so far. **Pairing.**
`member-grid` below the opener, `steps-plain` for how joining works. It refuses
`signup-steps`, the block it replaces, and `picker-chips`.

**A line after each answer**, under the answers so far, drawn at random and
never repeated in a visit: the library's (`lib/messages/`, English, true on a
brand with no members yet) and the page's own: `-say-iam`, `-say-seeking`,
`-say-location`, `-say-interest`, `-say-last` (`;`-separated; `{who}`,
`{place}`, `{interest}` fill from the answers), `-say-labels` (`Label: line |
line; Label: line`). `-say-mode="replace"`: only the page's where it has some.
`-platform` (`excite`, `affinity`) adds that platform's lines per interest. A
page in another language uses only its own; `-messages="off"` stops them.

**Brand adaptability.** `--btn-radius` shapes rows, fields and buttons;
`--chip-radius` the pills, progress bar and member strip; `--color-primary`
marks chosen answers; every ink is `--color-text` on `--color-surface`.
