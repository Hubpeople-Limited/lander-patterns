# picker-chips

**What it is and when to use it.** A small card holding a question, one helper
line, and a row of pill links that each go straight into the join flow. It
moves the first sign-up decision above the fold and makes it one tap instead
of a form. That is the whole of its value: it is a **conversion device, not a
filter** — nothing on the page changes when a pill is tapped, the visitor
simply arrives at sign-up already committed to an answer. Use it inside or
directly beneath the hero, where it is the page's first action. Do **not** use
it further down a page (the commitment is worth nothing once the visitor has
already scrolled past the decision), do not use it to filter or sort anything
on the page, and do not use it where the honest option count is one — a single
pill is a button, and `hero-split` already has one.

Two structural fixes over the hand-built version this came from: the pills are
a real `<ul role="list">` inside a `role="group"` named by its heading, so the
group has an accessible name and a count instead of the source's inner bare
`<div aria-label>`, which no assistive technology reads; and the arrow is a
separate `aria-hidden` span, so each link is announced as "Women", not "Women
right arrow". No landmark, deliberately: a `<nav>` would be wrong — these are
calls to action, all to one destination, not site navigation — and a `<section>`
with an accessible name is a `region` landmark, which would put a small card
inside a hero into the same list as the header's real nav for the same cost.
`role="group"` gives the name without the landmark, which is what the source
did on its outer card and got right. (Named `picker-chips` because `chip` is a
chassis-reserved class family.)

**What it needs.** The real opening question in the brand's own words, and two
to four real options behind it — past four this becomes the form it exists to
replace. One helper line saying what picking does.

**Let each pill carry the answer it gives.** The join flow reads two answers
from the link and skips the step each one settles: `lf`, who the visitor is
looking for, and `mt`, who they are. The values are `1` a man, `2` a woman,
`4` a couple and `16` other, and `lf` adds them for more than one (`3` is men
and women). Append the one the question asks — for *Who are you looking for?*,
the *Women* pill is `{{join.url}}?lf=2` — and nothing else. **`4` exists on
Excite brands only**: an Affinity brand ignores it without a word, so a
*Couples* pill there is a control that does nothing. An option with no value
keeps the bare token, which always works. The parameters are HubPeople's
Registration URL API; never invent another, and never swap the token for a
written-out URL — a wrong URL is a dead sign-up.

**Not on a page with `signup-card` or `signup-steps`.** Those ask the opening questions itself; two first questions is none.

**Pairing.** Built for `hero-split`: drop it into the hero's copy column, and
delete `hero-split`'s own join CTA so there is one action in the viewport
rather than two competing ones. Do not put a second picker on the same page:
two opening questions is no opening question.

**Brand adaptability.** `--chip-radius` does the most work: pill-round reads
consumer and warm, squared reads utilitarian. `--card-radius`,
`--card-border` and `--card-shadow` decide whether the card floats above the
hero or sits flat in it. Pills are outlined in a `color-mix()` tint of
`--color-primary` and fill to solid `--color-primary` on hover, so the card is
quiet until touched. The 48px minimum height and the gap between pills are the
pattern's own `--picker-chips-target` and the spacing scale — a brand may
raise the target, and should not lower it.
