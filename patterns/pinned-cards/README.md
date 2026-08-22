# pinned-cards

**What it is and when to use it.** Two to four full-screen photographic cards
that pin at the top of the viewport as the page scrolls, so each one slides up
over the last like a hand being dealt. Every card carries a solid panel with a
title and a line or two of copy; the last one carries the join control.

Use it where a brand has a small number of genuinely strong photographs and
something ordered to say over them — a sequence, a progression, a case built in
stages. It is the most attention-taking section in the library and should be the
only such section on the page.

Do **not** use it for a peer set: the stacking says *and then*, so equal things
stacked this way tell a reader there is an order they have missed —
`media-card-grid` is the pattern for those. Fewer than two cards is a hero with
extra scrolling; more than four stops being a hand and becomes a slideshow the
reader cannot skip.

**What it needs.** One strong landscape photograph per card, at least 1600px
wide, each with its own alt text. The photographs are the section — a weak one
occupies a whole screen and says nothing, and there is no scrim to hide behind
because the words sit on their own panel. A short title and one or two sentences
per card, in an order that means something.

**Increment `--pinned-cards-i` on every card.** It is the stacking order, and
the later card has to sit over the earlier one or the effect runs backwards. It
is a custom property in a `style` attribute, which is the only thing a `style`
attribute is permitted to carry here.

**Keep the join control on the last card only.** Three identical buttons is one
decision asked three times, and it makes the earlier cards feel like adverts
rather than argument. Delete the whole action paragraph from every other card.

**Pairing.** `opener-split` or `heading-block` above it if the section wants a
fuller introduction than its own head block gives — delete the `h2` and its
`aria-labelledby` if you do. `cta-band` after it.

`avoid-with` names `cta-curtain`, and that one is mechanical rather than
editorial: both build a stacking order out of `position: sticky`, and two of
them on one page put the curtain's pinned panel and these cards' z-indexes in
the same argument.

**Brand adaptability.** The words sit on `--color-surface` with `--color-text`
and `--color-text-soft`, which is the whole reason this pattern has no contrast
question to answer: nothing is ever laid over the photograph, so no scrim has to
carry a ratio and no token is asked to promise something against an image. The
panel heading takes `--color-text` rather than `--color-heading` — a panel is
not `--color-bg` and the heading token promises nothing there. The section title
above the cards does take `--color-heading`, where the ground genuinely is
`--color-bg` and the `clamp()` floor is 28px.

The control is `--color-primary` with `--color-on-primary`; its focus ring is
`--color-focus`, landing on the panel rather than the photograph.

`--card-radius` shapes both card and panel. Two dials:
`--pinned-cards-panel-max` (default `34rem`) holds the panel to a readable
measure on a wide screen, and `--pinned-cards-step` (default `6vh`) is the
overlap between cards — larger makes the deal more pronounced, `0` makes them
flush.

**The pin waits on viewport height as well as width, and that is the most
important thing in this file.** A pinned card holds its top against the top of
the viewport, so anything below the fold *inside* that card cannot be scrolled
to — it is simply unreachable. So the sticky rule is gated on
`(min-width: 48rem) and (min-height: 44rem)`, and everywhere else the cards are
a plain stack of full-height sections, one after another, all reachable.

That gate is why a phone in landscape, a short window and a desktop at 200%
browser zoom all get the plain stack, as does a browser without
`position: sticky`. **The plain stack is a correct render, not a fallback.**

This is not hypothetical: one of the designer pages this library was built from
set `height: 100%; overflow: hidden` on a full-viewport section and became
unscrollable at 200% zoom, failing WCAG 1.4.4. The card here uses `min-height`,
never `height`, for the same reason — copy that outgrows its card must grow the
card rather than overflow it.

**Nothing animates.** The cards are laid out by the page's own scroll position,
so there is no motion to remove under `prefers-reduced-motion` and the pattern
declares `motion: none` honestly. On paper the cards unpin so the whole set
prints instead of one card printing over the rest.
