# safety-protections

**What it is and when to use it.** A grid of cards, one per protection a brand
actually operates, each carrying three registers in a fixed order: the name of
the protection, what the brand does in plain words, and one line saying what
that means for the person reading. Use it on a safety page — the page a
hesitant visitor reads immediately before deciding whether to join, where doubt
about safety is the objection that costs the sign-up. It is also legitimate on a
homepage or landing page where safety is one section among several.

The three registers are the point of the pattern and they are not
interchangeable. A page listing protections by name alone reads as a boast; one
that only describes process reads as a policy document. The third line is what a
scanning reader leaves with, which is why it is the darkest text in the card,
sits under its own rule, and is pinned to the card's floor.

Do **not** use it as a general feature grid — `benefit-tiles` is that. Do not
use it for compliance marks and memberships, a different claim with their own
evidence: that is `trust-row`. And do not reach for it when the brand has two or
three protections and nothing else — a short honest column is a real answer, and
furniture the material cannot fill is how a trust page starts lying by layout.

**What it needs.** Real protections the brand genuinely operates, drawn from
material the brand supplied, and nothing else. **This is the strictest `needs`
in the library and it is not a formality.** An invented safety claim is a
promise about other people's physical safety that nobody is keeping — "every
photo is reviewed before it appears", written because it sounds like the sort of
thing a dating brand says, is the failure this warning exists for. Nothing may
be inferred from what competitors do, softened from what the brand actually
said, or padded with reassuring texture: no invented review processes, response
times or team descriptions. Three protections that are true beat six where three
are hopeful. If the material names none, the honest output is to say so rather
than to write across the gap.

Per card: `protection-name` as the brand itself names it; `protection-what`, one
or two plain sentences of what actually happens; `protection-effect`, one
sentence of consequence for the reader. `effect-label` names the third register
and is **the same words on every card on the page** — a column header, not a
per-card sentence. Section level: `section-id`, `section-title`, and
`section-intro` deleted entirely when there is nothing true to put in it.

Several of these may sit on one page, one per category, which is why
`one-per-page` is `no`. Three to six categories reads as organised without
fragmenting; the categories come from the material's own seams, never a taxonomy
borrowed from another platform. Every `section-id` must differ.

**Pairing.** `heading-block` above it when a category wants a fuller opener —
delete the `h2` and its `aria-labelledby` if you do. `trust-row` after it, which
answers the neighbouring question of whether the brand is accredited rather than
what it does; then `faq-details` for the questions a reader still has. No
`avoid-with` entry: the section paints no ground, carries no image and makes no
call to action, so it fights nothing.

**Brand adaptability.** Every colour is a pair the contract states.
`--color-text` carries the protection name and the takeaway line and is promised
against `--color-surface`; `--color-text-soft` carries the description and the
intro and is promised against whatever surface it sits on. The section title is
the one use of `--color-heading`, and both halves of that token's contract are
met deliberately: the section paints no ground, so it sits on `--color-bg`, and
the `clamp()` floor is 28px, above the 24px the token is promised at. Move
either and the guarantee stops holding.

**Nothing here is tinted, and that is a decision rather than an omission.** The
takeaway line has to be visually distinct, and the primary call-to-action colour
is explicitly the wrong tool for it; the token set has no other accent carrying a
stated ratio on a card surface. So the emphasis is weight, position and a
hairline — which also settles "never colour alone" outright, there being no
colour to be alone. A brand wanting a tint here should add it in its own
stylesheet against its own measured values, not to the pattern.

`--color-rule` draws the card outline and the rule above the takeaway,
decorative twice over: nothing depends on either line being seen, only on the
words. The outline is a plain hairline rather than the `--card-border` dial and
there is no shadow — on a brand whose surface and page ground are all but the
same colour the fill alone does not group a card, and a page that earns trust by
being quiet is not a page for elevation. `--card-radius` shapes the cards. The
grid is one column on phones, two from `48rem`, three from `64rem`, so a
category holding two protections keeps two columns rather than stretching one
card across the row.
