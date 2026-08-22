# member-strip

**What it is and when to use it.** A short row of real members — photograph,
name and one optional line each — small enough to sit inside a hero or directly
beside a control.

It exists because proof belongs **at the point of friction**. The homepage brief
asks for it there in as many words, and until now the library could not do it at
any size: all three testimonial patterns are full-width sections that occupy
their own screen, so the proof was always at least one scroll away from the ask
it was meant to support.

Use it under a hero's control, inside `hero-squeeze`, or beside a closing band.

**It is not `portrait-wall`, and the two refuse each other.** That pattern is
fifteen anonymous faces with `alt=""` throughout, `one-per-page`, and its own
README says it argues nothing on its own — it is scale and atmosphere. This one
is *these specific people, by name*. A page carrying both is making the same
gesture twice with different furniture, and the anonymous version undercuts the
named one.

Do **not** use it as a gallery. Four to eight members; below four it reads as
the only four the brand has, and above eight it stops being a strip and becomes
the wall.

**What it needs, and this is the strictest consent gate in the library.** Four
to eight real members the brand can name, each with their real photograph and
the name they actually use on the platform.

**Every one of them must have agreed to appear on a public page anyone can
reach without an account.** Consent to be a member is not consent to be
marketing. This is a face and a username on an acquisition page, and on this
vertical the consequences of getting it wrong land on someone who did not
choose them — a member's neighbours, family or employer can be the audience for
the ad this page serves.

That gate is not satisfied by the members existing, by the photographs being
real, or by the platform's terms permitting it. It is satisfied by somebody
having asked them. If nobody has, use `rating-mark` or a `quote-feature` from
someone who did agree.

Never stock, never the same face twice, and never a member invented to lengthen
the row.

**The `alt` is empty and must stay empty.** The name sits directly beside the
photograph and carries it; describing the face again is noise to anyone using a
screen reader. The meta line is optional — a rating, a city, how long they have
been a member — and is deleted rather than padded when there is nothing true and
short to put in it.

**Pairing.** Inside `hero-split`, `hero-centred` or `hero-squeeze`; beside
`cta-band`; with `rating-mark` where the brand publishes an aggregate score as
well as individual members. `avoid-with` names `portrait-wall` alone.

**Brand adaptability. It sets no ink of its own**, so it takes the colour of
whatever it sits in — a page ground, a brand-coloured band or a scrim — which is
by definition the ink the contract promises against that ground.

**The meta line inherits too, and that is not an oversight.**
`--color-text-soft` is promised against page grounds only, and this pattern's
own placements put it on a scrim and on `--color-primary`, where it measures
as low as 1.12:1. A token whose name contains *text* is not a token that
travels with the text: the promise is about a ground, not about a role.

The photograph paints `--color-surface` behind itself, so a slow or failed
image leaves a circle rather than collapsing the row and dropping every name
onto a different line.

One dial: `--member-strip-photo` (default `3.5rem`) sizes the photograph, and
the name column follows it, so changing one changes both and the row stays on
its grid.
