# gallery-scroll

**What it is and when to use it.** The carousel this platform can actually
have: a horizontal strip of images the visitor scrolls or swipes, with
scroll-snap making each stop land cleanly. Nothing auto-advances — auto-play
needs a pause control, a pause control needs JavaScript, and the evidence is
against auto-advancing carousels anyway. Use it for a genuine peer set of
images: venue shots, app screens, real event photos. Do **not** use it for
member photos presented as endorsements (that is testimonial territory with
its own rules), for a single image, or as a way to hide content that matters —
anything the visitor must see belongs in the page flow, not off-screen.

**What it needs.** Three or more real images of the same kind, each with real
alt text, each sized for the slot through the CDN (roughly 480px wide at 2×).
A short caption per image if the material supports one; delete the caption
element otherwise. Duplicate the item element once per image.

**Not on a page with `photo-cards`.** Two runs of photographs competing for the same attention, one of which scrolls sideways, is a page asking a reader to browse twice.

**Pairing.** Fine mid-page on a homepage or article. Keep it away from
`hero-split` and `hero-overlay` — two large visual moments on one page compete
and neither wins — and off any page carrying `steps-numbered`,
`media-card-grid` or `portrait-wall`, all of which are already runs of images.
This is the most image-hungry pattern in the library and it wants the page to
itself.

**Brand adaptability.** `--card-radius` and `--card-shadow` restyle every
tile. Item width (`min(70vw, 22rem)`) shows a deliberate sliver of the next
image on phones, which is what invites the swipe — tune it per brand if the
images are portrait. Smooth scrolling engages only for visitors who have not
asked for reduced motion. The items ship `width="480" height="360"` as a
stand-in ratio — **set both attributes to each real image's intrinsic
dimensions** when filling the slots.

**With the library, `carousel` builds a previous and a next control** inside the
scroller, sticky to its start edge so they stay in view; each moves the rail by one
item and disables at the ends. Without it the rail is the rail: swipe, scroll or
keyboard, exactly as authored.
