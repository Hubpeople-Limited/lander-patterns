# testimonial-grid

**What it is and when to use it.** Three testimonial cards side by side, equal
height, each with the person's portrait breaking the top edge of the card and
their name bottom-aligned so the row shares one baseline. One card may invert
to the brand's action colour to lead the set. Use it where a page needs social
proof from real, attributable people. Do **not** use it with fewer than three
testimonials (two cards read as a gap, one is a pull quote — a different
thing), and do not use it for anonymous praise: a quote with no name attached
is not evidence and this pattern makes it look like evidence.

**There is no star rating, deliberately.** The source component drew five
stars on every card with `aria-label="5 star rating"` hardcoded, whatever the
review actually said — a fabricated claim rendered identically on twelve
cards. Rather than turn it into a slot, it is gone. A rating is a separate
factual claim about aggregate data, it needs a review system behind it to be
true, and a slot is exactly the thing a builder fills in with whatever looks
good. What replaces it is the optional source link on the attribution: if the
testimonial has a real public page, point at it, and if it does not, delete
the link. Evidence, not decoration.

**What it needs.** Three real testimonials: each quote as the person actually
wrote it, their name, and their attribution line (role, location, how long
they have been a member — whatever is true). One real portrait each, square,
at least 160px, with real alt text describing the person. If one testimonial
is featured, the flag's *words* come from the brand too — keep them, because
the filled card alone is colour-only meaning. Delete the flag from every
non-featured card. The source link needs a real URL and real link text or it
is deleted outright.

**Pairing.** `heading-block` above it gives the section its opener, which is
why this pattern carries only a plain `<h2>`. Do not put it directly next to a
second card grid — two rows of cards in a row stop reading as distinct
sections. And not on a page with `quote-feature`, which spends a whole screen
on a single testimonial: between them they say the same thing twice, and the
choice is whether the brand has one strong quote or several.

**Brand adaptability.** `--card-border`, `--card-radius` and `--card-shadow`
set the feel, as everywhere: hairline-and-flat reads editorial, shadowed-and-
round reads warm. The quote carries `--font-heading` at weight 800 with tight
negative tracking, so the brand's display face does most of the work. The
portrait's roundness is the pattern's own `--testimonial-grid-avatar-radius`
rather than `--card-radius`, so a sharp-cornered brand keeps round faces by
default and can square them by overriding that one property. Muted text uses
`--color-text-soft`, never a hardcoded grey, and drops to `--color-on-primary`
inside the featured card where only that pair's contrast is guaranteed.
