# cta-curtain

**What it is and when to use it.** The page's closing CTA, a full viewport
tall, pinned behind the last content section and uncovered as that section
scrolls up and away — a sheet being lifted off. Three CSS rules do all of it
and no JavaScript is involved. Nothing animates, but that is not the same as
having nothing for reduced motion to switch off: the sheet still travels a
screen under the reader's own scrolling, and the shadow is the cue that says
so, which is why it flattens under `prefers-reduced-motion` exactly as the
source did. Use it once, as the last block on a long page,
where the visitor has already read the case and the only thing left is to act.
Do **not** use it on a short page (there is no scroll to spend), do not use two
on one page, and do not put anything after it — content below the spacer looks
like a mistake.

**What it needs.** A closing headline and one supporting line, both real copy,
plus the platform's join control, which the markup already carries as
`{{join.url}}` / `{{join.text}}`. And it needs **the section that covers it**.
That is the pattern's one unusual demand: it spans two elements.

- The panel and the cover live inside one `.cta-curtain` wrapper, **panel
  first**. That order is what makes the pin work and cannot be swapped.
- Take the page's existing last content section — whatever pattern it is — and
  move it, unchanged, inside `<div class="cta-curtain-cover">`. The wrapper
  supplies the opaque background and the leading-edge shadow; the section keeps
  its own markup and styling. Putting the class straight on the section instead
  works only if that section is already opaque and has no collapsing top
  margin, so the wrapper is the version to use.
- Leave `.cta-curtain-spacer` in place. It restores the scroll height the
  cover's negative margin removes. Delete it and the page ends a screen early
  and the panel never fully uncovers.

**Pairing.** `hero-split` opens the page and this closes it. `pricing-tiers`
makes a good covering sheet — the tiers lift away and the join CTA is what is
left. Never with `cta-sticky`: a full-screen finale and a fixed bottom bar
fight for the same decision, and the bar sits over the panel the whole reveal.
Never with `cta-band` or `cta-image` either, for a plainer reason: all three
close a page, and a page that closes three times has not decided how it ends.
Reach for this one only when the uncovering is the point; `cta-band` is the
ordinary finale and `cta-image` the photographic one.
Note the reading order — the panel precedes the covering section in the DOM, so
a screen-reader or keyboard visitor meets the join link before the content that
visually sits above it. The link's own words carry the meaning, which keeps
that honest, but it is a real trade the pin forces and worth knowing.

**Fallbacks — and note the third one, because it is the common case.** The CSS
unwinds in three situations: where `position: sticky` is unsupported; on
viewports under 34rem tall, where a pinned full-height panel would clip its own
headline; and **on anything narrower than 35rem, which is every phone**. The
source turned the curtain off below 560px and said so in a comment, and this
follows it — a full-screen panel behind a cover is least legible exactly where
the screen is smallest. In all three the panel sizes to its content and sits in
normal flow as an ordinary closing section.
The effect is lost, the CTA is still readable and reachable. Heights use
`100svh` so a mobile address bar showing or hiding cannot break the pin, with a
`100vh` line before each as the fallback for engines without `svh`.

**Brand adaptability.** The panel sits on `--color-surface-soft` against the
cover's `--color-bg`, so the two grounds read as different surfaces the moment
the seam moves. The lifting edge carries a large soft shadow at the scale of
the gesture rather than a card's, and a rounded lower edge — together they are
most of the illusion. The depth is `--cta-curtain-lift`, the pattern's own
dial rather than `--card-shadow`, because a card's shadow reads as a hairline
at this scale. Set it to `none` for a flat brand and the sheet reads as a
clean cut instead, which is a legitimate look rather than a bug.
`--font-heading` and the title's clamp carry the drama. A brand wanting a
darker finale can override the panel ground in its own CSS, but must then
re-check the heading, lead and button contrast on it — the contract only
guarantees those against the surface tokens.
