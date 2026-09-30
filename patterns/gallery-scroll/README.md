# gallery-scroll

**What it is and when to use it.** The carousel this platform can actually
have: a horizontal strip of images the visitor scrolls or swipes, with
scroll-snap making each stop land cleanly. Nothing auto-advances — auto-play
needs a pause control, a pause control needs JavaScript, and the evidence is
against auto-advancing carousels anyway. Use it for a genuine peer set of
images: venue shots, app screens, real event photos. Member photos
presented as endorsements sit better in a testimonial pattern, where a name
and the person's OK go with the picture; a single image has patterns of its
own; and anything the visitor must see reads better in the page flow than
off-screen.

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

**The rail shows no scroll bar**, which on a desktop reads as a broken page rather
than a gallery. The list scrolls inside the block, so **with the library,
`carousel` builds two round arrows** that hold still: **Arrows** `top`, above the
photographs at the right (under them on a phone), or `edges`, over their sides on
a solid circle with a soft shadow; **Arrows on a phone** `arrows`, or `swipe` to
leave them off there. Each arrow moves the rail by one photograph and dims at an
end, and none show while every photograph fits. Without the library the rail
still swipes and takes the keyboard. With scripting off nothing can build the
arrows and a mouse would have no way along it, so the photographs wrap into
centred rows instead.
