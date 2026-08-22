# cta-image

**What it is and when to use it.** A full-bleed photographic closing call to
action: one landscape image filling a band, a scrim carrying the contrast, and a
centred claim with both platform controls over it. Use it where the photograph
is doing the asking — a page whose argument has been visual throughout, or one
where the last thing a reader should see is a person rather than a sentence.

The library's other photographic full-bleed section is `hero-overlay`, which is
`one-per-page` and explicitly the opener. There was no closing equivalent, so a
page wanting to end on an image had nothing. Two designers built one
independently, and a third built the flat-colour version, `cta-band`.

Choose between the three by what is doing the work. `cta-band` when the words
are; this when the picture is; `cta-curtain` only when the uncovering itself is
the point.

Do **not** use it without a photograph strong enough to fill a band at that
size. A weak image under a heavy scrim is a grey rectangle with a headline on
it, which is `cta-band` with extra bytes and a slower page.

**What it needs.** One landscape photograph at least 2000px wide with its own
alt text and a CDN srcset ladder; a closing headline; one supporting line. The
image is decoration under a scrim, but it is the section's whole atmosphere, so
it takes real alt text — empty the value only for a pure texture, and never
delete the attribute.

`loading="lazy"` is correct here and is the opposite of what `hero-overlay`
does. That pattern's image is the page's LCP element and must never be deferred;
this one sits at the foot of a long page, where deferring it is the right call.

The controls are `{{join.url}}` and `{{login.url}}` with their own text tokens.
Delete the second anchor for a pure acquisition page; never repoint it at a hash
or a hand-typed URL.

**Pairing.** After `pricing-tiers` or `faq-details`, where the reader has the
facts and this is the ask. `avoid-with` names `cta-band` and `cta-curtain`: all
three close a page and only one may.

It does **not** avoid `hero-overlay`, and that is deliberate rather than an
oversight. Opening on a photograph and closing on one is a normal editorial arc,
not a conflict — the two sit at opposite ends of the page and never compete for
the same slot. Give them different crops and different subjects, or the page
reads as though it has looped.

**Brand adaptability.** Every ink is `--color-on-scrim` on a `--color-scrim`
ground, one of the three pairs carrying a stated ratio. The title takes it too:
`--color-heading` is barred over a photograph however heavy the scrim, because
that token tops out at the 3:1 large-text bar against `--color-bg` and has no
headroom left for an image to eat.

`--cta-image-scrim-strength` is the one dial, and `clamp()` holds it at a floor
of `0.92` however it is set — the same floor `steps-numbered` enforces, for the
same reason. A brand may make the scrim heavier and cannot make it lighter.

**The section paints `--color-scrim` as a solid ground beneath the image**,
which is worth knowing before anyone removes it. It is not decoration: an image
that fails to load, is slow, or is later deleted from the CDN leaves the copy on
the exact colour its contrast was measured against, rather than on whatever the
page ground happens to be. Two of the designer pages this came from carried the
same guard, arrived at independently.

**The focus indicator is two bands rather than one ring.** What sits behind a
control here is a photograph, which no token describes and no ratio covers, so
the indicator brings its own ground: an `--color-on-scrim` ring backed by a
`--color-scrim` halo. That pair measures **18.34** at worst across the three
sample token sets, so the indicator is visible whatever the image does. It is
the same technique `media-card-grid` already uses inside its cards. Re-derive
from `preview/tokens-*.css` before changing it.

`--btn-radius` shapes both controls. The band is
`clamp(28rem, 60vh, 40rem)` tall, so it fills a phone screen without taking a
whole desktop one.
