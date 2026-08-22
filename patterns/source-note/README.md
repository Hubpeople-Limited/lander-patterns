# source-note

**What it is and when to use it.** One small line saying where a claim came
from, placed directly under it. Who produced the figure, what it counts, and the
date it covers.

Use it under anything the brand asserts as fact: a figure in `stat-rows` or
`stats-band`, a score in `rating-mark`, a claim in an FAQ answer, a number in a
closing line. It is a component, not a section — it belongs inside whatever
carries the claim.

**Why it exists.** `stat-rows`, `stats-band` and `rating-mark` all demand real
figures in their `needs`. `rating-mark`'s own words are *"a score the brand
cannot point at is invented proof"* — **and until now there was nowhere on the
page to point.** The rule existed and the mechanism did not.

The market leaders all do this. The ones that carry a footnote under every
claimed figure read as careful; the ones that assert a number and move on read
as marketing. That difference costs a line of 12px type.

Do **not** use it as a disclaimer, a legal line or a general footnote. It
belongs to one claim and sits under that claim. Site-wide legal text is footer
furniture.

**What it needs.** Three parts, in this order:

1. **Who produced the figure** — the research house, the analyst, the
   regulator, or the brand itself if it is genuinely internal data.
2. **What it counts** — one phrase. Registered accounts, survey respondents,
   completed matches. A number means nothing without its unit.
3. **The date it covers** — a figure with no date is a figure that was true
   once.

**A figure whose source cannot be named does not get this component. It comes
off the page.** That is the entire point: this is not a decoration that makes a
claim look better, it is the thing that makes the claim placeable at all.

Never *"source: internal"* without saying what was counted. Never *"research
shows"*. Never a bare link — a URL is not a citation, and a reader should not
have to leave the page to find out what a number means.

**Pairing.** Under `stat-rows`, `stats-band`, `rating-mark`, inside a
`faq-details` answer, or under a `quote-feature` where the quote carries a
figure. `one-per-page` is `no` — a page with four claimed figures needs four of
these, and if that looks like a lot of small print, the honest response is fewer
claims rather than fewer sources.

No `avoid-with` entry. It paints no ground, makes no ask and takes one line.

**Brand adaptability. It sets no colour, and that is deliberate.** It sits under
a claim that may be on the page ground, on a brand-coloured band or over a
scrim, and only the pattern around it knows which. Inheriting takes the ink that
pattern already established, which is by definition the one the contract
promises against that ground.

**Subordination is size and position, never a tint and never `opacity`.** A
faded ink is exactly where a contrast guarantee stops holding, and this is the
line that most has to stay readable — a source nobody can read is a source
nobody can check, which returns the claim to being an assertion. At 12px it is
already quiet enough; making it quieter would only make it decorative.

The measure is capped at `60ch` and it uses `text-wrap: pretty`, so a two-line
source does not leave one word stranded. The only tokens it touches are two
spacing steps, so it inherits the brand's rhythm and asserts nothing else.
