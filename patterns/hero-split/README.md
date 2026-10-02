# hero-split

**What it is and when to use it.** The conversion opener for a homepage or
campaign lander: the value proposition on one side, one strong image on the
other, a single join CTA. Use it when the brand has a genuinely good hero image
and one clear offer to state. It works best with a strong
image: a split hero with a weak one reads as a filler panel, and a text-led
opener can serve better until a good photograph arrives. A placeholder holds
the place meanwhile. One hero per page, always at the top.

**What it needs.** A headline and one-sentence subhead stating the real offer
(message-matched to whatever brought the visitor), and one image at least
1280px wide with real alt text. **Serve it through the CDN as a `srcset`
ladder, not one fixed width** — 640 / 960 / 1280w covers it. `sizes` ships
matching the column the photograph takes: the full width on a phone, about
half from 48rem, and at most 36rem once the container stops growing; change
it only if the brand's `--container-max` is far wider than 72rem. It is the
page's LCP element, so it ships `fetchpriority="high"` and never
`loading="lazy"`. The CTA is always the platform's join placeholder — never a
written-out URL.

**Choose between this and `hero-overlay`.** They are alternatives, not
neighbours: every page gets exactly one opener, which is what
`one-per-page: yes` says on both. Pick this one when the offer has to be read
rather than felt, or when the available photography will not survive being
cropped to a full screen. Pick `hero-overlay` when the image carries the
argument on its own.

**Not on a page with `hero-centred`.** Both put the claim beside or above a single image and a page opens once. `hero-centred` is the one to reach for when the photograph is landscape and unpredictable, since it lays no word over it.

**Not on a page with `hero-squeeze`.** That one is not an opener, it is the whole page: everything the visitor needs sits in one viewport and nothing follows it. A page opens once.

**Not on a page with `hero-stated`.** Reach for that one when there is no photograph worth the space, or none at all.

**Not on a page with `signup-steps`.** That one opens the page on its own sign-up card; a page opens once.

**Not on a page with `hero-portrait`.** That one sets the claim beside one large portrait; a page opens once.

**Not on a page with `hero-bento`.** That one opens on the words among tiles; a page opens once.

**Not on a page with `hero-collage`.** That one sets the claim beside a cluster of photographs; a page opens once.

**Pairing.** Works ahead of `pricing-tiers` on long pages. Not on a page with
`gallery-scroll` — two large visual moments compete and neither wins — nor with
`zigzag-rows`, which is the same image-beside-copy shape further down. Not with
`article-masthead`: that opens an article and carries the page's `<h1>`, which
this pattern also does. `signup-card` can take the button's place: wide, the
photograph fills its half and the card overlaps its inner edge; on a phone the
photograph follows the card. Over the library's placeholder the card sits under
the words instead, so the drawing and its mark stay whole beside it.

**Brand adaptability.** `--card-radius` + `--card-shadow` set the image's
character: radius 0 and no shadow reads sharp and editorial, soft radius and
shadow reads warm and friendly. `--font-heading` and the clamp size carry the
voice. **`side` sets which side the photograph takes from 48rem up**:
`hero-split--end` (the default, copy first) or `hero-split--start`
(photograph first; the column widths swap with it). Choose `start` when the
subject faces into the page from the left, or to alternate with a photograph
further down. On phones the image leads whichever side is chosen; with
`signup-card` in place of the button the card leads instead, and wide, the
card overlaps the photograph's inner edge on either side. The markup ships
`width="640" height="720"` as a stand-in ratio —
**set both attributes to the real image's intrinsic dimensions** when filling
the slot, or the page reserves the wrong space and jumps as it loads.
