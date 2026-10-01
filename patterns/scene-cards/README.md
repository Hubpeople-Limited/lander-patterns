# scene-cards

**What it is and when to use it.** Places, events and ideas as big photo
cards: each photograph large, its name under it or across its foot, and where
or when in italics. One large card and two small, or three the same. It is
the card `story-cards` uses for couples, for a brand with no couples' stories
to show: a place members meet, an event the brand runs, an idea for a first
date. Use it on a homepage, a landing page, an about page or a location page
when the brand has three such things worth a photograph.

**What reads best.** Something real the brand is about, from its own
material, with the brand's own photograph of it. A card about a place or an
event keeps the attention on the brand; a couple's story reads best in
`story-cards`, shown with their OK. Before the brand has a photograph a card
takes the library's placeholder, a drawing of a place, with its "Photo to
come" mark.

**The twin, `story-cards`.** The same markup, the same stylesheet and the same
rungs; only the header differs, because it says what a card carries.
`ci/test_gates.py` (`check_story_cards`) holds the two files identical. **A
change to one is made to both, in the same commit.** They avoid each other:
one run of big cards per page.

**Three axes.**

| Axis | Rungs |
|---|---|
| `size` | `feature`, the first card large and the next two stacked beside it (the default, drawn for three); `even`, three the same to a row |
| `words` | `below`, the words on the page under the photograph (the default); `over`, across the photograph's foot on a scrim |
| `motion` | `default`, still; `moving`, the cards ease in and a photograph grows a little under the pointer |

**Words over a photograph.** As in `story-cards`: the caption shares the
photograph's cell, its top padding is the fade, and every line sits on
`--color-scrim` at the floor of `--scene-cards-scrim-strength`, held at `0.92`.
**Over the library's placeholder the floor drops to `0.4`** and the tint
behind the drawing is the brand colour mixed into `--color-scrim`;
`ci/check_placeholder_scrim.py` requires the drawing to show and the words to
hold 4.5:1. The placeholder is drawn whole (`object-fit: contain`) on its
tint, never cropped by the card's frame.

**What it needs.** Three things, each with a photograph at least 1200px wide in
portrait with alt text, or the placeholder; a name; where or when. A line only
when something true fills it. A section heading.

**Not on a page with `photo-cards`:** both are a run of photograph cards, and
a page carrying both shows the section twice.

**Pairing.** After the opener or `steps-plain`; `cta-band` after it. On a
location page, under the place's own words.

**Movement** (`motion`). Still by default. On `moving` the cards ease in one
after another through the behaviour library's `reveal`, and a photograph grows
a little inside its frame under the pointer; both sit inside the
reduced-motion guard.

**Brand adaptability.** As `story-cards`: `--card-radius` rounds the frames,
`--font-heading` carries the names, the heading takes `--color-heading` on the
page ground with a clamp floor of 1.75rem.
