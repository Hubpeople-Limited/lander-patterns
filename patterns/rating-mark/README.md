# rating-mark

**What it is and when to use it.** A published rating shown as whole stars
beside the figure itself: five stars, the score, and the number of ratings
behind it.

It is a component rather than a section, and it is meant to go *inside* other
things — a hero's copy column, a testimonial's attribution, beside a
`member-strip`, under a closing control. Every live template this library was
measured against shows a rating somewhere, and until now there was nothing to
show one with.

Do **not** use it as a section of its own. A rating floating on its own band is
a number with nothing to be a rating *of*.

**What it needs.** A rating the platform actually publishes, **and the count
behind it**. Both, always.

A score with no count is not evidence — 5.0 from two people and 4.6 from a
hundred and forty thousand are different claims and the star row cannot tell
them apart. And a score the brand cannot point at is invented proof on the most
checkable kind of statement a page can make.

**The stars are decoration and the text is the claim.** The star row is
`aria-hidden`, so the value and the count are the only things read out. Never
ship the stars without them: a rating a screen reader cannot read is not a
rating, and a page that shows four gold shapes and no number has said nothing it
could be held to.

**There is deliberately no half star.** Round to the nearest whole star and let
the figure carry the precision. A half star is a rendering problem — a clipped
overlay, a fill percentage, an id that collides when the component appears
twice — solving for a level of detail the text beside it already states exactly.
Whole stars have none of that and lose nothing.

**Pairing.** Inside `quote-feature`'s attribution, inside `testimonial-grid`,
beside `member-strip`, in a hero's copy column. `one-per-page` is `no`: a page
may legitimately show an aggregate at the top and an individual rating beside a
member.

No `avoid-with` entry. It paints no ground, makes no ask and takes almost no
room.

**Brand adaptability. It sets no colour for the stars or the value**, so both
take the ink of whatever they sit in — which is the only ink promised against
that ground, and lets the same component work in a hero over a scrim, on a
card, and on a brand-coloured band without changing a line.

**The count inherits with everything else.** `--color-text-soft` states its
ratio against a page ground, and this pattern's whole purpose is sitting on
scrims and brand bands, where it measures between 1.12:1 and 3.04:1. A stated
ratio is only worth having against the ground it was stated for.

Dimming with `opacity` is where a contrast guarantee stops holding, so the
count is not dimmed at all — it is subordinated by size and position, the same
way `source-note` is.

The stars are inline SVG with `fill="currentColor"`, so they inherit rather than
being fetched, cannot go missing in a brand font the way a `★` character can,
and carry no ids to collide when the component appears more than once on a page.
