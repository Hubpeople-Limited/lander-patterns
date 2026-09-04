# portrait-prose

**What it is and when to use it.** One person and their story: a portrait
given a column of its own, with a caption that names them and says what they
are, beside a heading and a few paragraphs of prose. It is the founder
section - the page every small brand has and the one that is most often built
badly, as a grid of values or a wall of text with a tiny round photo in the
corner. Here the photograph gets room, because the reader is being asked to
trust a person, and the prose gets a measure, because it is a story and not a
list.

Use it on an about page, on a homepage whose brand is one person's, and in an
article that is an interview or a profile. Not for a team: one person, one
portrait. Not for a testimonial - that is somebody else's words about the
brand, and `quote-feature` is for those. Not for a person who has not agreed
to be here: `requires: consented-people` is the strong reading on purpose,
because a portrait on a public page is marketing whether or not it was meant
as one.

**What it needs.** One real portrait of a real person who has agreed to
appear on a public page anyone can reach, at least 800px wide and taller than
it is wide - a landscape photograph is cropped to a portrait by the column and
loses whatever was at its sides. Their name and one line of standing for the
caption ("Founder", "Founder, and a member since 2019"). A heading in the
brand's voice. Two to four paragraphs of real prose about that person and why
the brand exists, written by or with them. Nothing here is invented: a story
written from nothing is the thing a reader can smell.

**Pairing.** After a stated opener on an about page, and before `claim-stack`,
which sets the promises the story earns. `photo-band` after it gives the story
somewhere to land. `cta-band` closes the page. It sits on the page ground and
has no ground axis, so a recipe records its band as `plain`; put a `soft`
band on either side of it.

**Brand adaptability.** One axis.

| Axis | Rungs | What it moves |
|---|---|---|
| `side` | `start`, `end` | which side the portrait takes from `48rem` up; below that it comes first either way, because on a phone the face is what stops the thumb |

The columns are 2:3, so the portrait is generous without being the section.
The heading takes `--font-heading`, `--weight-display` and the two heading
dials; the caption's name line is bold `--color-text` and the standing line
`--color-text-soft`, so the eye reads name, then role. The portrait takes
`--card-radius` and `--card-shadow`, so a brand with square cards has a square
portrait. The measure on the prose is `62ch`, a body measure and not a
display one.
