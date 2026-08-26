# hero-stated

**What it is and when to use it.** An opener made of words: a display claim,
one supporting line and the join control. No photograph, no figure, no logo.

It exists because **the library could not open a page for a brand with no
imagery.** All five other heroes name a photograph in their `needs` — 1280px,
1600px, 2000px, 2400px — and they are the only patterns carrying an `h1`. A
brand with words and nothing else had no opener, no `h1`, and no
above-the-fold control. Not a poor page: no page.

Use it for a cold start, for a brand whose photography has not arrived, and for
any brand whose argument is better made in type than in a picture. It is also
the right opener when the available imagery is weak — a bad photograph at hero
scale costs more than no photograph.

**Six looks from one pattern, and that is the point.** Take exactly one ground
modifier, and optionally the alignment:

| Modifier | Ground |
|---|---|
| `hero-stated--plain` | the page ground; the title takes the heading colour |
| `hero-stated--brand` | `--color-primary`, everything inverted |
| `hero-stated--deep` | `--color-scrim` |
| `hero-stated--centred` | added to any of the three; left-aligned is the default |

On a platform where hundreds of brands must not resemble each other, a pattern
that ships one look is a pattern that will be recognised across the estate.
Three grounds and two alignments is the cheapest multiplication available.

**What it needs.** A headline the brand can stand behind and one supporting
sentence that says something the headline does not. That is the whole gate, and
it is why this pattern is available to every brand on the platform.

The headline is held to `10.75em`, so it wraps early and reads as display type
rather than as a sentence running the width of the page. Write it to be broken:
three to seven words is the range this shape carries.

The eyebrow is deleted rather than padded. `cta-assurance` goes in the assurance
slot — a text-only opener has no photograph doing reassurance work, so the line
under the control matters more here than anywhere else in the library.

**Pairing.** `picker-chips` directly under it turns the claim into the first
decision, which is the shape eharmony opens with. `benefit-tiles` and
`steps-plain` after it, both of which also need no photography — between them
those three build a complete page for a brand that has none. `rating-mark`
inside or beneath, where the brand publishes a score.

It refuses `hero-overlay`, `hero-split`, `hero-centred`, `hero-squeeze` and
`article-masthead`. A page opens once, and each of those is the opener for a
brand that has the photograph this one exists to do without.

**Brand adaptability.** Each ground modifier names its own ink, and every rule
in the file reads that pair rather than a token — so nothing here knows which
ground it is on, and adding a fourth would be one three-line block. The same
technique as `feature-panels`.

Every pairing is one the contract states. On `--plain` the title is
`--color-heading`, and both halves of that token's contract hold: the section
sits on `--color-bg` and the `clamp()` floor is 40px, well above the 24px it is
promised at. On `--brand` and `--deep` the title takes that ground's own ink,
because `--color-heading` promises nothing off the page ground.

**The focus ring is the ground's own ink**, which is one rule that is correct on
all three. `--color-focus` would not be: on `--color-primary` it measures 1.00,
1.14, 1.58 and 1.75 across the sample sets against a 3:1 bar. Re-derive from
`preview/tokens-*.css` before changing it.

The control is 52px rather than 48. On a page whose opener carries no image, the
button is what the eye lands on after the words, and it should look like it.

`--btn-radius` shapes it and `--container-max` holds the measure. There are no
dials: the modifiers are the variation, and a brand wanting something outside
those three grounds should say so rather than tune this one.
