# quote-feature

**What it is and when to use it.** One testimonial, set at display size on a
full-width tinted stage, with a tracked eyebrow pinned to the top of the stage,
an optional stars line, and a circular portrait with name and role beneath. It
spends a whole screen on the single best thing a customer has said. Use it when
a brand has exactly one quote worth that much room.

That is the case it exists for. `testimonial-grid` needs a stock of at least
three real testimonials and its `needs` field gates use, so a brand with one
good quote has no honest pattern to reach for and the temptation is to invent
two more. This is the pattern for one. Do **not** use it for anonymous praise,
for a paraphrase, or for a line written in-house and attributed to a customer:
the size of the type is the claim, and it makes an invented quote look like the
most trustworthy thing on the page. If there is no quote, there is no section.

**What it needs.** One real testimonial, word for word as the person wrote it,
short enough to read at display size — the quote is held to a 20-character
measure, so roughly fifteen to twenty-five words is the working range. A real
name, and an attribution line that is true (role, location, how long they have
been a member). One real portrait of that person, square, at least 160px, with
alt text describing them. The eyebrow is one short label from brand material.

The stars line is optional and gated: fill `rating` and `rating-label` only
where a real published rating exists, and delete the whole `<p>` otherwise. A
star count is a separate factual claim about aggregate data and needs a review
system behind it to be true. Five stars drawn by default is a fabrication, and
it is the fastest way to make a genuine quote read as marketing.

**Pairing.** It carries its own eyebrow, so it needs no heading section above
it. It sits well after a stats or steps section, where a run of figures or
process copy has earned a pause, and it works as the last content section
before the page's closing call to action.

Do not put it on the same page as `testimonial-grid`. Both are social proof
from named people; two of them on one page split the reader's trust rather
than doubling it, and a brand with enough material for the grid does not need
this one. Where a brand has three or more testimonials, use `testimonial-grid`
and drop this pattern; where it has one, use this one. `one-per-page: yes`:
two full-screen quote stages on one page is a mistake, not a layout choice.

Give it room. The stage is a tint edge to edge, so it reads as a break in the
page and wants a section either side that is not also tinted.

**Brand adaptability.** The stage is `--color-surface-soft`, so how far the
section separates from the page is entirely the brand's business — a near-white
soft tint gives a whisper of separation, a saturated one gives a hard band. The
quote takes `--font-heading` at weight 650 with tight negative tracking, so the
brand's display face does nearly all of the work here; a serif reads as an
editorial pull quote and a grotesque as a product claim, from the same markup.

Every ink on the stage is `--color-text` or `--color-text-soft`, and that is
deliberate rather than dull. The quote is display-size but it is not sitting on
`--color-bg`, and `--color-heading` promises 3:1 against `--color-bg` only —
against a surface it measures as low as 1.5:1 on a conforming brand. The stars
are the same case: at 18px they are small text on a coloured ground, so they
take the one ink guaranteed on every page ground. `--color-primary-dark` there
measures 1.75:1 on the sample dark brand, which is a stars line nobody can see.

The portrait's roundness is the pattern's own `--quote-feature-portrait-radius`
rather than `--card-radius`, so a sharp-cornered brand keeps a round face by
default and can square it by overriding that one property.
