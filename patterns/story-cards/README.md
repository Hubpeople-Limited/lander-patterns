# story-cards

**What it is and when to use it.** Couples who met through the brand, as big
photo cards: each photograph large, the couple's names under it or across its
foot, and where they are in italics. One large card and two small, or three
the same. On a dating brand this is the proof a visitor looks for first:
people like them who found someone here. Use it on a homepage, a landing page
or an about page when the brand has three couples' stories to show.

**Real couples, shown with their OK.** Each card works best with the couple's
own photograph, the names they are happy to be shown by, where they are, and a
line in their own words where they gave one. Ask them before their story goes
on a public page anyone can reach. The library ships no sample couple and no
drawn stand-in for one (the slot is `placeholder=no`): a made-up couple reads
as a real one to a visitor.

**The twin, `scene-cards`.** A brand with no couples' stories has the same
card for places, events and ideas: `scene-cards`, the same markup, the same
stylesheet and the same rungs, whose picture may be the library's
placeholder. They are two files because the header says what a card carries,
one per pattern (`requires:`, `image-slots:`, `layout:`); `ci/test_gates.py`
(`check_story_cards`) holds the two files' markup, stylesheet and rung words
identical. **A change to one is made to both, in the same commit.** They
avoid each other: one run of big cards per page.

**Three axes.**

| Axis | Rungs |
|---|---|
| `size` | `feature`, the first card large and the next two stacked beside it (the default, drawn for three); `even`, three the same to a row |
| `words` | `below`, the words on the page under the photograph (the default); `over`, across the photograph's foot on a scrim |
| `motion` | `default`, still; `moving`, the cards ease in and a photograph grows a little under the pointer |

On a phone the cards stack whichever `size` is chosen: portrait frames below
`30rem`, landscape ones up to `48rem`, so a stacked card never fills a tablet.

**Words over a photograph.** On `over` the photograph and the caption share one
grid cell, so a long caption grows the card instead of climbing out over the
card above. The caption's top padding is the scrim's fade and nothing more:
every line of the words sits on the full level, `--color-scrim` at the floor
of `--story-cards-scrim-strength`, held by `clamp()` at `0.92`. Every ink
there is `--color-on-scrim`.

**What it needs.** Three couples, each with a photograph at least 1200px wide
in portrait with alt text saying who is in it, the names and the place. Faces
sit in the upper part of the frame (`object-position: 50% 30%`), which every
crop keeps. A section heading, and an eyebrow only when something true fills
it.

**Not on a page with `media-card-grid`:** both are people's photographs set as
cards, and one run of them is the proof; two read as a gallery.

**Pairing.** `steps-plain` before it, so the visitor has seen how joining
works before they see who it worked for; `cta-band` after it.

**Movement** (`motion`). Still by default. On `moving` the cards ease in one
after another through the behaviour library's `reveal`, and a photograph grows
a little inside its frame under the pointer; both sit inside the
reduced-motion guard.

**Brand adaptability.** `--card-radius` rounds the frames, `--font-heading`
carries the names at up to 1.625rem, and the place is set in the body face's
italic. The heading takes `--color-heading` on the page ground, held to a
clamp floor of 1.75rem; the names and the place take `--color-text` and
`--color-text-soft`.
