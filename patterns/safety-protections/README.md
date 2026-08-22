# safety-protections

**What it is and when to use it.** A grid of cards, one per protection a brand
actually operates, each carrying three registers in a fixed order: the name of
the protection, what the brand does in plain words, and one line saying what
that means for the person reading. Use it on a safety page — the page a
hesitant visitor reads immediately before deciding whether to join, where doubt
about safety is the objection that costs the sign-up. It is also legitimate on a
homepage or landing page where safety is one section among several.

The three registers are the point and they are not interchangeable. Names alone
read as a boast; process alone reads as a policy document. The third line is
what a scanning reader leaves with, which is why it is the darkest text in the
card and sits under its own rule at the card's floor.

Do **not** use it as a general feature grid (`benefit-tiles`), or for
compliance marks and memberships, which are a different claim with their own
evidence (`trust-row`). Furniture the material cannot fill is how a trust page
starts lying by layout.

**What it needs.** Real protections the brand genuinely operates, drawn from
material the brand supplied, and nothing else. **This is the strictest `needs`
in the library and it is not a formality.** An invented safety claim is a
promise about someone's physical safety that nobody is keeping — "every photo is
reviewed before it appears", written because it sounds like what a dating brand
says, is the failure this exists for. Nothing inferred from competitors,
softened from what the brand said, or padded with reassuring texture: no
invented review processes, response times or team descriptions. Three true
protections beat six where three are hopeful. If the material names none, say
so rather than writing across the gap.

Per card: `protection-name` as the brand names it; `protection-what`, one or two
plain sentences of what happens; `protection-effect`, one sentence of
consequence. `effect-label` names the third register and is **the same words on
every card** — a column header, not a sentence. Section level: `section-id`,
`section-title`, and `section-intro`, deleted when nothing true fills it.

Several may sit on one page, one per category, which is why `one-per-page` is
`no`. Three to six categories reads as organised without fragmenting, drawn from
the material's own seams rather than a borrowed taxonomy. Every `section-id`
must differ.

**Pairing.** `heading-block` or `opener-split` above it when a category wants a
fuller opener — delete the `h2` and its `aria-labelledby` if you do. `trust-row`
after it, then `faq-details`. No `avoid-with` entry: the section paints no
ground, carries no image and makes no call to action, so it fights nothing.

**Not directly under `steps-plain`.** Both are runs of surface cells hairlined
in `--color-rule` at the same column count, so stacked they read as one card
wall with a heading lost in the middle. Put a full-width section between them,
or lead this one with an opener that changes the rhythm.

**Brand adaptability.** Every colour is a pair the contract states.
`--color-text` carries the protection name and the takeaway line and is promised
against `--color-surface`; `--color-text-soft` carries the description and the
intro and is promised against whatever surface it sits on. The section title is
the one use of `--color-heading`, and both halves of that token's contract are
met deliberately: the section paints no ground, so it sits on `--color-bg`, and
the `clamp()` floor is 28px, above the 24px the token is promised at. Move
either and the guarantee stops holding.

**Nothing here is tinted, deliberately.** The takeaway line must read as
distinct, the call-to-action colour is the wrong tool for it, and no other
accent carries a stated ratio on a card surface — so the emphasis is weight,
position and a hairline, which settles "never colour alone" outright.

**`--color-rule` is load-bearing here, and the pattern overrides two brand dials
to make it so.** The outline is a plain hairline rather than `--card-border`,
and there is no `--card-shadow`: a page that earns trust by being quiet is not a
page for elevation. The cost is worth stating. Where `--color-surface` and
`--color-bg` are nearly the same colour, that hairline is the only thing
separating one protection from the next, and a brand setting `--color-rule` very
soft — which it may — will find the cards stop reading as cards. What survives
is a stack of named protections still carrying three registers in order: a
correct render, not a broken one. A brand wanting its usual card treatment sets
`--card-border` and `--card-shadow` on `.safety-protections-item` itself.

`--card-radius` shapes the cards. One column on phones, two from `48rem`, then
`auto-fit` from `64rem` so two protections keep two columns and four leave no
orphan.
