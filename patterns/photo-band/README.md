# photo-band

**What it is and when to use it.** One photograph, full width, with nothing
on it and nothing beside it: a breath between two sections on a long page.
Every other photographic pattern in this library lays words on or next to the
image, which is the right thing to do with a photograph that is carrying an
argument. This is for a photograph that is carrying a mood. Use it where a
page has two runs of argument in a row and the reader needs a moment between
them; use it on an about page, where a picture of the place or the people says
more than another paragraph would.

Not for the first thing on a page, where an opener belongs, and not for the
last, where the ask belongs. Not for a photograph that needs explaining: a
picture that wants a caption is `article-figure`. Not twice in a row.

**What it needs.** One real photograph at least 1600px wide that is worth
looking at on its own - a place, a crowd, a table, weather. It is cover-cropped
to the band's height, so the subject should sit near the middle and survive
losing its top and bottom on a wide screen. Alt text saying what is in it, or
an empty alt where it is decoration only, which is the honest answer for most
bands: a screen reader then skips it, which is exactly what a sighted reader
does.

**Pairing.** Between two sections of words - after `prose-column`, after
`portrait-prose`, between the rows of `zigzag-rows` and what follows. It sits
on no ground of its own and separates whatever grounds are either side of it,
so a recipe records its band as `plain`. Two in one page is fine on a long
page; two adjacent is a gallery, and there is a pattern for that.

**Brand adaptability.** One axis, and the rest is the photograph.

| Axis | Rungs | What it moves |
|---|---|---|
| `height` | `short`, `standard`, `tall` | a strip (`clamp(10rem, 28vw, 18rem)`); the ordinary band (`clamp(14rem, 40vw, 28rem)`); most of a phone screen (`clamp(18rem, 56vw, 40rem)`). Rem against the viewport width, never viewport height, so the band never competes with the fold rules an opener obeys |

The only token it reads is `--color-surface-soft`, the ground the image
arrives onto so the band is not a white gap while the file loads. Corners are
square: a full-bleed image with rounded corners is a card that forgot its
margins.
