# hero-squeeze

**What it is and when to use it.** The whole page in one viewport: a
photograph, one claim, one control, the reassurance under it, and one piece of
proof. **Nothing goes below the fold, because nothing goes after it.**

Build it when paid traffic lands straight on the page and the only question is
whether they sign up. It is the highest-volume shape in acquisition and it is
the one shape where every extra section costs money.

The other heroes are **openers for pages that continue**; this one is the page,
which is why it is a separate pattern rather than a modifier. Do **not** put a
second section after it — that is how a squeeze quietly becomes a short landing
page, and `hero-overlay` is the opener for one of those.

**What it needs.** One landscape photograph at least 1600px wide with real alt
text; a headline of one line; one supporting sentence; a reassurance line; and
one piece of real proof.

**Everything needed to decide is in those five things**, because there is
nowhere else. If the argument does not fit, this brand needs a landing page.

**The two slots are slots on purpose.** Drop `cta-assurance` into `assurance`
and `member-strip` or `rating-mark` into `proof` — the proof a brand has
differs, and hard-coding one would gate the pattern on material half the
brands do not hold.

**With no proof to put there, delete the proof block rather than filling
it.** A squeeze with a real claim and no proof still converts; one with
invented proof puts a fabricated claim on the highest-traffic page the brand
runs.

**Pairing.** `cta-assurance`, `member-strip` and `rating-mark` go inside it; nothing goes after it.

It refuses every other opener — `hero-overlay`, `hero-split`, `hero-centred`,
`hero-stated`, `article-masthead`. A page opens once, and two of them means two
first impressions and two claims on the `h1`.

**Brand adaptability.** Every ink is `--color-on-scrim` on a `--color-scrim`
ground, one of the pairs the contract states. The headline takes it too:
`--color-heading` is barred over a photograph however heavy the scrim.

The control is `--color-primary` with `--color-on-primary`, at 52px rather
than the usual 48: it is the only control on the page. Its focus indicator is
two bands, an `--color-on-scrim` ring backed by a `--color-scrim` halo, because
a photograph sits behind it and no token describes a photograph. Same technique
as `media-card-grid`.

`--hero-squeeze-scrim-strength` is the one dial, held by `clamp()` at a floor of
`0.86`. That floor is lower than `cta-image`'s `0.92` deliberately: the copy
here sits in the middle of the frame rather than against an edge, and the
gradient reaches full strength behind it by 12% down.

**The ramp starts at 68%, and that number is load-bearing.** Content is
centred, so on a tall content box - 200% zoom, a long headline, a landscape
phone - the headline sits in the *top* of the ramp. The first stop has to
clear 4.5:1 on its own rather than lean on the block padding. It does on all
four sample sets, but the closest measures 4.51:1. Darkening an on-scrim ink
or lightening a scrim breaks that, so re-derive from `preview/tokens-*.css`
before touching either.

**It is `min-height: 100svh`, not `height`, and that decides how it fails.**
The section aims to fill exactly one viewport. Where the content is taller than
the viewport — a long headline, a short window, 200% browser zoom, a phone in
landscape — **it scrolls rather than clipping.** A squeeze that hides its own
call to action to keep a promise about scrolling has broken the only thing it
was for; a fixed height with `overflow: hidden` is how a page in this library's
own source material became unscrollable at 200% zoom, failing WCAG 1.4.4.
`svh` not `vh` for the same family of reason: `100vh` is the largest viewport,
so the control would sit behind the address bar.

**A viewport minus the furniture at BOTH ends.** A header sits above this
section and a footer below it, and the platform injects the footer at serve
time, so no markup here can enclose it: the height is `calc(100svh -
var(--page-header-height, 9.5rem) - var(--page-footer-height, 12.5rem))`.
Subtracting only the header leaves the page scrolling by the footer — 177px on
a 1280×800 laptop, 166 of them the footer. Take both numbers off the rendered
page, never off `--logo-height`, which came up 11px short of the header that
rendered; TOKENS.md's *The page's furniture* says how. `--hero-squeeze-above`
no longer does anything, and `0px` is the value for an end with nothing at it.
