# photo-cards

**What it is and when to use it.** A run of cards, each with its photograph in
its own box at the top and every word set below it on the card's own surface.
Nothing is ever laid over an image, so there is no scrim, no over-photo contrast
question, and nothing that depends on what a particular photograph happens to
look like.

That is the reason to reach for it. **It is the safest card run in the library
for a brand whose imagery is unpredictable** — user-supplied photographs, a
mixed-quality library, anything a partner will swap out later without telling
anyone. `media-card-grid` sets its copy over the picture on a tuned scrim, which
looks better when the photographs are good and degrades badly when one turns out
to be pale, busy or portrait-cropped the wrong way.

Choose between the two on that question alone: **do you control the
photographs?** If you do, `media-card-grid` is the stronger composition. If you
do not, use this. They refuse each other, because two card runs answering the
same question with different furniture is the section appearing twice.

**What it needs.** One real photograph per card with its own alt text, a short
heading, one or two sentences, and a real destination. Three or four cards read
best; the grid is `auto-fit`, so any count fills its row rather than leaving a
hole. The chip is optional and should be deleted where an item has no real
label — a row of chips reading *Featured*, *Popular*, *New* invented to fill the
slot is worse than no chips.

**There is deliberately no button in the card.** Every link a pattern may carry
points at `{{join.url}}`, so a run of three cards each with its own join button
is one decision asked three times, and it makes the cards read as adverts rather
than as things worth looking at. The heading is the link and the whole card is
its target, which gives one focus stop and one accessible name per card. If a
page needs an ask, that is `cta-band`'s job at the foot of it.

**Pairing.** `opener-split` or `heading-block` above it, in which case delete
this pattern's own `h2` and the `aria-labelledby` pointing at it. `cta-band`
below. `avoid-with` names `media-card-grid` for the reason above, and
`gallery-scroll`, which is a second horizontal run of images competing with this
one for the same attention.

**Brand adaptability.** Every ink is a pair the contract states.
`--color-text` carries the heading and the chip; `--color-text-soft` carries the
copy. Both sit on `--color-surface` or `--color-surface-soft`, the grounds those
tokens are promised against. The card heading is `--color-text` rather than
`--color-heading`: a card is not `--color-bg`, and the heading token promises
nothing there. The section title above the run does take `--color-heading`,
where the ground genuinely is the page's and the `clamp()` floor is 28px.

The chip is `--color-text` on `--color-surface-soft` rather than a brand tint,
which is what lets it hold a real ratio at 12px. A chip is a label, never a
control, and it must never be the only thing carrying a meaning.

The card takes `--color-surface`, `--card-border`, `--card-radius` and
`--card-shadow` together, because a brand may set the border to `none` and the
shadow to `none` independently and the card still has to read as a card. On a
brand that sets both flat, the surface against the page ground is what separates
it — which is why the image also paints `--color-surface-soft` behind itself: a
slow or failed image leaves a card-shaped hole rather than a collapsed one.

Two dials: `--photo-cards-min` (default `17rem`) is the narrowest a card may get
before the grid drops a column, and `--photo-cards-ratio` (default `3 / 2`) sets
the image box. A brand with portrait photography should set the ratio rather
than crop every file — `4 / 5` and `1 / 1` both work without touching anything
else.

**The whole card is clickable, and that is done from the heading's own link
rather than by wrapping the card in an anchor.** Wrapping puts the image and the
copy inside the link, which gives assistive technology a name made of everything
in the card; the stretched pseudo-element keeps the accessible name as the
heading text alone. The trade is that text inside the card cannot be selected
with the mouse, which is the accepted cost of the technique and worth knowing
before anyone reports it as a bug.
