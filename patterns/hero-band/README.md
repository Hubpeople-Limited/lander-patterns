# hero-band

**What it is and when to use it.** The opener for an inner page: about,
features, pricing, safety, a location page and the two listing pages. The
page's title and one line, with a photograph beside them or behind them,
one band tall rather than a screen, so what the visitor came to the page for
starts on the first screen. Use it where an inner page would otherwise open
on words alone and the brand has a photograph of people or a place it can
show. `hero-stated` stays the opener for a page with no photograph worth the
space. Not for a homepage or a campaign page, which open on a full photo
opener, and not for an article, which opens on `article-masthead`.

**Three places for the photograph** (`photo`):

| Rung | Wide screen | Phone |
|---|---|---|
| `end` | words left, photograph right (the default) | photograph first |
| `start` | photograph left, words right | photograph first |
| `behind` | the photograph fills the band; the words sit on a panel of the ground in front of it | photograph edge to edge, the panel over its foot |

The words never sit on the photograph itself. Behind, they sit on a panel
painted in the ground's own colour, so every ink is one of the contract's
stated pairs and no scrim has to carry a contrast ratio. The panel takes at
most 36rem or 62% of the container, so the photograph keeps a real share
of the band on a tablet too. A "Photo to come" placeholder is a marked
drawing rather than a photograph: behind, on a wide screen, it is drawn
whole in the space beside the panel instead of cropped under it. That rule
repeats the panel's track in its own `calc()`; change the two together.

**What it needs.** One real photograph at least 1600px wide of people or a
place the brand can show, with alt text saying what is in it; a headline for
this page and one sentence that says something the headline does not. The
eyebrow is deleted rather than padded. The photograph is cover-cropped to a
band, so its subject should sit near the middle; on `behind`, keep it away
from the left, where the panel sits. It is the page's largest image and
usually its LCP element: it ships `fetchpriority="high"` and never takes
`loading="lazy"`; set `width` and `height` to the file's own pixels. Before
the brand has a photograph the slot takes the library's placeholder, a line
drawing, never a picture of a person the page names.

**Not on a page with `hero-stated`.** Both open an inner page and carry its
`h1`; a page opens once. Pick this one when there is a photograph worth the
band, that one when there is not.

**Pairing.** Above whatever the page is for: `prose-column` on about and
location pages, `listing-rows` on the listings, `pricing-tiers`,
`safety-protections`. Not directly above `photo-band`: two photographs in a
row is a gallery. Take a different ground from the section under it.

**Movement** (`motion`). Still by default. On `moving` the photograph
settles from a slight zoom over five seconds as the page opens, once, then
holds still. It is the page's largest paint, so it shows from the first
frame and only its size moves; the frame clips it, so the page never widens.
Inside the reduced-motion guard, and CSS only: no behaviour library needed.

**Brand adaptability.** Four grounds from the ladder (`plain`, `soft`,
`brand`, `deep`). Each names its own ink and every rule reads that pair, as
in `hero-stated`, so nothing in the file knows which ground it is on. On
`plain` the title is `--color-heading`, held to a clamp floor of 1.75rem;
elsewhere it takes the ground's own ink. `--card-radius` rounds the
photograph and the panel; `--font-heading` carries the title at up to
3.25rem, smaller than a homepage opener on purpose. Heights are set from the
width, never the viewport height, so none of the fold rules an opener obeys
apply: `clamp(11rem, 48vw, 16rem)` on a phone, `clamp(16rem, 30vw, 24rem)`
beside the words, and behind, a band at least `clamp(18rem, 30vw, 24rem)`
tall.
