# portrait-row

**What it is and when to use it.** A full-width band of the brand's own
people: one row of photographs under a heading, each with a first name and a
place under it where the person gave them. Faces as atmosphere on a
homepage, a landing page or an about page - the row the design-led dating
sites carry of real people, a first name and a town. Still by default; it
glides by itself when its Movement rung is chosen.

**It works best with eight or more faces.** Eight tall cards are more
than a laptop's row holds, so the arrows have somewhere to go and a gliding
row loops cleanly. Six is the fewest that reads as a row; twelve is plenty.
A row whose faces all fit is left still on both rungs, with no arrows and no
pause control.

**The brand's own people, shown with their OK.** Each face works best as the
person's own photograph, chosen by the brand, used once, with alt text
saying who is in it. Check that everyone has agreed to appear on a public
page anyone can reach without an account: consent to be a member is not
consent to be on the homepage. The library ships no sample face and no
drawn stand-in for one (the slot is `placeholder=no`). A generated face or a
stock photograph shown as one of the brand's people reads as a real person
to a visitor, so the band is better left out than filled that way.

**Members' profile photographs belong in `member-grid`.** They are the
platform's to show, change and withdraw, and that block shows live members.
This row is for pictures the brand chose and keeps.

**What it needs.** Six to twelve photographs at least 480px wide in
portrait, faces in the upper third (`object-position: 50% 30%`, and `50% 25%`
in a circle); a first name and a place only where the person gave them,
each line deleted where they did not; a section heading, and an eyebrow only
when something true fills it; and three short labels for the arrows and the
pause control, which a visitor hears and never sees.

**Three axes.**

| Axis | Rungs |
|---|---|
| `shape` | `portrait`, tall cards with rounded corners (the default); `round`, circles, a little smaller |
| `ground` | `plain`, `soft`, `brand`, `deep`: the ground ladder |
| `motion` | `default`, still: a row the visitor swipes or steps along with round arrows; `moving`, the row glides by itself |

**Still** is a swipe row that snaps to each face and shows no scroll bar.
The behaviour library builds two round arrows above it at the end (under it
on a phone), only while there are more faces than fit. With scripting off
the row wraps into a grid, so a mouse always has a way to every face.

**Moving** glides through the behaviour library's `marquee` with a round
pause control beside the arrows, and halts on hover, on keyboard focus,
while dragged and off screen; the arrows show once it is paused. Nothing
moves under reduced motion and no control appears. A row that is not
gliding - under reduced motion, with no behaviour library, or with every
face fitting - starts on the heading's edge, as the still rung does. Both rungs hook
`marquee carousel`; the still rung's `--hub-motion: none` keeps the marquee
from starting, so Movement is one class and no markup swap. Never a CSS
keyframe loop: only the behaviour builds the stop control a moving row
needs.

**Not on a page with `portrait-wall` or `member-strip`:** both are rows of
faces too, and a page making the same gesture twice undercuts it. A live
`member-grid` lower on the same page is defensible - curated faces near the
top, the brand's real members further down - but two gliding rows of faces
on one page are not: leave one of them still.

**Pairing.** `hero-split` above it, `steps-plain` or `cta-band` after it.
Homepage, landing and about pages; not a location page, where the same faces
on every town page are the sameness `member-grid` exists to avoid.

**Brand adaptability.** `--card-radius` rounds the tall cards and
`--font-heading` carries the heading, held to a clamp floor of 1.75rem. Each
ground names its own inks: the heading takes `--color-heading` on the page
ground and the ground's own ink elsewhere; names take the ink and places the
quieter one.
