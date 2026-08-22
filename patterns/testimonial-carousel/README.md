# testimonial-carousel

**What it is and when to use it.** A testimonial carousel with no JavaScript:
one card centre stage in the brand's action colour, its two neighbours peeking
either side at 0.94 scale, and a row of dots below. A radio group holds the
state and `:checked ~` sibling rules do the rest. Use it where a page has more
social proof than a row of cards can carry and only one screen height to spend
on it — that is the whole reason it exists, and the only reason to prefer it to
`testimonial-grid`, which shows three quotes at once with nothing to operate.

**It never advances on its own, and it must not be made to.** An
auto-advancing carousel legally requires a visible pause control (WCAG 2.2.2),
and a pause control cannot be built without script, which is why TOKENS.md
refuses them outright. This one is legitimate precisely because the reader
drives every move. Do not add a CSS animation that changes slides on a timer.

**Do not use it** for fewer than three testimonials (there is no carousel to
operate), for anonymous praise, or for anything the visitor needs in order to
decide — a carousel hides most of its content, so it is for depth, not for the
case. It is `one-per-page: yes`: a page has one body of social proof, and a
second full-bleed stage competes with the first rather than adding to it.

**How a keyboard works it.** The radios are the interface, clipped to one
pixel but left in the tab order.

1. **Tab** into the section: focus lands on the checked radio, slide one.
2. A focus ring appears on **both** the active card and its dot, so the reader
   can see where they are without a pointer.
3. **Left/Right** or **Up/Down** arrows move between slides. The browser
   checks each as focus arrives, so the stage turns with the key.
4. **Tab** again leaves the whole group in one press.

A screen reader announces each radio as "Testimonial 2 of 3" and the group by
the section heading; each card repeats its own position, so a card read out of
context still says which one it is. A card
off stage is `visibility: hidden`, so it leaves both the reading order and the
tab order until the reader brings it in. With the three slides that ship, that
only happens below 60rem — above it all three are on stage as active, previous
and next. A fourth slide is off stage at every width.

**There are no prev/next arrows.** They would need a two-label set per slide,
renumbered on every content change, and two labels pointing at one radio
concatenate into its accessible name. The dots reach every slide in one press
from either device. **There is no star rating either**: a rating is a separate
factual claim needing a review system behind it, and `testimonial-grid`
already settled that.

**What it needs.** At least three real testimonials — each quote as the person
actually wrote it, their real name, and a true attribution line. One real
portrait each, square, at least 176px, with alt text describing the person.
A section heading. Plus five structural slots that are not content: the
heading's id, the radio group's name, and one id per slide. Fill them with
something specific to the page; two carousels sharing them would drive each
other. The stage stacks all the cards on one grid cell, so it is always as
tall as the longest quote in the set rather than as tall as the one on show:
the page does not jump as the reader moves, and no card can grow down over the
dots. A long quote still costs: it sets the height for every slide.

**Pairing.** `heading-block` above it, which is why this carries only a plain
`<h2>`. **Do not put it on the same page as `testimonial-grid`**: two
presentations of the same evidence read as padding. Pick the grid when three
quotes are all there is; pick this when the set is worth stepping through.
Beyond the three that ship, each slide needs a line adding to five selector
lists, which is a change to `pattern.css` and so a version of its own — treat
much past six as a copy the brand owns. It is full-bleed, so give it clear air
above and below.

**Brand adaptability.** The active card is `--color-primary` with
`--color-on-primary` ink — a real change from a near-black card. The quote is
small text on a coloured ground and only three token pairs carry a stated
ratio, so this is the one that works. The action colour leads the section,
which suits a warm brand and makes a loud one very loud. `--card-radius`, `--card-border` and `--card-shadow` set the
character of all three cards; `--chip-radius` decides whether the dots are
round or squared; `--font-heading` at weight 800 with tight tracking does the
work in the quote. The stage geometry is two of the pattern's own properties,
`--testimonial-carousel-card-w` and `--testimonial-carousel-side-offset`. Both
carry responsive values on `.testimonial-carousel`, so overriding one means a
`.testimonial-carousel { … }` rule after the appended CSS — a `:root`
declaration is not specific enough to reach it. Below 60rem the neighbours are
not drawn.
