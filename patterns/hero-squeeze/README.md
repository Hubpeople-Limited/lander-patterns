# hero-squeeze

**What it is and when to use it.** The whole page in one viewport: a
photograph, one claim, one control, the reassurance under it, and one piece of
proof. **Nothing goes below the fold, because nothing goes after it.**

Build it when paid traffic lands straight on the page and the only question is
whether they sign up. It is the highest-volume shape in acquisition and it is
the one shape where every extra section costs money.

The other heroes are **openers for pages that continue**; this one is the page,
which is why it is a separate pattern rather than a modifier. Nothing follows
it: a second section is how a squeeze quietly becomes a short landing page, and
`hero-overlay` is the opener for one of those.

**What it needs.** One landscape photograph at least 1600px wide with real alt
text; a headline of one line; one supporting sentence; a reassurance line; and
one piece of real proof. **Everything needed to decide is in those five
things**, because there is nowhere else. If the argument does not fit, this
brand needs a landing page.

**The two slots are slots on purpose.** Drop `cta-assurance` into `assurance`
and `member-strip` or `rating-mark` into `proof` — the proof a brand has
differs, and hard-coding one would gate the pattern on material half the
brands do not hold.

**With no proof to put there, delete the proof block rather than filling it.** A
squeeze with a real claim and no proof still converts; one with invented proof
puts a fabricated claim on the highest-traffic page the brand runs.

**Pairing.** `cta-assurance`, `member-strip` and `rating-mark` go inside it;
nothing goes after it. `signup-card` can take the button's place, assurance left
empty: words left, card right, and the photograph clipped to a fixed height so
it holds still while the section grows.

It refuses every other opener: `hero-overlay`, `hero-split`, `hero-centred`,
`hero-stated`, `hero-portrait`, `signup-steps`, `article-masthead`. A page
opens once: two means two first impressions and two claims on the `h1`.

**Brand adaptability.** Every ink is `--color-on-scrim` on a `--color-scrim`
ground, one of the pairs the contract states. The headline takes it too:
`--color-heading` is barred over a photograph however heavy the scrim.

The control is `--color-primary` with `--color-on-primary`, at 52px rather
than the usual 48: it is the only control on the page. Its focus indicator is
two bands, an `--color-on-scrim` ring backed by a `--color-scrim` halo, because
a photograph sits behind it and no token describes a photograph.

`--hero-squeeze-scrim-strength` is the one dial, held by `clamp()` at a floor of
`0.86`. That floor is lower than `cta-image`'s `0.92` deliberately: the copy
here sits in the middle of the frame rather than against an edge, and the
gradient reaches full strength behind it by 12% down.

**Over the library's placeholder the floor drops to `0.4`**, on a tint of the
brand colour mixed into `--color-scrim`, so the drawing shows. That ground is
known, so `ci/check_placeholder_scrim.py` holds the copy to 4.5:1 on it; a real
photograph, which carries no `[data-hub-placeholder]`, keeps the full floor.

**The ramp starts at 68%, and that number is load-bearing.** Content is centred,
so on a tall content box - 200% zoom, a long headline, a landscape phone - the
headline sits in the *top* of the ramp. The first stop has to clear 4.5:1 on its
own rather than lean on the block padding. It does on all four sample sets, but
the closest measures 4.51:1. Darkening an on-scrim ink or lightening a scrim
breaks that, so re-derive from `preview/tokens-*.css` before touching either.

**It is `min-height: 100svh`, not `height`, and that decides how it fails.**
The section aims to fill exactly one viewport. Where the content is taller than
the viewport — a long headline, a short window, 200% browser zoom, a phone in
landscape — **it scrolls rather than clipping.** A squeeze that hides its own
call to action has broken the only thing it was for, and a fixed height with
`overflow: hidden` fails WCAG 1.4.4 at 200% zoom. `svh`, not `vh`: `100vh` is
the largest viewport, so the control would sit behind the address bar.

**A viewport minus the furniture at BOTH ends.** A header sits above this
section and a footer below it, and the platform injects the footer at serve
time, so no markup here can enclose it: the height is `calc(100svh -
var(--page-header-height, 9.5rem) - var(--page-footer-height, 12.5rem))`.
Subtracting only the header leaves the page scrolling by the footer. Take both
numbers off the rendered page, never off `--logo-height`; TOKENS.md's *The
page's furniture* says how, and `0px` is the value for an end with nothing at it.
