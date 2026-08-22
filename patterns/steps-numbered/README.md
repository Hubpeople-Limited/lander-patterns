# steps-numbered

**What it is and when to use it.** A "how it works" run of full-bleed image
cards, each a photograph at a fixed portrait ratio with a dark bottom-up scrim
carrying a giant numeral and two lines of copy. Use it when the thing being
explained genuinely happens **in order** and each step has a real photograph
behind it. Three or four steps is the useful range: two is a list, five stops
being a sequence anyone remembers. Do **not** use it for unordered features or
benefits — that is a peer set and the numbering would be a lie — and do not use
it without photography, because a scrim over a flat fill is just a dark box.

**What it needs.** One real photograph per step, portrait-ish and at least
1020px wide (the cards render at 510×590 CSS pixels, so 2× for retina), each
with its own alt text describing that photograph — the alt slot is per step,
not shared. Plus a short step title and one sentence of body copy per step, in
the order they actually happen. **Set `width` and `height` on each `<img>` to
the real image's intrinsic pixel dimensions**; the shipped `510`/`590` is a
stand-in for the card's ratio and stops layout shift only by accident.
Duplicate the single `<li>` per step. Never type a number: the numeral is a CSS
counter on the `<ol>`, so the sequence is real to assistive tech and to the
markup, and reordering or removing a step renumbers the set with no edit.
It also needs a **guaranteed contrast floor, which is non-negotiable**: no
token describes what a photograph does under text. The scrim's bottom stop must
be **at least 92% opaque**, so the ink lands on effectively solid
`--color-scrim` whatever the photo does. The CSS enforces that floor:
`--steps-numbered-scrim-strength` may be raised toward `1` for busy or light
images, and `clamp()` pulls any value below 0.92 back up. Ink is
`--color-on-scrim` on a `--color-scrim` ground, which the contract states at
4.5:1, so a dark brand inverts cleanly instead of going white-on-white. It
grounds on `--color-scrim` rather than `--color-heading` for a reason worth
carrying to any pattern doing the same job: `--color-heading` carries no stated
ratio, and on a brand whose heading is a display colour sitting at the 3:1
large-text bar, this card's 14-16px body has no guarantee to stand on.

**Not on a page with `steps-plain`.** That pattern answers the same "how it works" question without photography, and a page carrying both asks a reader to follow two sequences that are really one. Choose by whether the brand has a real photograph for every step: if it does, this one; if it does not, `steps-plain`.

**Pairing.** `heading-block` above it when the section needs an eyebrow and an
intro line. Put it late: the step that follows "here is how it works" is
joining, so whatever carries the join should be the next thing a reader meets.
Not on a page with `gallery-scroll`, `media-card-grid`, `portrait-wall` or
`zigzag-rows`: all are image-led runs, and a reader who meets two stops telling
them
apart. This is the pattern to drop if the page needs one of the others.

**Brand adaptability.** `--card-radius` and `--card-shadow` set nearly all the
feel: 28px-and-shadowed reads editorial, square-and-flat reads utilitarian.
`--font-heading` carries the numeral as well as the titles, so a display face
shows up here more than anywhere else. The cards wrap to one column on phones,
where the numeral steps down and sits above the title rather than beside it.

**Behaviour (gated).** The `<ol>` carries the `reveal` hook: where the platform
serves the behaviour library the cards fade-and-rise in as they scroll into
view, staggered, and reduced-motion visitors get nothing. Without the library
the attributes are inert and the section renders in full — the source this came
from had `opacity: 0` baked in as the default and was invisible without
JavaScript. Never do that.
