# hero-split

**What it is and when to use it.** The conversion opener for a homepage or
campaign lander: the value proposition on one side, one strong image on the
other, a single join CTA. Use it when the brand has a genuinely good hero image
and one clear offer to state. Do **not** use it with a weak or placeholder
image — a split hero with a filler panel reads as broken; use a text-led
opener instead. One hero per page, always at the top.

**What it needs.** A headline and one-sentence subhead stating the real offer
(message-matched to whatever brought the visitor), and one image at least
1280px wide, served through the CDN sized for the slot with real alt text. The
CTA is always the platform's join placeholder — never a written-out URL.

**Choose between this and `hero-overlay`.** They are alternatives, not
neighbours: every page gets exactly one opener, which is what
`one-per-page: yes` says on both. Pick this one when the offer has to be read
rather than felt, or when the available photography will not survive being
cropped to a full screen. Pick `hero-overlay` when the image carries the
argument on its own.

**Not on a page with `hero-centred`.** Both put the claim beside or above a single image and a page opens once. `hero-centred` is the one to reach for when the photograph is landscape and unpredictable, since it lays no word over it.

**Pairing.** Works ahead of `pricing-tiers` on long
pages. Not on a page with `gallery-scroll` — two large visual moments compete
and neither wins — nor with `zigzag-rows`, which is the same image-beside-copy
shape further down. Not with `article-masthead`: that opens an article and
carries the page's `<h1>`, which this pattern also does.

**Brand adaptability.** `--card-radius` + `--card-shadow` set the image's
character: radius 0 and no shadow reads sharp and editorial, soft radius and
shadow reads warm and friendly. `--font-heading` and the clamp size carry the
voice. On phones the image leads and the copy follows; from 48rem the copy
leads. Variant: swap the grid columns (`0.9fr 1.1fr`) for an image-heavy
brand. The markup ships `width="640" height="720"` as a stand-in ratio —
**set both attributes to the real image's intrinsic dimensions** when filling
the slot, or the page reserves the wrong space and jumps as it loads.
