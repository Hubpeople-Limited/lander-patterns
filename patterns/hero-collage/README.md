# hero-collage

**What it is and when to use it.** A homepage, landing or about opener that
shows several of the brand's people at once: the headline, one line and the
join button beside a small collage of two or three photographs, or under a
row of them set as framed prints. The words never sit on a photograph, so no
scrim has to carry them. Use it where the brand has a few good pictures of its
people or its places and no one of them should stand for all; `hero-portrait`
is the choice for one face, `hero-split` for one scene.

**Two arrangements** (`arrange`), and a side for the first:

| Rung | Wide screen | Phone |
|---|---|---|
| `stack` | a staggered cluster beside the words, the first and largest photograph at the back, the other two in front of its foot; `side` puts it on the `end` (the default) or the `start` | two pictures overlapping in a short strip, then the words |
| `prints` | a row of framed prints above centred words, the first in the middle and in front, each turned a few degrees | two prints, then the words |

`side` does nothing on `prints`, which always sit above the words. On a phone
the third photograph waits for a wider screen.

**What it needs.** Two or three real photographs of the brand's own people or
places, each with alt text saying what is in it: the first at least 1200px
wide in portrait, the second at least 800px in portrait, the third at least
800px square. Delete the whole element of a photograph the brand does not
have and the rest close up: with one, it fills the cluster; with two, the
pair keeps the first two places. A headline and one sentence in the brand's
own words. The first photograph is the page's largest paint: it ships
`fetchpriority="high"` and never takes `loading="lazy"`; the third is lazy,
since a phone does not show it. Set every `width` and `height` to the file's
own pixels.

**Photographs work best when they are the brand's own.** Real pictures of
its members at its events, or of its places, with the people's OK, read as a
community; three stock pictures read as an advert. Until they arrive each
slot takes the library's placeholder, a line drawing marked "Photo to come",
drawn whole on the tint and never under another picture's front, so the page
shows what it is waiting for. Three drawings are a stand-in, not a collage:
the build lists each one as a photograph to send.

**The join button only.** This opener carries no sign-up card; for a page
that starts the sign-up itself, `hero-portrait`, `hero-split` and
`hero-bento` hold one.

**Not on a page with another opener** (`hero-band`, `hero-bento`,
`hero-centred`, `hero-overlay`, `hero-portrait`, `hero-split`,
`hero-squeeze`, `hero-stated`, `signup-steps`): each opens the page and
carries its `h1`; a page opens once. Not on a page with `gallery-scroll`
either: a second run of photographs reads as the opener said twice.

**Pairing.** `steps-plain` below it on a homepage, then `faq-details` and
`cta-band`; on an about page `prose-column` for the brand's own account and
`claim-stack` for what it stands for. Take a different ground from the section
under it.

**Movement** (`motion`). Still by default. On `moving` the smaller
photographs ease in one after another through the behaviour library's
`reveal`, once, in under a second. The first never does: it is the page's
largest paint, so it is there from the first frame on both rungs. No tilt or
lift moves under the pointer. A visitor who asked for less motion sees the
still rung.

**Brand adaptability.** Four grounds from the ladder (`plain`, `soft`,
`brand`, `deep`), each naming its own ink, as in `hero-portrait`; on `plain`
the title is `--color-heading`. `--card-radius` rounds the stacked
photographs, and each front one is ringed in the ground's own colour so it
reads as laid on top. The prints are framed in `--color-surface` with
`--card-border` and `--card-shadow`, the same on every ground. `--font-heading`
carries the title at up to 3.5rem, its leading floored at 1.45 cap heights.
Heights come from the width, never the viewport height.
