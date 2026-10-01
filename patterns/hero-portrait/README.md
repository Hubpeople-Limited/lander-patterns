# hero-portrait

**What it is and when to use it.** The sign-up opener with a person in it:
one large portrait on one side, the headline, one line and the sign-up card
on the other. It is built to hold `signup-card` in place of its join button;
with the button alone it is a portrait opener with one control. Use it on a
homepage or a landing page whose job is sign-ups, for a brand with one good
photograph of a person or a couple. `hero-split` is the choice when the
picture is a scene rather than a face; this one gives the face the room.

**Who the portrait works best with.** Someone who stands for the brand's
members: a photograph the brand has the right to use, with the person's OK. It
carries no name or caption, so a named member, a testimonial's face or a
founder reads better in a pattern built to name them - `member-strip`,
`quote-feature`, `portrait-prose`. Before the brand has a photograph the slot takes the library's
placeholder, a line drawing, never a likeness, drawn whole on the tint rather
than cropped, so "Photo to come" reads even in the phone strip.

**Three axes.**

| Axis | Rungs |
|---|---|
| `side` | `start` portrait left (the default), `end` portrait right. On a phone it always comes first |
| `shape` | `rounded`, twice the brand's card rounding; `arch`, a half circle across the top on every brand; `half-bleed`, to the screen's edge and the section's full height |
| `ground` | `plain`, `soft`, `brand`, `deep`, each naming its own ink |

**What it needs.** The portrait, at least 1200px wide in portrait, with alt
text saying what is in it; it is cropped high (`object-position: 50% 25%`), so
the face should sit in the upper third. It is the page's LCP element: it ships
`fetchpriority="high"`, never takes `loading="lazy"`, and its `width` and
`height` are set to the file's own pixels. A headline and one sentence in the
brand's own words. The card's own needs are in `signup-card`'s README.

**Holding the card.** Put `signup-card` where the join button is, as in
`hero-split`. Wide, the card sits under the words, in their column, so it
never lands on the headline or the line under it at any width. The portrait
keeps a fixed height anchored at the top, so a taller step never moves or
stretches it; that height is set to end level with the card's first step when
the behaviour library runs it, and on `half-bleed` to reach the section's
foot. On a phone the portrait shrinks to a short strip cropped to the face, so
the card's first question is on the first screen below the site header.

**Not on a page with `hero-split`, `hero-overlay`, `hero-centred`,
`hero-squeeze`, `hero-stated` or `signup-steps`.** Each opens the page and
carries its `h1`; a page opens once.

**Pairing.** `member-grid` below it, under a `heading-block`: the portrait
says who the brand is for, the members show who is there. `steps-plain` for
how joining works. It reads better without `picker-chips` while it holds the
card: two first questions is none.

**Brand adaptability.** Each ground names its own ink and every rule reads
that pair, as in `hero-stated`. On `plain` the title is `--color-heading`,
held to a clamp floor of 2rem; elsewhere it takes the ground's own ink.
`--card-radius` sets the `rounded` corners and the foot of the `arch`;
`--font-heading` carries the title at up to 3.5rem, its leading floored at
1.45 cap heights. Heights come from the width, never the viewport height: a
`clamp(13rem, 64vw, 20rem)` strip on a phone (`clamp(8rem, 36vw, 10rem)`
holding the card), `clamp(30rem, 52vw, 44rem)` beside the words and
`clamp(38rem, 66vw, 50rem)` beside the card. On `half-bleed` the words line up
with the container above and below.
