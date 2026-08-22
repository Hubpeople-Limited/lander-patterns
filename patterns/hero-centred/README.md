# hero-centred

**What it is and when to use it.** An opener with the claim centred at the top —
headline, one supporting sentence, one join control — above a wide cropped
photograph sitting in its own rounded band. The copy and the picture never
overlap.

That is the whole reason it exists. **It is the only hero in the library that
lays no word over an image**, so no scrim has to carry a contrast ratio and
nothing depends on what a particular photograph happens to look like. Reach for
it when you do not control the imagery, when a partner will swap the file later,
or when the available photograph is good but busy — the three cases where
`hero-overlay` quietly degrades and nobody notices until the brand ships.

**Three heroes now exist and a page takes exactly one.** They all refuse each
other. Choose like this:

- `hero-overlay` — the photograph is strong enough to fill a whole screen and be
  read through, and you control it.
- `hero-split` — the argument needs to sit beside the picture rather than above
  it, and the picture is portrait or square.
- `hero-centred` — the photograph is landscape, or unpredictable, or the claim
  is the thing that has to land first.

Do **not** use it as a section opener further down a page. It carries the page's
only `h1`; `opener-split` and `heading-block` are the section openers.

**What it needs.** A headline of one or two lines and one supporting sentence,
both from real brand material. One landscape photograph at least 1600px wide
with its own alt text and a CDN srcset ladder.

The alt text is a real, filled slot rather than an optional one. Nothing in the
copy says what the photograph shows, and the picture is the page's whole first
impression — empty the value only for a pure texture or gradient, and never
delete the attribute.

**Not on a page with `hero-squeeze`.** Both put the claim first, but that one is the entire page rather than its opening - nothing follows it, so everything has to fit one screen.

**Pairing.** `picker-chips` directly under it, which turns the claim into the
first decision. `stats-band` under that. `steps-plain` where the page then has
to explain itself. `avoid-with` names the other two heroes and
`article-masthead`, which is an article's own opener and would give the page two.

**Brand adaptability.** The headline is the one use of `--color-heading`, with
both halves of that token's contract met deliberately: the section paints no
ground, so it sits on `--color-bg`, and the `clamp()` floor is 34px, well above
the 24px the token is promised at. The supporting sentence is
`--color-text-soft`, contracted against the surface it sits on. The control is
`--color-primary` with `--color-on-primary`, and its focus ring is
`--color-focus` — which is correct here precisely because the ring lands on the
page ground rather than on the brand colour, where that token is contracted.

`--card-radius` shapes the image band and `--btn-radius` the control. The band
paints `--color-surface-soft` behind the image, so a slow or failed file leaves
a band-shaped space rather than a collapsed one.

**The image ratio changes at the breakpoint, and that is the detail worth
keeping.** `--hero-centred-ratio` is `4 / 5` on phones and `16 / 7` from `48rem`
up. A landscape crop shown at a letterbox ratio on a narrow screen is a sliver
about eighty pixels tall — technically present, visually nothing. Turning the
band portrait on phones keeps the photograph doing work on the screen most of
this traffic arrives on. A brand with square or portrait source imagery should
set the wide value rather than crop every file.

Two more dials: `--hero-centred-title-measure` (default `15ch`) is what makes
the headline wrap early and read as display type instead of running the width of
the page, and `--hero-centred-sub-measure` (default `50ch`) holds the supporting
sentence to a readable width.

**It is still the LCP element.** The image sits below the copy, which makes it
tempting to defer — do not. It is the largest thing on the first screen on most
viewports, so it ships `fetchpriority="high"`, no `loading` attribute, and
`width`/`height` carrying the real file's intrinsic pixel size so the box is
reserved before a byte arrives.
