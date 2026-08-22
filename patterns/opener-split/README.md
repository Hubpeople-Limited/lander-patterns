# opener-split

**What it is and when to use it.** A section opener built as two halves: a
display title held to a short measure on the left, and its supporting line
pushed to the right and set to the title's last baseline. Below the wide band it
stacks into one column and reads as an ordinary heading with a paragraph.

It is the editorial alternative to `heading-block`, which is centred, stacked,
and puts a rule-flanked eyebrow above the title. Neither is better; they are
different registers. This one suits a page that wants to look like it was
designed rather than assembled, and it gives the supporting line real weight
instead of treating it as a subtitle.

**Pick one opener style per page and hold it.** `heading-block` and this pattern
answer exactly the same question, so a page carrying both looks like two people
built it. There is no `avoid-with` entry between them, because that field is for
patterns that fight structurally and these do not — a page could legitimately
use `heading-block` in a narrow column and this across a full-width run. But if
you are reaching for both without being able to say why, use one.

**What it needs.** A title, and one supporting sentence **that says something
the title does not**. That second half is the whole bar. This layout gives the
supporting line as much optical weight as the title, so a line restating the
heading in longer words is more conspicuously empty here than it would be under
`heading-block`. If there is nothing to add, delete the paragraph and let the
title stand alone — the grid collapses to one column and it still reads.

The eyebrow is for a section that genuinely belongs to a named group — a
category, a stage, a numbered part. It is not a decorative kicker, and a page
where every opener has one has stopped meaning anything by them. Delete it
otherwise.

`opener-split--ruled` adds a hairline under the whole block. Use it where the
opener needs separating from what follows — typically above a dense run like
`steps-plain` or `faq-details` — and leave it off where the section beneath
already paints its own ground.

**Pairing.** Above `steps-plain`, `benefit-tiles`, `zigzag-rows` or
`faq-details`, all of which carry their own `h2` that should then be deleted
along with any `aria-labelledby` pointing at it. It has no ground of its own, no
image and no call to action, so it fights nothing and carries no `avoid-with`.

Note the heading level. This ships an `<h2>`, so it is a section opener rather
than a page opener — it never carries the page's `h1`. On a page whose only
heading structure is a run of these, that is correct; on one opening with a
hero, the hero owns the `h1` as usual.

**Brand adaptability.** The title is the one use of `--color-heading`, and both
halves of that token's contract are met deliberately: the component paints no
ground, so it sits on `--color-bg`, and the `clamp()` floor is 30px, above the
24px the token is promised at. The eyebrow and the supporting line are
`--color-text-soft`, which is contracted against the surface it sits on — the
eyebrow in particular is small text and must never take the heading colour,
which promises nothing at that size.

`--color-rule` draws the optional hairline and is decorative: the modifier is
separation, never meaning.

Two dials worth knowing. `--opener-split-title-measure` (default `14ch`) is what
makes the title wrap early and read as display type rather than as a headline
running the width of the page; a brand with a very wide or very condensed
heading face may want it a little different. `--opener-split-intro-measure`
(default `42ch`) holds the supporting line to a readable width independently of
the container.

**The side-by-side arrangement waits for `64rem` rather than the usual `48rem`,
and that is deliberate.** Two half-width columns at tablet width leave the title
about seven characters wide, which wraps a three-word heading into three lines.
The stacked form is the correct render at that size, not a fallback.
