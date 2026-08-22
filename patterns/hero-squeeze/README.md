# hero-squeeze

**What it is and when to use it.** The whole page in one viewport: a
photograph, one claim, one control, the reassurance under it, and one piece of
proof. **Nothing goes below the fold, because nothing goes after it.**

Build it when paid traffic lands straight on the page and the only question is
whether they sign up. It is the highest-volume shape in acquisition and it is
the one shape where every extra section costs money.

The other four heroes are **openers for pages that continue**. This one is the
page. That is the whole distinction, and it is why it is a separate pattern
rather than a modifier: it has a different job, a different height discipline,
and a rule the others do not have about what may follow it.

Do **not** put a second section after it. That is how a squeeze quietly becomes
a short landing page — which is a real and useful thing to build, and
`hero-overlay` is the opener for it.

**What it needs.** One landscape photograph at least 1600px wide with real alt
text; a headline of one line; one supporting sentence; a reassurance line; and
one piece of real proof.

**Everything the visitor needs in order to decide has to be in those five
things**, because there is nowhere else to put anything. If the argument does
not fit, the honest answer is that this brand needs a landing page, not a
squeeze.

**The two slots are slots on purpose.** Drop `cta-assurance` into `assurance`
and `member-strip` or `rating-mark` into `proof` — the proof a brand actually
has differs, and hard-coding one would gate the pattern on material half the
brands do not hold.

**When there is no proof to put there, delete the proof block rather than
filling it.** A squeeze with a real claim and no proof still converts. A squeeze
with invented proof is a fabricated claim on the highest-traffic page the brand
runs, which is the worst place in the estate to put one.

**Not on a page with `hero-stated`.** That one is the text-only opener for a page that continues; this is the whole page. A page opens once.

**Pairing.** `cta-assurance`, `member-strip` and `rating-mark` go inside it,
and nothing goes after it.

It refuses `hero-overlay`, `hero-split`, `hero-centred` and `article-masthead`.
A page opens once, and each of those is an opener for a page that carries on -
placing one beside this would give the page two first impressions and two
claims on the `h1`.

**Brand adaptability.** Every ink is `--color-on-scrim` on a `--color-scrim`
ground, one of the pairs the contract states. The headline takes it too:
`--color-heading` is barred over a photograph however heavy the scrim.

The control is `--color-primary` with `--color-on-primary`, and it is 52px
rather than the usual 48 — it is the only control on the page and the page has
exactly one job. Its focus indicator is two bands, an `--color-on-scrim` ring
backed by a `--color-scrim` halo, because a photograph sits behind it and no
token describes a photograph. Same technique as `media-card-grid`.

`--hero-squeeze-scrim-strength` is the one dial, held by `clamp()` at a floor of
`0.86`. That floor is lower than `cta-image`'s `0.92` deliberately: the copy
here sits in the middle of the frame rather than against an edge, and the
gradient reaches full strength behind it by 34% down.

**It is `min-height: 100svh`, not `height`, and that decides how it fails.**
The section aims to fill exactly one viewport. Where the content is taller than
the viewport — a long headline, a short window, 200% browser zoom, a phone in
landscape — **it scrolls rather than clipping.** A squeeze that hides its own
call to action to keep a promise about scrolling has broken the only thing it
was for, and a full-viewport section with a fixed height and `overflow: hidden`
is how a page in this library's own source material became unscrollable at 200%
zoom, failing WCAG 1.4.4.

So: no scroll on any viewport that fits the content, and a short scroll rather
than a hidden button on any that does not. `svh` rather than `vh` for the same
family of reason — `100vh` is the largest viewport, so the control would sit
behind the address bar on first load.
