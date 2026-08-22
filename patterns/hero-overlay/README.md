# hero-overlay

**What it is and when to use it.** One of the library's two hero shapes, and the
cinematic one: a single photograph filling the whole first viewport with the
claim set over it, plus the join and login controls. Use it when the brand has
**one** photograph good enough to be the entire first screen and the job of that
screen is atmosphere — who this is for, what it feels like — rather than
explanation. Reach for `hero-split` instead when the offer needs a stated value
proposition read alongside the image, or when the image is a product shot,
screenshot or anything that must be *looked at* rather than felt: cover-cropping
a screenshot to fill a screen destroys it. Do **not** use it without a real
photograph — a scrim over a flat fill is a dark rectangle — and never put it on
a page that already has a hero. Two openers means two `<h1>`s and two first
impressions, which is why the header declares `avoid-with: hero-split`.

**What it needs.** One landscape photograph, at least 2400px wide, that survives
being cropped hard at both ends of the viewport range. **Serve it through the
CDN as a `srcset` ladder sized for the slot, not one fixed width** — the slot
is full-bleed, so `sizes` is `100vw` and a sensible ladder is 640 / 960 / 1280
/ 1920 / 2560w; a single 2560px file costs a phone most of its LCP budget. It
is the page's largest asset and its LCP element, so it ships
`fetchpriority="high"` and **must never carry `loading="lazy"`**; set `width`
and `height` to the real file's intrinsic pixels (the shipped 1920×1280 is a
stand-in ratio). It needs its own alt text describing the photograph — empty
the value only for a pure texture, never delete the attribute. Then a headline
of one or two lines and one supporting sentence. Both controls are platform
placeholders: join for the new visitor, login for the returning one. Delete
the second anchor for a pure acquisition page; never repoint it at a
written-out URL. Contrast here is **not optional and the tokens do not cover
it**: text on photography is outside the contract. The scrim's strongest stop
must be **at least 92% opaque**, and the CSS enforces that floor —
`--hero-overlay-scrim-strength` may be raised toward `1` for a bright or busy
image, and `clamp()` pulls anything below 0.92 back up. Because the scrim
resolves to `--color-bg`, the ink sits on the page's own background — so
`--color-text` carries the title and the ghost control's edge, and
`--color-text-soft` the subhead — both at the 4.5:1 the contract states,
against a token it states it against. `--color-heading` is used nowhere here:
its only promise is 3:1 against `--color-bg`, and the ground is that colour at
92% over a photograph, which a bright image pushes away from solid rather than
toward it. There is no headroom to spend. Raise the scrim, never dim the
image. A headline past three lines climbs out of the guaranteed
band: shorten it, or raise the strength.

**Choose between this and `hero-split`.** They are alternatives, not
neighbours: every page gets exactly one opener, which is what
`one-per-page: yes` says on both. Pick this one when the photograph is the
argument — atmosphere, who this is for, what it feels like. Pick `hero-split`
when the words are the argument and the image supports them, or when no
photograph strong enough to fill a whole screen exists.

**Not on a page with `hero-centred`.** Three heroes now exist and a page takes one. Choose this where the photograph is strong enough to carry a whole screen and be read through; `hero-centred` where it is not, or where you do not control it.

**Pairing.** `stats-band` directly beneath it, which is what the dissolve is
for — the hero resolves into the page background and the numbers begin with no
seam. Avoid `gallery-scroll` for the same reason `hero-split` does: a second
large image set anywhere on the page fights the one that is meant to
own the screen.
And avoid `hero-split` outright — a page gets one hero. Not on a page with
`article-masthead` either: that opens an article and carries the page's `<h1>`,
which this pattern also does.

**Brand adaptability.** `--color-bg` does most of the work, because it is both
the scrim and the page: a dark brand gets the moody cinema look the treatment
was drawn from, a light brand gets an airy one, and neither needs a different
stylesheet. `--btn-radius` sets the pair of controls (pill reads consumer,
square reads editorial) and `--font-heading` carries the claim at up to 4rem, so
a display face shows here more than anywhere. Phones get their own treatment,
not a squeeze of this one: the vignette is replaced by a top-down wash and the
copy moves to the top, clear of the browser chrome that eats the bottom of a
small viewport. Variant: drop the login control and centre the copy
(`margin-inline: auto; text-align: center`) for a single-message campaign page.
