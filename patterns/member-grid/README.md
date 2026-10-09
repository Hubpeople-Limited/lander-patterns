# member-grid

**What it is and when to use it.** A block of your brand's own members, filled
in by the platform when the page is built. The page ships an **empty
`<section>`**; the platform writes real profiles into it, in the HTML a crawler
receives — no JavaScript, nothing fetched in the visitor's browser.

That makes it the one people-pattern on a location page that is worth having.
A page per town carrying the same words with the place name swapped is the
thing Google's spam policy names as doorway abuse; a page carrying real members
who are only on *that* page is unique first-party data no competitor holds.

Use it where the members are the argument: a location page, a community page,
or a homepage that opens on who is already here. Two on one page earn their
place only when the sets genuinely differ, which is `member-filter`.

**Set `data-members-min` and mean it.** Below that many members the platform
renders the empty state instead of a thin grid. A location page with four faces
on it is the doorway page this pattern exists to avoid, so let it refuse.

**What it needs.** Nothing from the partner, which sets it apart from every
other people-pattern here: no photographs, consent or names to check. The
platform supplies the members and owns whether they may be shown.

What it does need is four decisions:

- **The place**, spelled exactly as [`lib/places`](../../lib/places/README.md)
  holds it. A wrong value is **ignored, not refused**: the block fills from
  somewhere else and looks normal, so check it before shipping. **Separate a
  list with `|`, never a comma, and end one value holding a comma with `|`**, or
  the platform splits it: `data-members-region="England: City of Manchester, Greater Manchester|"`.
- **`data-members-strict="true"`, lowercase, always.** It scopes the block to
  this brand. `"True"` with a capital, or `"false"`, silently shows other
  brands' members.
- **The brand's own words for the two links.** The card link goes to the join
  flow, not to that member's profile, so the wording must not promise a profile.
  Two more, `previous-label` and `next-label`, name the row's controls.
- **An empty-state sentence** that is true when the block is empty.

**Every setting**, with its values and default, is in this folder's
`settings.json`: who is shown, the places and how a list of them is read, the
count, and what each card carries. Nothing filters on who members are seeking.

**Pairing.** `heading-block` above it — the grid has no heading of its own and
says nothing about itself without one. `member-filter` wraps two or more of
these and switches between them. `cta-band` below it.

Think hard before `portrait-wall` or `member-strip` on the same page: all three
are the same gesture. Not an enforced edge — a small strip in a hero above a
live grid lower down is defensible; two big member displays in one column is not.

**Brand adaptability.** `--card-radius`, `--card-border` and `--card-shadow`
carry the whole feel — hairline-and-square reads as a directory, rounded-and-
shadowed as a product. `--color-primary` tints the initial tile that stands in
for a member with no photograph, and colours the verified badge.

Four axes. **Card style** — `plain` (square photo, no furniture), `framed`
(bordered card on your surface colour), `portrait` (a taller photo, cropping
faces less). All three are deliberately quiet: member photographs are a real,
mixed set, and furniture that flatters a shoot makes a mixed set look worse.
**Layout** — `grid` wraps onto as many rows as it needs, `rail` is one row the
visitor swipes through snapping to each member, and `marquee` is that row moving
along by itself. **Arrows** — `top`, a round pair above the row (under it on a
phone), or `edges`, over its sides on a solid circle. **Arrows on a phone** —
`arrows`, or `swipe` to leave them off there.

**`rail` never moves on its own**, the same bargain `gallery-scroll` makes, and
shows no scroll bar: `carousel` builds the arrows, none while every member fits,
and with scripting off both rows wrap like `grid`, as a mouse has no other way
along. **`marquee` is the only rung needing a markup change as well as the
class**: swap `"reveal"` for `"marquee"` in `data-hub-module` and keep
`"carousel"`. With no library it is simply the rail.

Everything the marquee needs is built, not authored: it clones the run for a
seamless loop, keeps the copies out of the tab order and hidden from assistive
technology, and **makes its own pause control**, a round icon beside the arrows
— moving content needs a way to stop it, and pause-on-hover does nothing on a
phone or a keyboard. It also halts on hover, on focus, while dragged and off
screen. Under reduced motion nothing moves and no stop control appears; the
arrows show once it is stopped, or when it never starts.
