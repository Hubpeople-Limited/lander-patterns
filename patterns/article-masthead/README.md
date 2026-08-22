# article-masthead

**What it is and when to use it.** The top of a page that *is* an article — a
blog post, a guide, a piece of advice. A metadata eyebrow (category, read time,
date) sits over a hairline; below it the display `<h1>`, a lede on a shorter
measure, and an author row with a portrait under a second hairline.

Use it when the page's whole job is one piece of long-form writing. That is the
material a dating brand needs for search visibility, and the library had nothing
for it: `heading-block` is a section opener with an `<h2>`, for announcing a
section *inside* any page. The two are not alternatives — an article page can
carry this masthead at the top and several `heading-block`s down the body.

Do **not** use it to head a section, and do not put it on a page that already
has a hero. `hero-split` and `hero-overlay` each ship the page's `<h1>`, so a
masthead beside either gives the page two, and a marketing hero above an article
buries the piece it was meant to introduce. Pick one opener per page.

The root is a `<div>`, not a `<header>`. A `<header>` that is not inside an
`<article>`, `<aside>`, `<main>`, `<nav>` or `<section>` maps to the banner
landmark, and pasted into a page body this one would not be — so it would
announce itself as a second site header alongside the chassis's real one.

**What it needs.** All of it real, and it gates use:

- A title, and a lede of one or two sentences that actually stands the piece up.
- The category the article genuinely sits in, an honest read time, and the real
  publication date. `datetime` takes the machine-readable form (`2026-08-22`),
  the slot beside it the words a reader sees.
- The name and role of the person who wrote it, and their portrait. The alt
  is `""` unless the portrait carries something the byline beside it does not
  describing that portrait. A byline is a claim about a named human being: if
  nobody is willing to be named, this is the wrong pattern, not a field to fill.

Portrait renders at 44px and is cropped square, so supply at least 88px square.

**Not on a page with `hero-centred`.** An article opens on its masthead, and a hero above one gives the page two openers and two competing claims to the `h1`.

**Not on a page with `hero-squeeze`.** That one is a whole page in one viewport with nothing after it, so there is no article for a masthead to open.

**Not on a page with `hero-stated`.** An article opens on its masthead, and a hero above one gives the page two claims on the `h1`.

**Pairing.** `heading-block` down the article body, for each section within it.
Nothing else belongs directly beneath the masthead — the article's own first
paragraph does. Page furniture such as `cta-sticky` is a page-level decision
and is unaffected either way.

**Brand adaptability.** `--font-heading` and the title's negative tracking carry
most of the character; the title scales `clamp(2rem, 4vw, 3.5rem)`, which stays
above the size the contract requires for `--color-heading` at every width. The
block paints `--color-bg` deliberately: `--color-heading` is only guaranteed
against that ground, so a brand must not re-ground the masthead on a surface
token. `--color-rule` draws both hairlines and brands may set it as soft as they
like — nothing here depends on either line being seen, they only frame.

Two measures do the work: the title runs to the full 52rem column with
`text-wrap: balance`, the lede stops at `42ch`. Brands wanting a wider standfirst
raise that one value; setting the two equal loses the shape.
