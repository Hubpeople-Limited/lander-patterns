# Contributing a pattern

You need a GitHub account and nothing else — no local tooling, no build. The
whole flow works in the GitHub web editor: add or edit files in a branch, open a
pull request, let the checks run, and a maintainer merges. Merging tags a
release automatically; agents pick the new library up on their next session.

## A pattern is a folder

```
patterns/<pattern-name>/
  pattern.html            metadata header + the markup
  pattern.css             the styling, tokens only
  README.md               the guidance a builder reads before using it
  preview-content.json    sample values so the preview can render it
  variants.json           the words a chooser shows - only if you declare any
```

Name the folder for what the pattern is: `hero-split`, `pricing-tiers`,
`cta-sticky`. Lowercase, hyphens, no dates.

## pattern.html

Starts with the metadata header, exactly this shape:

```html
<!--
name: your-pattern-name
version: 1
type: section
page-types: homepage, landing
content-shape: single claim
requires: none
description: One line - what it is and the job it does.
keywords: three or four words someone would search for
needs: the real content this consumes, named precisely
pairs-with: none
avoid-with: none
tokens-used: --color-primary, --font-heading, --space-6, --card-radius
one-per-page: no
motion: none
status: active
added: 2026-08-21
-->
```

**Copy that verbatim and fill it in — it carries no `#` annotations on
purpose**, because CI rejects those in a pattern header (they are this
document's notes, not your pattern's, and they ride into every page built from
it). `name` must equal your folder name. Leave `pairs-with` and `avoid-with` as
`none` until you have someone to name: **`avoid-with` is mutual, so adding an
entry means editing the other pattern's header in the same commit**, and CI
fails the build if only one side names the other — as it does if an
`avoid-with` entry never appears in your README, since the header is what an
agent parses and the README is what a person reads. What each field means:

| Field | Value |
|---|---|
| `display-name` | The name a PERSON sees - "Footer", "Section opener", "Questions and answers". `name` is a folder name and the thing a brand pins, so it can never change; this can, and it is what a chooser shows. `colophon` is a printing term and `opener-split` is this library talking to itself: neither belongs in a tool where somebody is picking what to put on a page |
| `summary` | One sentence, in a partner's words, saying what the pattern is. Not `description`, which is written for an agent shortlisting and is longer and more precise than a person wants |
| `type` | `component`, `section` or `page` |
| `content-shape` | The shape of the content this suits, in the building skill's own vocabulary: `narrative`, `peer set`, `comparison`, `progression`, `single claim`, `question and answer`, `reference`. It is what an agent matches a pattern against before it opens one, so it is **that** list rather than a second one that reads like it — CI holds you to it. Two spellings for one idea is a lookup that quietly returns nothing, and adding a value here means adding it to the skill's own table in the same change |
| `requires` | The class of material the pattern cannot exist without: `none`, `photography`, or `consented-people` — real pictures of real people who agreed to appear. It is coarser than `needs` and is read first, because a brand with no photography can skip eighteen patterns without reading eighteen `needs` lines. It is on the index row for that reason |
| `whole-page` | `yes` if this pattern IS the page and nothing follows it. One pattern carries it today. Omit it otherwise. It is not only a label: a full-viewport section carrying it must subtract `--page-footer-height` as well as `--page-header-height`, because the site footer is inside a promise about the page |
| `behaviours` | Names from `lib/REGISTRY.md`, where the pattern carries `data-hub-module` hooks. Omit it if there are none. The header, the markup and the registry must all agree, and CI checks all three |
| `needs` | The real content this consumes. It gates use: no material, wrong pattern. Say "real" and mean it |
| `pairs-with` | Patterns that read well after this one. Not page furniture — `cta-sticky` belongs to the page, decided once |
| `avoid-with` | Patterns that must not both appear on one page, or `none` — two image-led card runs, a full-screen finale and a fixed bar. It is the strong reading on purpose: follow it and the weaker adjacency problems cannot arise either. Mutual by nature, so CI checks both sides name each other. A constraint that is only ever about *neighbours* ("not directly above this") is prose in the README, not an edge here |
| `one-per-page` | `yes` if a page may hold at most one. Two heroes or two sticky bars are a mistake, not a layout choice. This is where cardinality lives, not in `avoid-with`; where two patterns are **alternatives**, set it on both and say which to pick when in both READMEs |
| `tokens-used` | The contract tokens your `pattern.css` references. Your own `--<pattern-name>-*` properties are yours and are ignored |
| `variants` | The axes this pattern can be varied along, as `axis=value\|value; axis=value\|value` — for example `ground=plain\|soft\|brand; alignment=default\|centred`. Omit it where there are none. Every value must be a real `.<pattern-name>*--<value>` selector, and CI checks that: two READMEs once described a "Variant" with no CSS behind it, which is an instruction to hand-edit a file the version pin then names. `default` means the pattern with no modifier on it, which is a real choice and has no class. This is the field that makes a second look **visible while shortlisting** — a pattern that ships one look is one that will be recognised across the estate, and an axis nobody can see is one nobody turns |
| `motion` | `none`, `subtle` or `expressive` — this pattern's OWN CSS as shipped. Behaviour-driven motion is declared by `behaviours:` and is always reduced-motion-safe. CI checks `none` against the stylesheet |
| `status` | `active`, or `deprecated` with a `replaced-by: <name>` line |
| `version` | Bump it whenever `pattern.css` or the markup changes. A brand pins `name@version` in its own stylesheet, so an unbumped change makes that pin name two different files. CI compares against the merge base |

Then the markup. Three rules:

1. **Slots mark where real content goes.** A block of content is
   `<!-- slot: name -->` (that exact spelling); a value inside an attribute is
   the literal `slot:name` (for example `src="slot:hero-image"`). Everything
   in `needs` gets its slots; supporting slots (a section heading, alt text,
   an aria label) are fine too — the pattern README's "what it needs" section
   accounts for all of them.
2. **Platform `{{ }}` tokens come from the table in [TOKENS.md](TOKENS.md)**,
   spelled exactly. Join and login controls are always `{{join.url}}` /
   `{{login.url}}` — never a written-out URL.
3. **A pattern pulls nothing in from elsewhere.** No `<iframe>`, `<object>`,
   `<embed>`, `<link>`, `<base>` or `<meta http-equiv>`, and no form posting
   to another host. An embed runs third-party code, which is the outcome the
   no-script rule exists to prevent; a `<link>` pulls a stylesheet and defeats
   the token contract; a `<base>` silently repoints every relative URL,
   including the platform's own. A map, a video or a reviews widget is a
   likely thing to want and is still refused.
4. **No `<script>`, no `<style>`, no `style=` attributes** (the one exception:
   a custom-property data binding such as `style="--i: 3"`). Real heading tags,
   real `<button>`/`<a>`, labels on every input, `alt` on every image slot.

## pattern.css

- **Every selector references the pattern's own classes**: `.hero-split`,
  `.hero-split-copy` — normally as the selector's start; a scoping form like
  `body:has(.cta-sticky)` is fine. That is what lets many patterns share one
  stylesheet without collisions. CI rejects any selector that does not
  reference a `.pattern-name` class (references inside `:not()` do not
  count — they would target everything else).
- **Tokens only** — no hex colours, no hardcoded radii or shadows. Tints are
  `color-mix()` of contract tokens.
- Mobile-first: base styles for small screens, scaling up with
  `@media (min-width: …rem)` or range syntax (`@media (width < 60rem)`) —
  both are fine. This one is measured rather than taken on trust: see
  **[At a phone width](#at-a-phone-width)** for what your render has to
  survive and how to run it yourself.
- Every pattern styles itself through at least one token — a markup-only
  pattern with an empty stylesheet is not accepted.
- If the pattern moves (`motion: subtle`/`expressive`), keep every animation
  and transition inside the reduced-motion guard pattern shown in existing
  patterns, and nothing auto-moves for more than five seconds.

### The ground ladder — one vocabulary, four rungs

A pattern that offers a choice of ground names it from this list and no other:

| Modifier | Ground | Ink |
|---|---|---|
| `--plain` | `--color-bg`, the page's own ground | `--color-text`, or `--color-heading` on genuinely large text |
| `--soft` | `--color-surface-soft`, the tinted fill | `--color-text` |
| `--brand` | `--color-primary` | `--color-on-primary` — the contract's stated pair |
| `--deep` | `--color-scrim` | `--color-on-scrim` — the contract's stated pair |

Offer the rungs that suit the pattern; nothing has to offer all four. **Do not
invent a fifth name for one of these, and do not invent a fifth rung.** Two
patterns spelling the same idea differently is a choice a builder cannot
generalise, and this is the axis that most cheaply stops two pages on one brand
looking alike — which only works if it is the same axis everywhere.

Set the ground's ink and its ground as `--<pattern-name>-*` properties on the
modifier, then have every rule read those rather than a contract token. Nothing
in the file should know which ground it is on: that is what stops a rule being
correct on two rungs and wrong on the third.

`feature-panels` spells its first rung `--light` and predates this table. Its
three grounds are a fixed ranked ladder rather than a choice, so it is left as
it is; a pattern offering a real choice uses the names above.

## What may be written down, and where

This repository is public and its files are published twice over: `pattern.css`
is appended verbatim into a brand's stylesheet, and `pattern.html` is pasted
into a page. Assume every byte of both is served to the public, because it is.

**Never, in any file:**

- A credential, token, key or password, in any form — including hashed,
  encoded, or split across lines. CI scans for a private list of strings it is
  not given in this repo; when the list is missing the build fails rather than
  passing, so a green build means the scan ran.
- Anything identifying a person, a machine, an account, an internal host, an
  internal path or an internal system. Not in code, not in a comment, not in a
  commit message.
- Any account of how the file came to be: what an earlier version did, what was
  changed and why, what a review found, what was decided in conversation, what
  any tool or model contributed. None of it helps anyone build a page, and all
  of it ships. CI rejects the vocabulary of it.

**A comment earns its place by stopping someone breaking the pattern.** That is
the whole test. "`svh`, not `vh`: the address bar would cover the foot" earns
its place. "We chose `svh` after finding that…" does not, and neither does the
measurement behind it.

| File | Comments are | Ceiling |
|---|---|---|
| `pattern.css` | Warnings only — a rule that looks like a mistake and would be "fixed", a value that must stay in step with another | 12% of lines |
| `pattern.html` | Build instructions — which slot takes what, what to duplicate, what to delete. Removed when the pattern is placed | 35% of lines |
| `README.md` | Everything else. Reasoning, sources, measurements, trade-offs. Read at build time, never shipped | 80 lines |

If a comment is worth keeping and is not a warning or an instruction, it
belongs in the README. That is what the README is for, and it costs a reader
nothing because it never reaches the page.

## README.md — the four sections, in this order

1. **What it is and when to use it** — and, just as important, when *not* to.
2. **What it needs** — the real content it consumes, matching `needs`.
3. **Pairing** — what it sits well next to, what it fights with.
4. **Brand adaptability** — which tokens change its feel most, and any variants.

Aim for about 50 lines and treat 80 as the ceiling, which CI enforces. Agents fetch these at build time, so length is a running cost - put the decision first and the reasoning behind it, never the reverse. A builder reads this before the markup.

## variants.json — only if you declare `variants`

`variants: ground=plain|soft` tells a tool the rungs exist. It does not tell
anybody what picking one *does*, and `menu-centre` is a class name: exact,
versioned, pinned by brands, and no use at all to a partner deciding what a
page should look like. So a pattern that offers a choice also ships the words:

```json
{
  "ground": {
    "label": "Background",
    "note": "The colour behind this section. Change it between one section and the next.",
    "rungs": {
      "plain": { "label": "Default", "note": "The page's own background colour." },
      "soft":  { "label": "Light",   "note": "A soft tint, to separate this section from the one above." }
    }
  }
}
```

**The label is what a partner sees; the key is what ships.** A chooser renders
"Background → Light" and still writes `ground=soft` into the recipe, because
that is what this library, `ci/check_page.py` and every brand stylesheet
already agree on. Name the axis and the rungs the way another CMS would —
"Background", "Sticky header", "Left" — not the way the stylesheet does.

CI holds the file to **exactly** the axes and rungs the header declares, in
both directions: a rung with no words is a rung somebody picks blind, and a
note for a rung that no longer exists is one nobody will notice has gone
stale. `ci/build_configurator.py` publishes it as `variantNotes`, so the
chooser reads the library rather than a second copy of it kept elsewhere.

**Order comes from `variants:`, not from this file.** The published bundle
sorts its keys for a stable diff, so a tool takes rung order from the
`meta.variants` array and looks the words up by key.

## preview-content.json

Sample values for each slot so the preview pages can render — obviously fake by
design (`"headline": "Sample headline for preview"`). These values exist only
for the preview build; they never appear on a real page. To keep them
honestly fake, CI requires every value — image paths included — to contain the word
"sample" or "preview", so image values reference the `sample-*.svg` files
that ship in `preview/`. A value reading like a real claim fails the check.

```json
{
  "headline": "Sample headline for preview",
  "subhead": "One supporting sentence for the preview render.",
  "hero-image": "sample-wide.svg"
}
```

A value may carry simple markup where the slot fills a list or repeated
element (`"tier-features": "<li>Sample feature</li>"`); keep it minimal, and
image values reference the sample files that ship in `preview/`.

## What the checks do

On every pull request, CI:

- validates the metadata header (all fields, known values, unique name, no
  chassis-reserved names, cross-references to real patterns);
- rejects scripts (including `on*=` handlers and `javascript:` URLs), style
  attributes, unknown `{{ }}` tokens, selectors that do not reference the
  pattern's classes, colour literals in any syntax, hardcoded radii/shadows,
  non-canonical slot spellings, and slots missing from
  `preview-content.json`;
- regenerates `INDEX.md` itself — you never edit it, in a PR or otherwise;
- checks that `tokens-used` lists exactly the CONTRACT tokens your
  `pattern.css` references — your own `--<pattern-name>-*` properties are
  yours to use freely and are ignored by this check;
- refuses certain internal strings (the check reports position only);
- renders every pattern against five sample token sets — soft-rounded,
  sharp-flat, `dark`, a hostile brand whose `--color-heading` sits at the
  3:1 large-text bar and whose surfaces are dark, `brand`, which carries
  the token vocabulary real brands actually ship, and `display`, a hostile
  brand whose heading face is not one this library was designed against.
  Read `dark` and `display` as tests rather than styles: `dark` exists to
  fail patterns that ground text on tokens the contract does not guarantee,
  and `display` to fail anything whose size, leading or measure was decided
  by looking at Georgia. The pages attach to your pull request as the
  `pattern-previews` artifact, so you see all five before anyone merges;
  on merge they publish to the repo's Pages site;
- lays every pattern out in a headless browser at 320 and 360 and measures
  what came out — sideways scroll, tap-target size, text size, on `brand` and
  again on `display`. See [At a phone width](#at-a-phone-width);
- renders every display measure on all five sample brands and requires the
  resolved widths to be the same number, then re-renders them in the pre-v57
  `ch` form and requires that check to fire. See
  [Display measures](#display-measures).
- assembles a page around every full-viewport pattern — this library's own
  header above it, a stand-in site footer below — at five real device
  viewports, and requires the thing the pattern promised to fit to actually
  fit; then re-renders it with the furniture allowance the live defect had and
  requires that check to fire. See
  [The fold, measured on an assembled page](#the-fold-measured-on-an-assembled-page).
- renders every pattern that carries a brand mark against the logo shapes real
  brands ship — including an SVG with a `viewBox` and no dimensions — and
  requires the mark to be drawn at the height the header reserved for it; then
  re-renders it the way the live defect had it and requires that check to fire.
  See [The brand mark](#the-brand-mark).

A red check names the file and the rule. Fix and push again — nothing merges
red.

### Every check above measures one pattern alone

That is the right shape for most defects, and it is blind to the ones that only
exist between neighbours. A pattern has no page: it cannot see what sits above
it, what follows it, or what the reader has already been shown.

`hero-overlay` shipped `min-height: 100svh`, which is correct for a pattern and
wrong for a page — measured from below a site header it put the join control
exactly one header-height below the fold. It passed every gate on this list. It
took a screenshot of a browser.

So there is one more check, and it takes a **page** rather than a pattern:

```
python ci/check_page.py homepage hero-overlay stats-band cta-band
python ci/check_page.py homepage hero-stated:ground=deep heading-block benefit-tiles
python ci/check_page.py pricing hero-stated:ground=plain pricing-tiers cta-band \
    --brand ../some-brand/site/global.css --out /tmp/page
```

A recipe is a page type and then the patterns in the order they appear. A
pattern may carry the variant it was placed with — `hero-stated:ground=deep` —
and some checks can say nothing without it, so they say so rather than guess.

There is also a sweep that needs no page at all:

```
python ci/check_page.py --sweep
```

**A pattern that claims a whole viewport and subtracts nothing is wrong wherever
it lands**, so that half of the fold rule is held against all 44 patterns rather
than against the handful a fixture happens to name. `cta-curtain` and
`pinned-cards` are exempt in one named set in the code: they sit mid-page and at
the end, where nothing is above them by the time a reader arrives. The first
version of this file enforced the rule through the fixtures alone, which reached
five openers out of six and thirty patterns not at all, while printing "clean".

It fails a page where: a modifier is chosen that the pattern does not offer
(`hero-stated:ground=soft` when it ships `plain|brand|deep`); a full-viewport
**opener** subtracts nothing for what sits above it; a `whole-page` opener
allows for the header and not for the site footer under it; a `one-per-page`
section appears twice; two patterns whose
`avoid-with` names each other are both present; a pattern is used on a page type
it does not list; the page has no `h1` or more than one; a heading level is
skipped at the join between two patterns; or two neighbours land on the same
ground and read as one long section. It also reports, without failing, which
behaviours would need `hub.js` on the page and what material the brand must
supply.

`--out` writes the assembled page with a stand-in site header above it, which is
the only way to look at the thing the fold check is about. What that page
actually measures out at is `ci/check_fold.py`'s job, below.

**`ci/page-recipes.json` holds real pages that must stay valid**, and
`ci/test_gates.py` runs them. Breaking one is allowed — it is a decision, and
that file is where it gets made deliberately rather than found by a partner. Add
a recipe when a real build turns up a composition worth protecting; do not add
permutations, because a fixture nobody understands is one that gets deleted the
first time it fails.

### The fold, measured on an assembled page

Every check above — the page-level one included — measures **one pattern with
nothing around it**. `ci/check_page.py` reads source, so it knows an opener
subtracts *something* for what sits above it. `ci/check_phone.py` renders, but
it renders the pattern alone in a bare document: no header over it, no site
footer under it, and a viewport height of 760 that is no device's.

So nothing here had ever asked the one question a full-viewport pattern makes a
promise about. A page built from `hero-squeeze` — the pattern whose whole
premise is one viewport and nothing below the fold — overflowed a 1280×800
laptop by 177px, and 166 of the 177 were a site footer the platform injects at
serve time. Every gate in this repository passed it.

```
python ci/check_fold.py                  every full-viewport pattern
python ci/check_fold.py hero-squeeze
python ci/check_fold.py --broken         the positive control
python ci/check_fold.py --out /tmp/fold  keep the assembled pages
```

It puts each one in a page the way the platform serves one — this library's own
`masthead-nav` above it, a stand-in site footer below — at five real device
viewports, **width and height**, and holds the pattern to the promise its own
metadata makes:

| The pattern says | What must be true |
|---|---|
| `whole-page: yes` | the **document** does not scroll. It claims to be the page, so the footer is inside what it promised |
| anything else | the **section's foot** is at or above the fold. The page continues under it, so the footer is not |

**Which patterns are discovered, not listed** — anything whose CSS claims a
viewport height, minus `check_page.py`'s `FULL_VIEWPORT_EXEMPT`. Naming them
here would leave the next full-viewport opener outside the gate on the day it
lands, which is how the fold rule came to cover five openers out of six once
already.

**What fails is the allowance, not the overflow.** The check reads two numbers
off the rendered page: what the section's own `calc()` **set aside** for the
page's furniture — the viewport minus the resolved `min-height`, so every
`var()`, fallback and media query is already applied — and what the furniture
**measured**. Furniture taller than the allowance is this library's arithmetic
being wrong, it is wrong wherever the pattern lands, and it fails.

It used to test the overflow instead. While the section sits on its floor the
two are the same subtraction, so nothing that ever failed stops failing; what
changes is a case the overflow could not speak about at all. If the **content**
has grown past the floor, the section is doing what `hero-squeeze`'s README says
it does — a short scroll rather than a hidden join button — and what it depends
on is the copy somebody placed. That is reported with the numbers and never
failed, because a gate with an opinion about sample content is a gate with a
false positive in it. But the furniture arithmetic underneath a grown section
can be just as wrong, and it was unreachable: `hero-squeeze` is content-bound at
most viewports here, so its `--page-footer-height` sum could not be failed by
this gate at all. Reading the allowance separates the two properly — the copy is
still nobody's fault, and the sum is still checked.

**A rendered height is a height in a particular typeface, and CI does not have
your fonts.** On 2026-08-26 this gate went red on the runner and green on the
machine the commit was written on. `preview/tokens-display.css` builds its face
from a `local()` chain; the runner has no Georgia, landed further down the chain
on a wider serif, `masthead-nav`'s wide menu broke onto a third line, and the
header rendered 173.8px where `--page-header-height` had set aside 152. Nothing
was wrong with the runner and nothing was wrong with the laptop. What was wrong
was a token measured on one machine and believed everywhere. If you change a
sample token set's face, or add one, **measure its header against every face its
own stack can reach**, not against the one your machine happened to pick — and
if a gate here is red only in CI, look at the fonts before anything else.

**The positive control is not optional.** `--broken` re-renders every page with
the furniture tokens set the way the live defect had them — a header allowance
derived from a 70px logo, no footer allowance at all — and requires the check to
fire. Exit 0 on that run means the defect was detected. It reproduces the live
figures: 230px over at 390×844, against the 230px measured on the served page.

### At a phone width

Every check named so far, the page-level one included, **reads source**. It
knows your stylesheet says `min-height: 100svh`; it does not know what 100svh
turned out to be, whether the wordmark landed on top of the first menu link, or
whether the whole thing scrolls sideways. Three defects have reached live sites
through that blind spot in as many weeks, and all three were found the same
way — by opening a browser.

Most of the traffic these pages carry is phones, so that is what gets rendered:

```
python ci/check_phone.py                        every pattern, 320 and 360
python ci/check_phone.py hero-split faq-details  just these
python ci/check_phone.py --out /tmp/phone        keep the pages to look at
```

It needs a browser — `pip install playwright && playwright install chromium`,
once. **Without one it prints `SKIPPED` and exits 0**, so a contributor working
in the GitHub web editor is never blocked by tooling they cannot install. A
skip is not a pass and the output says so; CI installs the browser, so the
measurement always happens before anything merges.

**320 and 360.** 320 is the floor — the narrowest viewport still in real use,
and where anything too wide breaks out first. 360 is the mode, the single
commonest width in the traffic these pages serve, and it catches the grid whose
breakpoint fell between the two. 390 and 414 were tried and found nothing 360
had not, for a third more runtime.

Your pattern must, at both widths:

| Rule | The number |
|---|---|
| **Not scroll sideways.** The document's scroll width may not exceed the viewport | viewport + 1px |
| **Give every control a thumb-sized target** — `button`, `summary`, `input`, `select`, and any `<a>` drawn *as a control* rather than set as text | 44px in the smaller dimension |
| **Keep text readable** | 12px |
| **Keep form fields at a size iOS will not zoom into** | 16px |

Three of those carve out the cases that would otherwise make the gate
unusable, and it is worth knowing which, because they are also the shapes you
are allowed to ship:

- **A horizontal rail does not count.** Anything inside an element with its
  own `overflow-x` is contained by design — a carousel track is *meant* to be
  wider than the screen, and so is a cover-cropped image inside a frame that
  clips it. Only the document's own scroll width fails.
- **A link that is text is not a control.** Holding prose links to 44px means
  double-spacing prose, and WCAG carves the same exception for the same
  reason. The test is whether you gave it a box — padding, a `min-height`, a
  border, a fill. A row title in a grid parent computes as `display: block`
  and is still just words; a padded, filled link is a button and is measured
  like one. An `<a>` wrapping an image is a control either way: a logo is
  tapped, not read.
- **A small control inside a big label is a big control**, because the label
  activates it. A 16px checkbox in a 48px label passes.

**What it deliberately does not check.** A rule that cannot be made reliable is
worse than none, because the first false positive teaches everyone to stop
reading the output — and this repo has learnt that once already.

- **Content clipped by `overflow: hidden`.** Indistinguishable from the
  cover-crop that every image frame in the library does on purpose.
- **Content bleeding off the *left* edge.** Genuinely unreachable when it
  happens, but a deliberate left bleed is a real technique and nothing in the
  render tells the two apart.
- **Long unbreakable words.** Not a gate, and the reason is worth stating: 36
  of the 45 patterns break out of 320px on one, because only two patterns in the
  library set `overflow-wrap` at all. A rule failing four fifths of the
  library on the day it lands is a rule that gets switched off. The defence
  belongs once in the brand's base stylesheet, not forty-five times here.
- **Overlap between elements.** The header-logo-over-the-menu-link defect is
  exactly this and it is the obvious next check to build. Rect intersection
  alone is far too noisy — every deliberate overlap in the library trips it —
  so it needs a narrower rule than anyone has written yet.

**`ci/check_phone.py` carries a baseline** in `ACCEPTED`: four faults the
library has today, each with the reason it is not failing the build. A fault
matching one is reported as `known`; anything else is `new` and fails. So the
gate stops regressions from the day it lands without forcing four design
decisions in the same hour, and the debt stays visible in the output rather
than hidden by an exclusion nobody can see. **Fixing a pattern means deleting
its entry** — a run whose baseline matches nothing reports `STALE` and fails,
because a baseline that has outlived its defect is how a gate goes quiet.

`ci/test_gates.py` proves both halves against synthetic fixtures — seven faults
it must catch, ten valid shapes it must ignore — and then sweeps the library.
Proving it against the real patterns alone would prove nothing about the half
that matters: a check that never fires passes a clean library perfectly.

**CI runs it twice**, once on `brand` and once on `display`, whose heading face
is not one this library was designed against. `--tokens` picks the set. The
baseline is measured on `brand` and stays there, because **every entry in it is
a pixel size and a pixel size is a size in a particular typeface**: the
`masthead-nav` login link is 40px tall on Georgia and clears 44px on `display`,
whose line box is 57% taller. So `STALE` detection is reported only on the
baseline set — on any other the run says so in its output rather than sending
you to delete a live entry.

### The brand mark

Every sample image in this repository carries `width` and `height` attributes,
and `preview/sample-wordmark.svg` carries them in the file too. **Real brand
logos do not.** A brand mark is almost always an SVG exported with a `viewBox`
and nothing else: it has a *ratio* and no intrinsic size at all, which is a
different sizing problem and one nothing here had ever rendered.

`masthead-nav` sized its logo with `width: auto; height: auto` under a
`max-width` and a `max-height` — two ceilings and no floor. An image with
intrinsic dimensions settles on those and is capped. An image with only a ratio
has nothing to settle on and resolves to **0×0**: no brand mark at all, on every
phone and tablet, on every brand using any of the six page shells. Every gate in
this repository passed it, because the sample logo has a size.

```
python ci/check_logo.py                  every pattern that carries a logo
python ci/check_logo.py --broken         the positive control
python ci/check_logo.py --tokens display
python ci/check_logo.py --out /tmp/logo  keep the rendered pages
```

It renders each pattern against four logo shapes — a ratio-only wordmark, the
same file with the `<img>`'s own `width`/`height` dropped, a ratio-only square,
and a sized wordmark as the control — at six widths straddling `60rem`, and
fails a mark that is not drawn, one whose box is not as tall as `--logo-height`
resolved to on that page, or one stretched out of its file's ratio. The token is
measured off a probe element rather than read as text, because `--logo-height`
is `2.75rem` or whatever the brand wrote, and the number that matters is the one
the browser resolved.

**Which patterns are discovered, not listed** — anything whose markup carries an
`<img>` on `{{logo.src}}`. One does today. **`--broken` is a positive control
and CI runs it**: it appends one rule putting the logo back the way the defect
had it and requires the check to fire. It is appended rather than spliced into
the stylesheet so that rewording the shipped rule cannot quietly disarm it.

If you pin a replaced element's height, pin `object-fit` with it. The moment a
`max-width` bites, a box with a set height and no `object-fit` stretches what is
inside it.

### Display measures

A measure is a `max-width` on display type: the number that decides whether a
headline lands on two lines or three. Until v57 those were written in `ch`, and
`ch` is not a length — it is the advance width of *zero in the face actually
used, at the weight actually used*. Georgia Bold is `0.7012em` and Arial Bold
`0.5562em`, so `max-width: 16ch` was **26% wider on one sample brand than
another** and one headline had been rendering on two lines for some brands and
three for others since it was written. v57 moved every display measure to `em`.

That was a claim. `ci/check_measures.py` is the measurement:

```
python ci/check_measures.py                every measure, every sample brand
python ci/check_measures.py hero-stated    just this one
python ci/check_measures.py --as-ch        the positive control, below
```

It renders each measure on all five sample brands at 1280 and 1024 and
requires the resolved widths to be **the same number** — the only tolerance is
0.05px, which is float formatting rather than layout. It also fails a display
measure written in `ch` at all, which is the defect rather than its symptom.
**Body measures stay in `ch`** and are not judged: there `ch` is doing the job
it exists for, holding a line to a character count. Which selectors count as
display type is `ci/_display_type.py`'s answer, the same one the type-dial
check uses.

Two things about it are worth knowing before you touch either:

- **`--as-ch` is a positive control, and CI runs it.** It re-renders every
  measure in the pre-v57 form and requires the check to *fire*; exit 0 means
  the defect was detected. A gate that has only ever run against code that
  passes has not been shown to catch anything.
- **The hostile brand is calibrated before anything is reported.**
  `preview/tokens-display.css` builds its face from `@font-face` +
  `size-adjust` over a `local()` chain, and if that chain resolves nothing the
  family is simply unavailable, `--font-heading` falls through to Georgia, and
  the fifth brand becomes a fifth ordinary one — silently, and looking exactly
  like a pass. So the face is measured against its own fallback stack first,
  and a run that cannot show the adjustment took effect exits 3 having
  reported nothing.

## Behaviours — platform-delivered JavaScript (gated)

Patterns never carry a `<script>`; that rule does not move. But the library
has a second half: **`lib/hub.js`, one behaviour bundle that arrives beside
the patterns rather than inside them.** Markup opts in with
`data-hub-module="<name>"` attributes, which are **inert data attributes until
the bundle is on the page**, so a pattern ships its hooks and lights up
whenever the bundle turns up — with no change to the pattern.

How it turns up is a decision for whoever is building the site, and a pattern
must work either way. A site can carry the file as its own asset and reference
it with a single `<script type="module">` tag. A platform can inject it
instead, which is better where it exists — one cached copy across every brand,
versioned centrally, and no page carrying a tag at all.

A pattern that uses a behaviour declares it in the header
(`behaviours: reveal`) and hooks it in the markup; CI checks the header, the
hooks and `lib/REGISTRY.md` agree. Adding a **new** behaviour is a bigger
contribution — the JS goes into `lib/hub.js`, a row into `lib/REGISTRY.md`,
and a pattern demonstrates it — and it must obey five rules:

1. **The HTML must already work.** The behaviour may only enhance; if the
   no-JS render is broken, the contribution is rejected.
2. **Markup is the API.** Activated only by `data-hub-module`; configured
   only by `data-hub-*` attributes; never reaches outside its own element.
3. **Own nothing global.** No new globals (the library owns
   `window.HubBehaviours`), events dispatched as `hub:<name>:<event>`, no
   document-wide styles or listeners — the library's own namespaced `.hub-*`
   state classes, injected centrally by the runtime, are the one exception.
4. **Init twice, destroy once.** Idempotent init, error-contained per
   element (one broken element never breaks the page), listeners cleaned up.
5. **Motion is opt-in and pausable.** Everything honours
   `prefers-reduced-motion`; anything auto-advancing ships a visible pause
   control and halts on hover and focus — WCAG 2.2.2 is not per-brand
   configurable.

The preview harness embeds `lib/hub.js` so behaviour patterns can be seen
working; real pages get it only from the platform.

## Changing an existing pattern

Any change to `pattern.css` (or to the markup's structure) bumps `version` in
the header. Sites that already use the pattern keep the version they adopted;
the bump is what lets a later build see there is something newer. Never delete
a pattern that has shipped — set `status: deprecated` and `replaced-by:` and
leave it in place.


## Contributing a recipe

A recipe is not a pattern and not a shell. A shell is a thing — page markup,
assembled and maintained. A recipe is the order sheet above it: which shell,
which ground each band sits on, how the page opens and closes, the structural
signature it commits to, and a slot for the brand's own typeface pairing. It
exists because a shell alone risks sameness — every brand taking `pricing` gets
one page — and a second recipe on the same shell is the cheapest way two brands
end up with pages that read as genuinely different.

One file, `recipes/<name>@<version>.md`, and **the filename is the pin**. It
opens with a fenced block, then two or three short paragraphs somebody who is
not a developer can read: what the page is, who it suits, and what it
deliberately does not do. No class names, no jargon — the register of
`patterns/masthead-nav/variants.json`'s notes, not of this document.

````
```recipe
recipe: pricing-straight-answer@1
shape: reference
shell: pricing
look: hero-stated alignment=centred
grounds: plain, soft, plain, brand
opens: a plain statement of what it costs, with no build-up in front of it
closes: a full-width band in the brand colour, carrying the one control
signature: stated opener, tier cards, questions, band
pairing: brand
notes: the price is above the fold and nothing is withheld
```
````

One `field: value` per line, no blank lines inside the fence, in exactly that
order. `look` and `notes` are optional; everything else is required.

| Field | Value |
|---|---|
| `recipe` | `<kebab-name>@<integer>`, the recipe's own pin. Versioned like a pattern's and never renumbered: it is what a brand records when it takes one |
| `shape` | The content shape this recipe fits — `narrative`, `peer-set`, `comparison`, `progression`, `single-claim`, `question-and-answer`, `reference`. The same seven a pattern's `content-shape` uses, hyphenated |
| `shell` | A shell name from `compositions/`, **without its version** |
| `look` | Semicolon-separated `<pattern> axis=value[ axis=value]` entries — the dials this recipe sets over and above what the shell already pins. Pattern names, also without a version. Every axis and value must be one the pattern really declares |
| `grounds` | One rung per band, top to bottom, from `plain`, `soft`, `brand`, `deep` |
| `opens` | One line: the thesis form — a photograph, a claim, the first row of the content, a number, a question |
| `closes` | One line: a band, a line in the prose, a single link, a quiet panel, the last row, or nothing |
| `signature` | Ten words or fewer — the structural signature the page commits to. Longer than that and it is a description of the page instead, which the paragraphs underneath already are |
| `pairing` | The literal `brand`. A slot, filled at build time from the brand's own record |
| `notes` | One line, or leave it out |

Two rules decide most of what a recipe may say:

- **Pinless by default.** A recipe names `pricing`, never `pricing@3`, and
  `hero-stated`, never `hero-stated@4`. A bare name resolves at build time —
  against the brand's own record first, then the library's current release. A
  pinned one is a menu item that ages the day the library moves, and it ages
  silently, because it still reads correctly.
- **A library recipe is brand-agnostic.** It never names a brand's colours,
  faces, prices or furniture. That is the whole reason `pairing` is the literal
  word `brand` rather than two typefaces: the one decision a brand cannot share
  with another brand is left where it belongs.

**`grounds` counts bands, not sections.** A shell carries `masthead-nav` at the
top and `colophon` at the foot, and both are brand-level — settled once for a
site. A recipe restating them would be a second copy of a decision already made,
so the list runs from the first real band to the last. Read the shell's own
`README.md` for the order. Where a pattern fixes its own ground — `cta-band` is
always the brand colour — record that fixed value, so the run reads correctly
top to bottom rather than having a hole in it.

**Keep grounds out of `look`.** `grounds` owns the ground run and `look` carries
the other dials. `ground` is a legal axis on eight patterns, so nothing stops
you writing it in both, and then there are two descriptions of one decision free
to disagree. The gate does not fail this, because failing it would mean holding
an opinion the pattern metadata does not; it is a review question.

**The first sentence of your prose is the menu line.** `recipes/README.md` is
generated from the recipes rather than written, and it takes that sentence
verbatim — so write one, not a fragment. "The long read." tells nobody
anything; "The long read: everything the ordinary article page has, plus a
contents list a reader on a phone can jump from" tells them whether to open the
file.

Then run the gate, which also rewrites the menu:

```
python ci/check_recipes.py            check, and rewrite recipes/README.md
python ci/check_recipes.py --check    what CI runs: fail if the menu is stale
python ci/check_recipes.py --broken   the positive control
```

Commit `recipes/README.md` with your recipe. CI runs `--check` and fails when
the committed menu is not what the recipes produce — the treatment
`compositions/` gets, for the same reason: a menu that has drifted from the
recipes behind it is one an agent will read and believe.

**A second recipe on a shell has to earn it.** A different ground run and a
different close is a different page, and that is the point of this layer. Two
recipes nobody can tell apart is worse than one, because the menu is read in
full and every line on it costs a reader something. Say in the prose what each
one does that the other does not.

## Maintainer setup (once, when the repo is created)

- **Pages**: Settings → Pages → source "GitHub Actions".
- **Main must accept the release workflow's push**: the release job commits
  `INDEX.md` + `LATEST` back to main. If main is protected, add a bypass for
  the Actions token.
- **Seed release**: the initial push includes tag `v0` and `LATEST`
  containing `v0`, so the consumer chain works before the first merge.
