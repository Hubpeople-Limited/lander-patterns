# zigzag-rows

**What it is and when to use it.** The mid-page workhorse: a run of rows, each
one photograph beside one short piece of copy, the image side swapping row to
row. Use it for three to five *peer* things — features, audiences, promises —
each with a real photograph and about two sentences. Two rows is not a rhythm;
eight is a slog nobody scrolls to the end of. It is **not** a page opener:
`hero-split` is the split-column hero, and one of these at the top of a page
reads as a hero that forgot its CTA. Do not use it for an ordered process
(`steps-numbered`), without photography, or for copy that runs past a short
paragraph — long copy in a half-width column leaves a hole under the square
image on every second row.

**What it needs.** One real photograph per row, at least 1000px on the short
side (the media box is square by default), each with **its own alt text** — the
alt slot is per row, never shared. A short heading and one or two sentences per
row, and optionally one destination link per row: delete the whole
`zigzag-rows-action` paragraph on a row with nowhere to go rather than shipping
a dead link. **Set `width` and `height` on each `<img>` to the real file's
intrinsic pixel dimensions**; the shipped `800`/`800` is a stand-in for the
media box's ratio and stops layout shift only by accident. Copy either shipped
row to add more, and put the modifier on every second one.

Two rules hold the pattern up:

- **The alternation is a modifier, not `:nth-child(even)`.** `:nth-child` reads
  position in the parent, so the day someone drops a heading or an aside
  between two rows every row below it silently inverts. The alternation is a
  property of the row, so it is stated on the row:
  `zigzag-rows-row--mirrored`.
- **Only the media ever moves.** Source order is media then copy in every row —
that is the reading order — and the mirroring shifts the media column only. It
carries nothing focusable, so focus can never jump backwards. Which means
**never wrap a row's image in a link**: in a mirrored row that puts a focus
stop in the half that moves, and focus runs right-then-left across the row. A
row whose image must be a link is not mirrored, and the CSS catches it where
`:has()` is supported — a mirrored row whose media contains a link, a button
or anything tabbable renders unmirrored. Treat that as a safety net and not as
enforcement: a browser without `:has()` drops the rule whole and the row does
flip, so the markup still has to be right. The row's destination belongs in
the copy link, whose words say where it goes.

On phones the rows stack to one column, image first, always — and there is no
`order` property anywhere in the stylesheet to un-set, because source order
already puts the image first. The source this was lifted from had to re-set
`order: 4` / `order: 3` on mobile to undo its own desktop swap; that is the
detail most zigzag implementations get wrong.

**Pairing.** `heading-block` above it for an eyebrow and one line of
introduction. Put it in the body of a long page rather than at the end: the
rows are what earn the join, so something else should carry it afterwards.
Avoid `steps-numbered` on the same page — two image-led runs and the reader
stops telling them apart. Not with `hero-split` either, which is the same
image-beside-copy shape at the top of the page — one of them is doing the
other's job.

**Brand adaptability.** `--card-radius` and `--card-shadow` do most of the
work — square and flat reads editorial, rounded and shadowed reads warm — and
`--font-heading` carries the row headings. The one local dial is
`--zigzag-rows-media-ratio` (default `1 / 1`): `3 / 2` for landscape
photography, `4 / 5` for portrait, set on the section so every row keeps the
same beat, never per row. Body copy runs from `1rem` up and the link is
underlined at full size with a 44px target; both were deliberately fixed on the
way in from a 13px paragraph and a 12px arrow-suffixed link, so do not scale
either back down for a brand that wants a quieter row.

**Behaviour (gated).** The row container carries the `reveal` hook: where the
platform serves the behaviour library the rows fade-and-rise in as they scroll
into view, staggered, and reduced-motion visitors get nothing. Without the
library the attributes are inert and every row renders in full, which is the
same outcome the source reached by a different route: it added its reveal
class from script rather than baking `opacity: 0` into the served markup, and
carried a reduced-motion reset besides. That is progressive enhancement done
properly.
