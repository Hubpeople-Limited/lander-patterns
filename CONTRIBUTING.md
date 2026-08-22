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
| `type` | `component`, `section` or `page` |
| `needs` | The real content this consumes. It gates use: no material, wrong pattern. Say "real" and mean it |
| `pairs-with` | Patterns that read well after this one. Not page furniture — `cta-sticky` belongs to the page, decided once |
| `avoid-with` | Patterns that must not both appear on one page, or `none` — two image-led card runs, a full-screen finale and a fixed bar. It is the strong reading on purpose: follow it and the weaker adjacency problems cannot arise either. Mutual by nature, so CI checks both sides name each other. A constraint that is only ever about *neighbours* ("not directly above this") is prose in the README, not an edge here |
| `one-per-page` | `yes` if a page may hold at most one. Two heroes or two sticky bars are a mistake, not a layout choice. This is where cardinality lives, not in `avoid-with`; where two patterns are **alternatives**, set it on both and say which to pick when in both READMEs |
| `tokens-used` | The contract tokens your `pattern.css` references. Your own `--<pattern-name>-*` properties are yours and are ignored |
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
  both are fine.
- Every pattern styles itself through at least one token — a markup-only
  pattern with an empty stylesheet is not accepted.
- If the pattern moves (`motion: subtle`/`expressive`), keep every animation
  and transition inside the reduced-motion guard pattern shown in existing
  patterns, and nothing auto-moves for more than five seconds.

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
- renders every pattern against three sample token sets — soft-rounded,
  sharp-flat, and `dark`, a hostile brand whose `--color-heading` sits at the
  3:1 large-text bar and whose surfaces are dark. Read `dark` as a test rather
  than a third style: it exists to fail patterns that ground text on tokens
  the contract does not guarantee. The pages attach to your pull request as
  the `pattern-previews` artifact, so you see all three before anyone merges;
  on merge they publish to the repo's Pages site.

A red check names the file and the rule. Fix and push again — nothing merges
red.

## Behaviours — platform-delivered JavaScript (gated)

Patterns never carry a `<script>`; that rule does not move. But the library
has a second half: **`lib/hub.js`, a single behaviour bundle the platform
itself will deliver to served pages** — the same way it already injects its
own navigation script. Markup opts in with `data-hub-module="<name>"`
attributes, which are **inert data attributes until that delivery exists**,
so a pattern can ship its hooks today and light up later with no change.

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


## Maintainer setup (once, when the repo is created)

- **Pages**: Settings → Pages → source "GitHub Actions".
- **Main must accept the release workflow's push**: the release job commits
  `INDEX.md` + `LATEST` back to main. If main is protected, add a bypass for
  the Actions token.
- **Seed release**: the initial push includes tag `v0` and `LATEST`
  containing `v0`, so the consumer chain works before the first merge.
