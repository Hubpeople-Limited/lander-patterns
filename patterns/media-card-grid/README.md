# media-card-grid

**What it is and when to use it.** A wrapping grid of portrait image cards.
Each card is one photograph with a corner chip, and its heading, one line of
copy and an arrow cue set over a dark bottom-up scrim. Use it for a set of
peers that each have a real photograph and a real destination — audiences,
solutions, places to go next. Do **not** use it without photography: a scrim
over a flat fill is a dark box, and this pattern is the photograph. Do not use
it for an ordered process (that is `steps-numbered`), and do not use it for
more copy than one sentence — a card that needs a paragraph is a page, and the
sentence is the link to it.

**The copy sits over the image, not below it.** Three of the four sources put
it over a scrim and one put it below; over won, for two reasons. The card then
has one visual object in it rather than two stacked ones, so a wrapping row of
them reads as a set of photographs instead of a row of boxes; and the
below-image treatment needs a card height tall enough for the worst copy in the
set, which is what drove the source's `min-height: 640px`. There is no modifier
for the other treatment. The two need different type colours, different
contrast rules and different height behaviour, so one pattern carrying both
would be two patterns sharing a name.

**What it needs.** One real photograph per card, portrait-ish and at least
1280px wide (cards render around 640×768 CSS pixels at the widest, so 2× for
retina), each with its own alt text describing that photograph. A short
heading, one sentence of copy, and a real destination URL per card. A chip
label only where the brand genuinely has one — delete the chip paragraph on
cards that do not, rather than inventing a label to balance the row.
**Set `width` and `height` on each `<img>` to the real image's intrinsic pixel
dimensions**; the shipped `640`/`768` is a stand-in for the card's 5:6 ratio
and stops layout shift only by accident. Duplicate the single `<li>` per card.

It also needs a **guaranteed contrast floor, and that is not negotiable**: text
on photography is not covered by the tokens. The scrim's lower band must be at
least 92% opaque, so the ink lands on effectively solid `--color-scrim`
whatever the photo does. The CSS enforces it: the ramp holds that full level
from the card's foot up to 45% — the whole band the text occupies — before
fading to 58% of it at 70% and to nothing at the top.
`--media-card-grid-scrim-strength` may be raised toward `1` for busy or light
images, and `clamp()` pulls any value below 0.92 back up. Neither the floor nor
the stop positions come from the sources — theirs ran 0.60–0.80 alpha with a
mid stop at 55%, because their copy sat on a solid card fill rather than on the
photograph. Only the shape of the fade is theirs. Ink is `--color-on-scrim` on
a `--color-scrim`
ground, which the contract states at 4.5:1, so a dark brand inverts cleanly.
It deliberately does not ground on `--color-heading`: that token carries no
stated ratio and may be a display colour, which leaves this card's 14px copy
with no guarantee at all.

**One link per card, and it is the heading.** One source made the whole card a
`<button>` wrapping `<div>`s and `<p>`s, which is invalid and announces the
card's entire text as the control's name. Here the heading is the link, and its
`::after` stretches over the card to give the full hit area — so the accessible
name is the destination, and there is never a second control inside the first.
The arrow cue is `aria-hidden`: it is the visual affordance and repeats nothing.

**Pairing.** `heading-block` above it when the section needs an eyebrow and an
intro, which is why this pattern carries only a plain `<h2>`. Avoid
`steps-numbered` on the same page — both are
portrait image cards with a scrim, and side by side the numbering stops reading
as meaning. `gallery-scroll` is out for the same reason: a third set of
image cards on one page and none of them means anything.

**Brand adaptability.** `--card-radius` and `--card-shadow` set nearly all the
feel: rounded-and-shadowed reads friendly, square-and-flat reads editorial.
`--font-heading` carries the section title and every card heading. The chip is
`--color-surface` with `--color-text` ink, guaranteed legible, so it
reads as a label rather than a second CTA. Card proportion is the pattern's own
`--media-card-grid-ratio` (5:6) rather than a contract token — override that one
property for a squarer or taller set. Cards drop to two columns and then one on
their own.

**Behaviour (gated).** The list carries the `reveal` hook: where the platform
serves the behaviour library the cards fade-and-rise in as they scroll into
view, staggered, and reduced-motion visitors get nothing. Without the library
the attributes are inert and the section renders in full — three of the four
sources baked `opacity: 0` in as the default and were invisible without
JavaScript. Never do that. The pattern's own motion is the arrow cue's widening
gap and a small lift on the photograph, both inside the reduced-motion guard.
