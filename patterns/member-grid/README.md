# member-grid

**What it is and when to use it.** A block of your brand's own members, filled
in by the platform when the page is built. The page ships an **empty section**;
the CMS queries the member database, writes real profiles into it, and the
result is in the HTML a crawler receives — no JavaScript, nothing fetched in the
visitor's browser.

That makes it the one people-pattern on a location page that is worth having.
A page per town carrying the same words with the place name swapped is the
thing Google's spam policy names as doorway abuse; a page carrying real members
who are only on *that* page is unique first-party data no competitor holds.

Use it where the members are the argument: a location page, a community page,
or a homepage that opens on who is already here. Do **not** use it as
decoration on a page that has nothing to do with who the members are, and do
not put two on one page unless they are showing genuinely different sets —
`member-filter` is the pattern for that.

**Set `data-members-min` and mean it.** Below that many members the platform
renders the empty state instead of a thin grid. A location page with four faces
on it is the doorway page this pattern exists to avoid, so let it refuse.

**What it needs.** Nothing from the partner, which is what separates this from
every other people-pattern here — no photographs to source, no consent to
gather, no names to check. The platform supplies the members and owns whether
they may be shown.

What it does need is four decisions:

- **The location**, spelled exactly as the platform spells it. A wrong value is
  **ignored, not refused**: the block fills with people from somewhere else and
  looks completely normal. Check it against the platform's location reference
  before shipping, never after.
- **`data-members-strict="true"`, lowercase, always.** It scopes the block to
  this brand. `"True"` with a capital, or `"false"`, silently shows other
  brands' members.
- **The brand's own words for the two links.** The card link goes to the join
  flow, not to that member's profile, so the wording must not promise a profile.
- **An empty-state sentence** that is true when the block is empty.

**Pairing.** `heading-block` above it — the grid has no heading of its own and
says nothing about itself without one. `member-filter` wraps two or more of
these and switches between them. `cta-band` below it.

Think hard before `portrait-wall` or `member-strip` on the same page: all three
are the same gesture, and a page making it twice undercuts itself. Not an
enforced edge — a small strip in a hero above a live grid lower down is
defensible; two big member displays in one column is not.

**Brand adaptability.** `--card-radius`, `--card-border` and `--card-shadow`
carry the whole feel — hairline-and-square reads as a directory, rounded-and-
shadowed as a product. `--color-primary` tints the initial tile that stands in
for a member with no photograph, and colours the verified badge.

Two axes. **Card style** — `plain` (square photo, no furniture), `framed`
(bordered card on your surface colour), `portrait` (a taller photo, cropping
faces less). All three are deliberately quiet: member photographs are a real,
mixed set, and furniture that flatters a shoot makes a mixed set look worse.
**Layout** — `grid` wraps onto as many rows as it needs, `rail` is one row the
visitor swipes through snapping to each member, and `marquee` is that row moving
along by itself.

**`rail` never moves on its own**, the same bargain `gallery-scroll` makes.
**`marquee` does, and it is the only rung needing a markup change as well as the
class**: swap `data-hub-module="reveal"` for `"marquee"`. Where the behaviour
library is not served the block is then simply the rail, which is why choosing
it is safe.

Everything the marquee needs is built rather than authored: it clones the run for
a seamless loop, keeps the copies out of the tab order and hidden from assistive
technology, and **makes its own pause control**. That control is not decoration —
content that moves by itself needs a way to stop it, and pause-on-hover is not
one, doing nothing for a visitor on a phone or a keyboard. It also halts on
hover, on focus, while dragged, and off screen. Under reduced motion nothing
moves and no control appears.

The `reveal` hook on the other two rungs fades the block in where the library is
served.
