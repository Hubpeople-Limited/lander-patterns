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
3. **Left/Right** or **Up/Down** arrows move to the next or previous radio.
   The browser checks it as focus arrives, so the stage turns with the arrow
   key — no Enter, no Space, nothing to activate.
4. **Tab** again leaves the whole group in one press, as a radio group should.

A screen reader announces each radio as "Testimonial 2 of 3", the group is
named by the section heading, and each card is a `role="group"` carrying the
same position, so a card read out of context still says which one it is. Cards
that are off stage are `visibility: hidden` and are not in the reading order
until the reader brings them in.

**There are no prev/next arrows.** In the source they were `<label
tabindex="0">` elements, and a label is not activated by Enter or Space, so
they were focusable and did nothing. Rebuilt honestly they would need a
separate two-label set per slide, renumbered on every content change, and two
labels pointing at one radio concatenate into its accessible name. The dots
reach every slide in one press from either device, so the arrows bought
nothing. **There is no star rating either** — the source drew five stars on
every one of its twelve cards whatever the review said, and `testimonial-grid`
already settled that question: a rating is a separate factual claim needing a
review system behind it, not decoration.

**What it needs.** At least three real testimonials — each quote as the person
actually wrote it, their real name, and a true attribution line. One real
portrait each, square, at least 176px, with alt text describing the person.
A section heading. Plus five structural slots that are not content: the
heading's id, the radio group's name, and one id per slide. Fill them with
something specific to the page; two carousels sharing them would drive each
other. Keep quotes to about two lines — the stage height is fixed on purpose,
so the page does not jump as the reader moves through the set, and a long
quote overruns it. Raise `--testimonial-carousel-stage-h` if it does.

**Pairing.** `heading-block` above it, which is why this carries only a plain
`<h2>`. **Do not put it on the same page as `testimonial-grid`**: two
presentations of the same evidence read as padding, and whichever comes second
looks like the brand ran out of new things to say. Pick the grid when three
quotes are all there is, and this when there are eight and they are worth
reading. It is full-bleed, so give it clear air above and below rather than
butting it against another edge-to-edge block.

**Brand adaptability.** The active card is `--color-primary` with
`--color-on-primary` ink. That is a real design change from a near-black card:
the quote is small text on a coloured ground, and only three token pairs carry
a stated contrast ratio, so brand colour is the one that works — the brand's
action colour now leads the section, which suits a warm brand and makes a
loud one very loud. `--card-radius`, `--card-border` and `--card-shadow` set the
character of all three cards; `--chip-radius` decides whether the dots are
round or squared; `--font-heading` at weight 800 with tight tracking does the
work in the quote. The stage geometry is two of the pattern's own properties,
`--testimonial-carousel-card-w` and `--testimonial-carousel-side-offset`, so a
brand can widen the card or push the neighbours further out without touching a
transform. Below 60rem the neighbours are not drawn at all.
