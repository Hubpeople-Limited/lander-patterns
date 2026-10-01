# quote-image

**What it is and when to use it.** One real quote at display size over a
full-width photograph, with the name it is attributed to and a detail line
under it. It is the page's pause: a member's own words, given a band of their
own. Use it on a homepage, a landing page or an about page where the brand has
one quote worth the room. `quote-feature` gives the same quote a tinted stage
and the speaker's portrait; this one gives it a photograph.

**The quote is a real one.** Word for word, from a member's review the
platform returns or from material the brand gives, with the name it came
with. A paraphrase or praise written in-house reads as made up to a visitor,
so the library ships no sample quote for a page: with no quote, leave the
section out.

**A scene reads best behind the words.** A place, or people who stand for the
brand: the quote then speaks for the brand and the picture sets the mood. A
face behind a quote tends to be read as the person speaking, so where the
brand has the speaker's own portrait, `quote-feature` puts it beside their
words. Before the brand has a photograph the slot takes the library's
placeholder, a drawing of a place.

**Three axes.**

| Axis | Rungs |
|---|---|
| `words` | `centre` (the default), `start` or `end`: where the quote sits on a wide screen. On a phone it sits across the foot of the photograph |
| `scrim` | `fade`, a soft shade behind the quote only (the default); `full`, the whole photograph evenly darkened as well |
| `motion` | `default`, still; `moving`, the photograph drifts slowly into place |

**How the words stay readable.** They never sit on the photograph itself. The
quote's own box is painted with `--color-scrim` at the floor, and an eased fade
of the same colour carries it into the photograph: on a phone a band across the
foot that fades upward; on a wide screen a band across the middle that fades
above and below (`centre`), or a column the section's height that fades
sideways (`start`, `end`). Every line of the quote and its attribution sits on
the full level whatever its length. The floor is
`--quote-image-scrim-strength`, held by `clamp()` at `0.92`, as in
`cta-image`: a brand may make it heavier and cannot make it lighter. Every ink
is `--color-on-scrim`, the contract's stated pair.

**Over the library's placeholder the floor drops to `0.4`,** the tint behind
the drawing is the brand colour mixed into `--color-scrim`, and the drawing
takes its own area, never the one under the words: above them on a phone and
on `centre`, beside them on `start` and `end`. `ci/check_placeholder_scrim.py`
requires the drawing to show and the words to hold 4.5:1 on every rung. The
rules key on `[data-hub-placeholder]`, so a real photograph keeps the full
floor and fills the section behind the words.

**What it needs.** The quote, short enough to read at display size (about
fifteen to thirty words); the name; a detail line that is true (a place, how
long they have been a member), deleted when nothing true fills it; the
eyebrow, deleted likewise. One landscape photograph at least 2000px wide with
alt text saying what is in it. It ships `loading="lazy"`: this section is
not the page's first picture.

**Pairing.** After `steps-plain` or before `faq-details`, where the page has
said how it works and a member's voice earns a pause. Not on a page with
`quote-feature`: one quote gets the stage. A different photograph from the
opener's reads better, and so does a section between it and another
full-width photograph.

**Movement** (`motion`). Still by default. On `moving` the photograph settles
from a slight zoom over five seconds as the quote comes into view, once. The
behaviour library's `reveal` says when; the photograph never fades or slides.
Inside the reduced-motion guard, so a visitor who asked for less motion sees
it still.

**Brand adaptability.** `--font-heading` at `--weight-display` carries the
quote, so a serif brand reads as an editorial pull quote and a grotesque as a
claim; the quote's measure is `22em`, so it wraps alike on every face. The
height comes from the width, never the screen: `clamp(30rem, 125vw, 40rem)` on
a phone, `clamp(30rem, 48vw, 40rem)` wide.
