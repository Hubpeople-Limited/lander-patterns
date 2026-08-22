# cta-assurance

**What it is and when to use it.** The short run of reassurances that sits
directly under a join control — what it costs, whether a card is needed, how
long it takes, what is visible to whom. Two to four items, each three or four
words, separated by drawn dots.

Every other pattern in this library that carries a join control ships it as a
bare button. This is the line underneath it, and it is doing three separate
jobs at the moment a visitor hesitates: **cost** ("free to join and browse"),
**commitment** ("no card needed"), and **effort** ("two minutes"). On a brand
where discretion matters, a fourth: **exposure** — what appears on a statement,
what is visible without an account.

Removing that line does not remove the objection. It leaves it unanswered at the
one place the visitor is deciding.

Use it under any control that asks someone to sign up. It is not a section and
has no heading; it belongs inside whatever wraps the button.

Do **not** use it as a feature list. Three benefits under a button is a
different thing and reads as one — `benefit-tiles` is the pattern for what the
product does. This is only about what signing up costs and commits you to.

**What it needs.** Two to four things about signing up that are **true and
checkable**. The price, whether a card is required, how long the form takes,
what other people can see. Each must be a fact the brand can evidence.

**Three things this slot must never carry.**

- **A bare "Free".** Say what is free — *"free to join and browse"*, not
  *"Free"*. In the UK an unqualified free claim is one the ASA rules on, and
  this is exactly the place someone would write it.
- **Anything time-limited.** No *"this week only"*, no *"limited places"*, no
  countdown. Manufactured scarcity is regulator-enforceable, not a style
  choice, and nothing here can be computed on the page anyway.
- **Anything about what the reader loses by waiting.** This slot is for what
  they are *not* committing to. The moment it becomes what they will miss, it
  has stopped reassuring and started pressing.

Keep each item to three or four words. This is a line taken in at a glance, not
a sentence anyone reads.

**Pairing.** Under `hero-split`, `hero-centred`, `cta-band`, `cta-image` or
`pricing-tiers` — anywhere a control asks for a sign-up. `one-per-page` is `no`
because a long page repeats its ask at natural decision points, and the same
reassurance belongs under each.

No `avoid-with` entry: it paints no ground, carries no image and makes no ask
of its own.

**Brand adaptability. It sets no colour, and that is the whole design.** It sits
under a control that might be on the page ground, on a brand-coloured band or
over a photographic scrim, and only the pattern around it knows which.
Inheriting takes whatever ink that pattern already established — which is, by
definition, the ink the contract promises against that ground. So a single rule
is safe in all three places, where naming any token would be safe in one.

The separator is drawn as a pseudo-element rather than typed as a character.
A typed dot or pipe can go missing in a brand font, and a screen reader may
announce it; a drawn one is decoration between items that already stand alone.

The only spacing tokens it uses are `--space-2`, `--space-3` and `--space-4`,
so it inherits the brand's rhythm and nothing else. There are no dials: a
component this small does not need them, and anything it might expose belongs
to the pattern above it.
