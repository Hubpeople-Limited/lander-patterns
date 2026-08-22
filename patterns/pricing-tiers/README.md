# pricing-tiers

**What it is and when to use it.** Two or three tier cards, structurally
identical, equal height, CTAs bottom-aligned whatever each tier's feature
count. Use it on the pricing page when the brand sells distinct tiers. Do
**not** use it for a single-plan brand (say the one plan plainly instead),
and never pad a tier with invented features to balance the row — a card with
three real lines beats one with six half-true ones.

**What it needs.** The real tiers: names, actual prices with their currency,
and each tier's genuine features from brand material. If one tier is
recommended, that comes from the brand too — keep the flag's *words* ("Most
members choose this"), because the tinted chip alone is colour-only meaning
and colour-only meaning is a failure. Delete the flag line entirely on
non-recommended tiers; if no tier is recommended, delete it everywhere.

**Pairing.** `stats-band` above it on a long pricing page, so the numbers land
before the price. Keep detailed feature *comparison* out of the cards — if the
brand needs a full matrix, that is a table, a different pattern.

**Brand adaptability.** `--card-border`, `--card-radius` and `--card-shadow`
set the whole feel — hairline-and-flat reads editorial, shadowed-and-round
reads friendly. The price uses `--color-text`, not `--color-heading` — the
card's ground is `--color-surface` and the heading token is only guaranteed
against `--color-bg`, not against a surface, so the one saturated element per card
is the CTA. Cards wrap to one column on phones automatically.

**Behaviour (gated).** The card grid carries the `reveal` hook: on platforms
serving the behaviour library, cards fade-and-rise in as they scroll into
view, staggered, and reduced-motion visitors get no animation at all. Without
the library the attributes are inert and the page renders exactly as
authored — never design as if the animation is guaranteed.
