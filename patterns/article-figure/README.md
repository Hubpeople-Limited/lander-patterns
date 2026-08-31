# article-figure

**What it is and when to use it.** One picture inside the flow of a piece of
writing, with its caption and its credit. A real `<figure>` and a real
`<figcaption>`, sitting between two runs of body copy.

Use it whenever an article refers to something a reader would be better off
seeing: a screen, a place, a document, a person the piece is about. Several
may appear in one article.

Nothing else in the library does this. `photo-cards` and `gallery-scroll` are
card runs — sets of images treated as peers — and where an opener carries a
picture at all, that picture opens the page rather than illustrating a
paragraph in it. This is the plain captioned figure an article needs, and it
is the only pattern here where the words under the image are the point.

It carries no heading, so it fits at any depth in a page without touching the
heading order.

**A decorative picture does not get this pattern.** A figure with a caption is
by definition carrying information: the caption says what the reader is
looking at. An image that is there to break up the page belongs in a pattern
whose job is the page's rhythm, and its `alt` belongs empty. Here `alt` is a
slot, it is filled, and it describes the picture rather than repeating the
caption — a reader who cannot see the image gets both, one after the other, so
two copies of the same sentence is a worse result than one.

**What it needs.** Four real things, and the absence of any one of them is a
reason not to place it:

1. **A photograph that shows what the writing refers to.** Sized for the slot
   through the CDN, not a full-resolution original.
2. **`alt` text describing what is in the picture**, written for somebody who
   cannot see it.
3. **A caption** saying what this is and why it is here. One or two lines.
4. **The credit** the picture is licensed under — the photographer, the
   library, or the brand's own name where it genuinely owns the image.

**The credit is part of the caption, not a second element.** It sits inside
the `figcaption`, after the caption sentence, set in italic. Moved outside,
it becomes a line of text belonging to nothing: the association between a
picture and the person owed for it is exactly what the `figure` element
carries, and putting the credit outside throws that away while still looking
correct on screen.

**Pairing.** Between two `prose-column` blocks, as a sibling of the column
rather than a child of it. `prose-column` styles its own descendants, and its
`figure` rule is built for the wide tables it holds, so a figure dropped
inside would take those rules instead of these.

No `avoid-with` entry. It paints no ground and makes no ask.

**Brand adaptability.** Very little of this is the brand's to move, which is
deliberate — a caption is furniture, not voice. `--card-radius` rounds the
image, so the picture picks up the corner language the brand uses everywhere
else, and `--color-text-soft` sets the caption, which is contracted against
every page ground the figure can land on. There is no ground, no border and no
shadow: the picture is the block.

**The figure breaks out of the prose measure to 52rem, which is the width
`article-masthead`, `article-toc` and `author-note` already hold to.** A
captioned image inside a text column is small enough that a reader has to lean
in, and the break-out is the standard editorial answer — but a page has room
for two left edges, not three. At 52rem the figure lands on the same edge as
the masthead above it and the author block below, and the only other edge on
the page is the column's. It could not have matched the column in any case:
`prose-column` holds its body to `68ch`, a character count and therefore a
different width on every typeface, while a figure has to be sized in `rem` — a
`ch` measure on display type is the defect `ci/check_measures.py` exists to
fail. A width that nearly matches something else on the page reads as a
mistake; one that matches it exactly, or is plainly wider, reads as a choice.

The caption is held to `60ch` inside that wider box, so the picture gets the
extra width and the reading does not.
