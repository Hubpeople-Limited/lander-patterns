# The token contract — v1

Patterns style themselves **only** through these custom properties. Each brand's
`global.css` defines them in its `:root`; a pattern never hardcodes a colour, a
font, a radius or a shadow. If a pattern genuinely needs a value the contract
cannot express, propose a new token in the PR — do not inline the value.

CI enforces this: colour literals in any syntax (hex, rgb/hsl, oklch and
friends, named colours) and hardcoded `border-radius` / `box-shadow` values
in `pattern.css` fail validation.

**A pattern may define its own properties.** Anything named
`--<pattern-name>-*` belongs to that pattern — a scrim strength, a row index,
an aspect ratio it wants to expose as one dial. They are internal plumbing,
not part of this contract, so they are not listed in `tokens-used` and no
other pattern may reference them. Everything a pattern takes from the brand
comes from the tables below.

## Colour

| Token | Meaning |
|---|---|
| `--color-bg` | Page background |
| `--color-surface` | Card / panel background |
| `--color-surface-soft` | Subtle fill — track backgrounds, alternate rows |
| `--color-text` | Body text (≥ 4.5:1 against `--color-bg` **and against every `--color-surface*`**) |
| `--color-text-soft` | Muted text (still ≥ 4.5:1 on the surface it sits on) |
| `--color-heading` | Headings — **large text only** (≥ 3:1 against `--color-bg`; may equal `--color-text`) |
| `--color-primary` | The brand's action colour — CTAs, key accents |
| `--color-primary-dark` | Darker companion: hover states, small text on light ground |
| `--color-on-primary` | Text/icons on `--color-primary` (≥ 4.5:1 against it) |
| `--color-scrim` | Ground for text laid over a photograph — a dark neutral, not a brand tint |
| `--color-on-scrim` | Text/icons on `--color-scrim` (≥ 4.5:1 against it) |
| `--color-rule` | Hairlines and dividers. **Decorative — brands may set it as soft as they like**, so no pattern may make it the only thing carrying a meaning |
| `--color-focus` | Focus rings (≥ 3:1 against adjacent colours) |

`--color-text` is the one ink that works anywhere the page's own grounds go:
`--color-bg`, `--color-surface` and `--color-surface-soft`. Patterns are told
to fall back to it whenever a heading sits on a card or a panel, so the
guarantee has to cover the ground they land on.

Only three pairs carry a stated ratio: `--color-text` on any page ground,
`--color-on-primary` on `--color-primary`, and `--color-on-scrim` on
`--color-scrim`. **A pattern that lays small text on a coloured ground must
use one of those three.**

`--color-heading` is not one of them. It is free to be a display colour sitting
at the 3:1 large-text bar **against `--color-bg`**, which constrains it twice
over. It may be used only on text that is genuinely large — 24px, or 18.66px
when bold — **and only where the ground is `--color-bg` itself**. A heading
inside a card, a panel or any `--color-surface*` block takes `--color-text`
instead — nothing promises the heading colour against a surface, and two
patterns measured 2.36:1 and 2.71:1 there. Nor over a photograph, however
heavy the scrim: the token tops out at 3.04:1 on a conforming brand, so there
is no headroom for an image to eat.

Both halves of that catch real cases. A 17px question, a 20px tier name and a
16px bold button label all failed the size half; a title over a hero scrim and
two headings on cards failed the ground half. None of them was visible until
`preview/tokens-dark.css` was calibrated to the bar the contract actually
promises. And nothing may be **grounded** on `--color-heading` at all — two
patterns did that before `--color-scrim` existed.

Derived tints are made with `color-mix()` from these tokens, never with new
literals.

## Type and space

| Token | Meaning |
|---|---|
| `--font-heading`, `--font-body` | The two typefaces (with real fallback stacks). **Each must supply 400 and 700** — see *What a face has to supply* below |
| `--space-1` `-2` `-3` `-4` `-5` `-6` `-8` `-12` | The spacing scale. Eight steps, not twelve — the gaps are deliberate, and a step that is not on this list is not defined on any brand |
| `--container-max` | Content max width (commonly `72rem`) |

### What a face has to supply

**Two weights, 400 and 700, and the body face needs a real italic.** That is
the whole requirement, and it is deliberately small: every weight the library
insists on is a family it cannot use.

The library used to spread heading emphasis across 600, 650, 700 and 800. Two
of those four were never a distinction a reader could see, and the third was a
face nobody chose. `650` cannot exist on a static family at all — CSS font
matching snaps it to 700 — and the one place 600 and 700 sat side by side at
the same size was `masthead-nav`, on brands whose heading face is Georgia or
Helvetica. **Neither has a 600**, so that distinction had never once reached a
screen. Nine of the ten patterns that render more than one heading element
already separate them by size rather than weight, which is what the whole
library now does.

### The collapse is not invisible, and 800 is not the same case as 600

**Do not repeat the claim that collapsing to 400/700 changes no pixels. It
does.** Whether it changes any depends entirely on the face in front of you,
which is what makes it easy to get wrong: on Georgia the collapse really is
byte-identical, and Georgia is the house face. Chromium, "Handgloves 0000" at
100px, on the stacks the five sample token sets actually use:

| Stack | 400 | 500 | 600 / 650 | 700 | 800 / 900 |
|---|---|---|---|---|---|
| `Georgia, "Times New Roman", serif` | 792.688 | 792.688 | 912.844 | 912.844 | 912.844 |
| `"Helvetica Neue", Helvetica, Arial` | 778.375 | 778.375 | 817.047 | 817.047 | **934.094** |
| `system-ui` / `-apple-system` (Segoe UI here) | 764.703 | **786.188** | **786.188** | **813.281** | 852.062 |
| `"Lander Display Fixture"` (`preview/tokens-display.css`) | 1125.609 | 1125.609 | 1296.250 | 1296.250 | 1296.250 |

The fourth row is why the first three were not enough. It is a simulated face —
`@font-face` with `size-adjust: 142%` over a `local()` chain, so nothing is
fetched and nothing can silently fail to arrive — and until it existed, every
row in this table was a face this library had been designed on. Its regular is
**42% wider than Georgia's** at the same size, and its line box 57% taller,
which is the spread a real brand's display face can put between itself and the
house one.

Two things fall out of that table, and both are visible changes on a real
brand:

**`800 → 700` on display type changes the family member.** Arial ships a real
weight above Bold, and `font-weight: 800` selects **Arial Black** — 934.094
against 817.047, **14.3% wider**. Three display rules make that change and it
is deliberate:

| Rule | What a brand with a real 800 sees |
|---|---|
| `.heading-block-title` | Bold rather than Black; the headline goes 3 lines to 2 at 360px |
| `.testimonial-grid-quote p` | the quote goes 3 lines to 2 at 360, 768 and 1280 |
| `.testimonial-carousel-quote p` | the quote goes 4 lines to 3 at 1280 |

The alternative is worse than the reflow. 800 is not a weight the contract can
ask for: present on Arial, absent on Georgia, and absent from most of what a
partner will hand over — so one rule draws three different things and the
pattern has no way to know which.

**`600 → 700` is a no-op on both heading stacks and is not one on Segoe UI**,
which has a genuine Semibold: 786.188 to 813.281, **3.4% wider**. So the rules
that carry 600 are supporting text on the *body* face, and collapsing them
widens a label by a few pixels on a Segoe-UI brand. Nothing reflows and no
page grows taller; the labels are simply drawn in the weight they were asking
for.

**No pattern declares a weight above 400 other than 700.** That is the whole
rule, and it is checkable by reading `font-weight` in any `pattern.css`. Two
supporting rules — `.heading-block-eyebrow` and `.testimonial-grid-flag` —
held 800 while the display type beside them went to 700, which on an Arial
stack drew a 13px eyebrow heavier than the 57px headline above it. Both are
700.

Below 400 the argument does not apply and the values stay: eight rules of
body-face supporting text sit at 500, and `stat-rows` exposes its own
`--stat-rows-weight` at 300 for its numerals. A face with neither falls to 400,
which is the reading those rules want, and nothing in the library asks a reader
to tell 500 from 600 — the pairs that sit side by side are 500 against 700.

**A weight the face does not have is not an error.** The browser synthesises
it by smearing the outline, which at display sizes fills in the counters — the
holes in *a*, *e*, *o* — and a headline turns into a black bar. Nothing warns
you. It simply looks cheap, and it looks cheap only on the brands whose face
is missing the weight, so it survives review on the machine it was built on.

**Measures on display type are `em`, never `ch`.** `ch` is the advance width
of *zero in the face actually used*, at the weight actually used. Georgia Bold
is `0.7012em`, Arial Bold `0.5562em` — a 26% divergence between two of this
library's own sample brands, which is why one `max-width: 16ch` headline
rendered on two lines for some brands and three for others. `em` removes the
typeface and keeps the type scale. **Body measures stay in `ch`**, because
there `ch` is doing the job it is for: holding a line to a character count.

**The conversion is `0.625em` per `ch`, and it is not a translation.** No em
value can equal a character count on every face at once — that is the whole
point of moving — so each of these measures is a new number that agrees across
faces rather than matching any one of them:

| Pattern | Measure | Ratio |
|---|---|---|
| `anchored-split`, `claim-stack` | `18ch` → `11.25em` | 0.625 |
| `opener-split` | `14ch` → `8.75em` | 0.625 |
| `quote-feature` | `20ch` → `12.5em` | 0.625 |
| `hero-centred` | `15ch` → `9.4em` | 0.6267 (9.375 rounded) |
| `hero-stated` | `16ch` → `10.75em` | **0.6719** |

**`hero-stated` is deliberately 7.5% wider than the ratio**, and nothing else
records that, so it is recorded here: at `10em` its headline broke to three
lines across the sample brands and the shape of the pattern is a two-line
statement. `10.75em` is the value that holds two lines above phone width on
every sample face this library was designed against. Do not "correct" it back
to `10em`.

**That is a narrower claim than the one this paragraph used to make**, and the
correction is worth keeping rather than quietly rewriting. It said `10.75em`
holds two lines "on every sample face", which was true of the four faces that
existed when it was written and is not a property of the measure. Added as a
fifth sample brand, `preview/tokens-display.css` renders the same headline on
**four** lines at 1280 — the measure resolves to the same 774.0px it does
everywhere, and the face simply puts fewer words in it. A measure in `em`
guarantees an identical width, never an identical line count, and no measure
of any kind can guarantee the second. Sizing a pattern's shape to a line count
is the thing to stop doing.

Two patterns reflow on a Georgia-stack brand as a result. `hero-stated` is the
one the ratio was chosen for. The other is `quote-feature`, whose measure goes
from 610.3px to 544px at 1280 — 10.9% narrower, the quote 3 lines to 4, and
the section about 54px taller. That is the cost of a measure that means the
same thing on every face, and it is noted in that pattern's README.

**`ci/check_measures.py` is what holds all of that true.** It renders every
display measure on all five sample brands and requires the resolved widths to
be the same number, which they now are: **0.00% spread**. Re-rendered in the
`ch` form the same six measures spread **79.0%** across the five, and **26.1%**
across the four that ship a system stack — the figure quoted above, reproduced
from the code rather than from this document. A display measure written in
`ch` fails that gate outright.

## The aesthetic dials

Set per brand to make the same patterns read differently — soft vs sharp, flat
vs shadowed:

| Token | Meaning |
|---|---|
| `--btn-radius` | Button corners |
| `--card-radius` | Card / panel / image corners |
| `--card-shadow` | Card elevation (`none` on flat brands) |
| `--card-border` | Card edge (often a `color-mix` hairline) |
| `--chip-radius` | Chips and small labels |
| `--logo-height` | Header logo size |

## The page's furniture

Two lengths, measured rather than derived. **A pattern cannot see the page it
lands in**, and a full-viewport section has to know how much of the viewport is
already spoken for before it can claim the rest.

| Token | Default | What it is |
|---|---|---|
| `--page-header-height` | `9.5rem` | The rendered height of the site header sitting above the opener, in normal flow |
| `--page-footer-height` | `12.5rem` | The rendered height of the site footer the platform puts under the page |

**The defaults are this library's own furniture, rounded up.** `masthead-nav`
renders between 77px and 145px across the five sample token sets at the widths
CI measures — a header height is a size in a particular typeface, the same way
every entry in `check_phone.py`'s baseline is — so `9.5rem` is the tallest of
those with a little over. `12.5rem` covers a platform footer measured at
165.8px on a desktop and 196.8px on a phone. Both are a starting point for a
brand nobody has measured, not a substitute for measuring.

They are **two tokens rather than one total on purpose**, because the two
patterns that read them need different subsets of it. `hero-overlay` opens a
page that continues, so only the header is inside its first viewport and it
subtracts only that. `hero-squeeze` is `whole-page: yes` — its promise is that
the *page* fits one viewport — so it subtracts both. A single
`--page-furniture` total could not serve both, and a per-pattern
`--hero-squeeze-below` beside `--hero-squeeze-above` would be four properties
naming two facts, with the names still not saying what to measure.

### Measure them, never derive them

The old guidance said to work the header out from `--logo-height`. Derivation
is what put this wrong on a live page: a brand with a 70px logo set the
allowance to 5.75rem and the header rendered at 103px — an 11px error, on top
of a whole footer nobody had subtracted at all. **Open the page and read the
two numbers off it.** In the browser's console, on a real page of the brand:

```js
(() => {
  const px = el => el ? Math.round(el.getBoundingClientRect().height * 10) / 10 : 0;
  const head = px(document.querySelector('header'));
  const foot = px(document.querySelector('footer'));
  const over = document.documentElement.scrollHeight
             - document.documentElement.clientHeight;
  console.log(innerWidth + 'x' + innerHeight + '  header ' + head
            + '  footer ' + foot + '  total ' + (head + foot)
            + '  page overflows by ' + over + 'px');
})()
```

**Do it at more than one width, and take the largest total you see.** The
furniture is not a step between "phone" and "desktop": it has a hump in the
middle, where a menu row has wrapped but the desktop layout has not yet
arrived. On the live page this was measured on, in Chromium:

| Viewport width | Header | Footer | Total |
|---|---|---|---|
| 320 – 480 | 125 | 196.8 | **321.8** |
| 640 | 132.3 | 165.8 | 298.1 |
| 768 | 143.1 | 165.8 | 308.9 |
| 900 | 151 | 165.8 | **316.8** |
| 1024 and up | 103 | 165.8 | 268.8 |

The tallest header on that brand is at 900px and the tallest total is on a
phone. Reading either number off a laptop alone gives the smallest of the
three, which is the one direction that scrolls.

### The two directions are not equally bad

**Too large costs a band of page background under the footer. Too small
scrolls**, and on `hero-squeeze` scrolling is the single thing the pattern
exists to prevent. So round up, and where the spread is worth reclaiming,
write it as two states rather than splitting the difference:

```css
:root {
  --page-header-height: 151px;   /* the hump at 900px */
  --page-footer-height: 197px;   /* the phone footer */
}
@media (min-width: 64em) {
  :root {
    --page-header-height: 103px;
    --page-footer-height: 166px;
  }
}
```

Those four numbers came off the table above. On that brand they give an exact
fit at 1280×800 and 26px to spare at 390×844, and the page does not scroll at
any width between.

### Where nothing sits above

`0px` is a legitimate value for either — a page served with no header, or an
opener that is genuinely the first thing in the document. It is the one case
where a zero is meant, and it has to be written rather than left to the
default.

### The names that used to do this

`--hero-squeeze-above` and `--hero-overlay-above` are **retired**. They were in
each pattern's private `--<pattern-name>-*` namespace, which is this document's
word for internal plumbing, and they carried a header height only. Setting
either one now does nothing. Replace it with `--page-header-height`, and on a
`hero-squeeze` page add `--page-footer-height` as well — a brand that carries
the old property forward and stops there still scrolls, by whatever its footer
measures.

## Dials

Five optional tokens. **Every other token in this document is one a brand must
define; these five are ones it may.** All carry a fallback in every use, so a
brand that never mentions them renders exactly as it does today, and a brand
that sets one changes its whole register in one line.

| Token | Default | What it does |
|---|---|---|
| `--type-scale` | `1` | Multiplies display type only - every size in a rule that also sets `--font-heading`. Body copy does not move. |
| `--space-scale` | `1` | Multiplies the spacing ramp, once, where the ramp is defined. Patterns never reference it. |
| `--heading-leading` | `1` | Multiplies the line-height of display type only. Body copy does not move. |
| `--heading-tracking` | `0` | **Adds** to the letter-spacing of display type, in em. Not a multiplier. |
| `--weight-display` | `700` | The weight display type is set in. A face with no 700 wants this lower, not faux-bold. |

**They are not all the same kind of number, and the difference matters.**
`--type-scale`, `--space-scale` and `--heading-leading` are **multipliers**:
`1` is the identity, `0` would blank the page, and a negative is invalid.
`--heading-tracking` is an **offset**: `0` is the identity, and negative is
the ordinary case — 40 of the 41 tracking values in this library are already
negative, because display type is drawn tight. `--weight-display` is neither;
it is a weight, and the only one of the five that is not `0` or `1` at rest.

Tracking is additive precisely *because* the values are negative. A multiplier
on a negative number runs backwards — turning the dial up would tighten — and
it can never cross zero, so a geometric face that wants a little air would
have no reachable value at all. Additive keeps the designed differences too:
`-0.035em` stays `0.015em` tighter than `-0.02em` at every setting.

**`--heading-leading` in practice.** Supported range `0.95` to `1.15`. Not
`0.9` like the other multipliers: the tightest leading shipped is `1.02`, and
`1.02 × 0.9` is `0.918`, where ascenders and descenders overlap outright. Past
`1.15` the `1.3` card headings reach `1.5`, and the dial has started changing
card heights rather than type.

**`--heading-tracking` in practice.** Supported range `-0.02` to `0.04`, in em,
**added** not multiplied. At `-0.02` the `-0.035em` quotes reach `-0.055em`,
where a tight face touches; at `+0.04` a headline held to `10.75em` gains
enough advance to lose a word a line, so `text-wrap: balance` balances a
different shape. A face drawn loose wants a negative value here, a geometric
face drawn tight a positive one.

**`--weight-display` in practice.** Supported range `400` to `800`, and only to
a weight the face actually has. This is the dial for a face that has no 700:
set it to what the family ships rather than letting the browser synthesise one.

**Why they exist.** Across the five sample token sets, seven of the eight
spacing steps are byte-identical and the display sizes are hard-coded in the
patterns. Two brands could pick different colours, different faces and different
corners, and still lay out identically - which is what makes pages on a
multi-tenant platform read as siblings. Colour is the axis brands already vary;
size and rhythm were the two they could not.

**`--type-scale` in practice.** `0.92` is a quieter, more editorial register;
`1.08` to `1.15` reads as a consumer brand shouting. Supported range `0.9` to
`1.2`. Past that the `clamp()` floors stop being sensible at 320px and
headlines held to `10.75em` start breaking in the wrong places, so a brand wanting
something outside it wants a different pattern rather than a bigger number.

It multiplies the whole `clamp()`, floor and ceiling together, so the
responsive behaviour is preserved rather than flattened.

**The contrast guarantees are stated across this range, not just at `1`.**
`--color-heading` carries 3:1 and is therefore valid only on large text, so
every pattern using it holds a `clamp()` floor that still clears 24px at
`0.9` — 28px, not the 24px that would clear it only on brands that never
touched the dial. CI enforces that, and it is the reason the range is a
documented number rather than a suggestion.

**`--space-scale` in practice.** It is applied by the brand, not the pattern -
each step is defined in terms of it, once:

```css
:root {
  --space-scale: 1;
  --space-1: calc(0.25rem * var(--space-scale, 1));
  --space-2: calc(0.5rem  * var(--space-scale, 1));
  /* and so on through --space-12 */
}
```

Supported range `0.85` to `1.2`: `0.85` is dense and utilitarian, `1.2` airy
and premium. Below `0.85` the 44px target sizes stop having room around them,
which is an accessibility floor rather than a taste one.

**All five are bare numbers, never lengths.** `ci/brand_fit.py` checks for this, and it is the only place it can be caught, because a brand's stylesheet is outside this library's CI.

**What a unit costs is different on each dial, and none of them says so out loud.** Measured in Chromium:

| Written as | What happens |
|---|---|
| `--type-scale: 1.1rem` | length × length is an area, every `calc()` reading it is invalid and drops. `font-size` is inherited, so every display size collapses to whatever it sits inside, on every viewport at once |
| `--space-scale: 1.2px` | the same, in the ramp. `padding`, `margin` and `gap` are **not** inherited, so they fall to `0` and the page loses every gap it had |
| `--heading-leading: 1.1rem` | **valid CSS.** Number × length is a length, so nothing drops and nothing warns — `calc(1.02 * 1.1rem)` computes to `17.952px`, a fixed leading that no longer tracks font-size and is inherited downward. A 40px heading and the 20px line under it are both set on a 17.952px body, and the text overlaps itself |
| `--heading-tracking: 0.02em` | an area inside `calc(-0.02em + var(--heading-tracking, 0) * 1em)`, so the declaration drops and letter-spacing falls back to **`normal`** — not to the `-0.02em` the pattern designed. The brand loses tracking it never set |
| `--weight-display: 700px` | `font-weight` is inherited, so the declaration is invalid at computed-value time and the element takes its **ancestor's** weight, not the pattern's `700`. Probed with an ancestor at 300, the heading computes 300 — on a real brand that is body weight, so every display heading goes bold to regular |

**The brand's own indirection is fine; its fallback is not exempt.** `--type-scale: var(--brand-density, 1)` is a reasonable thing to write and CI leaves it alone. `--type-scale: var(--brand-density, 1.1rem)` is the same trap one level down, because the fallback is what ships whenever the brand's property is not set — and an **empty** value (`--heading-tracking: ;`) substitutes nothing at all, which is not the same as leaving the dial alone. CI reads the fallback for both.

**Set at most one of them away from `1` at a time, to begin with.** Both at
once compounds, and a brand at `1.15` type on `1.2` space is not a bolder
brand, it is a broken one.

## Motion

Patterns whose metadata declares `motion: subtle` or `motion: expressive` may
use `--transition-fast` (~150ms) and `--transition-slow` (~400ms), always inside
the brand's `prefers-reduced-motion` guard. Nothing in any pattern moves by
itself for more than five seconds — auto-advancing carousels and marquees are
not accepted, because the pause control they legally require cannot be built
without JavaScript.

**A transition token is a duration and nothing else.** `--transition-fast: 150ms`,
not `150ms ease`. The pattern supplies the timing function, because only the pattern
knows whether a thing should ease out, ease in or move linearly.

This is not a style preference, it is the difference between motion and no motion. CSS
allows one timing function per transition item, so a token that already carries `ease`
turns the house form `var(--transition-fast) ease-out` into `150ms ease ease-out` -
**invalid, and the whole declaration is dropped**. The animation does not degrade, it
disappears, and nothing on the page looks broken. One of the four sample token sets
shipped the easing and sixteen transitions across five patterns were silently dead on
it. `ci/lint.py` now holds the token sets to this.


## Platform furniture tokens

The platform fills these per brand and per page. They are the **only** `{{ }}`
values allowed in a pattern, spelled exactly as below (a numbered middle segment
— `{{logo.0.src}}`, `{{login.0.url}}`, `{{join.0.text}}` — is also valid for the
logo, login and join families). This table is a vendored copy of the platform's
token registry; CI validates against it.

| Token | What the platform puts there |
|---|---|
| `{{menu.navigation}}`, `{{menu.navigation.default}}`, `{{menu.footer}}` | The menus |
| `{{footerLinks.antiSlaveryPolicyUrl}}`, `{{footerLinks.cookiesUrl}}`, `{{footerLinks.privacyPolicyUrl}}`, `{{footerLinks.termsAndConditionsUrl}}` | The four footer links |
| `{{logo.src}}`, `{{logo.alt}}` | Brand logo |
| `{{login.url}}`, `{{login.text}}`, `{{join.url}}`, `{{join.text}}` | Login and join CTAs |
| `{{canonicalPage}}`, `{{favicon}}` | Canonical URL and favicon |
| `{{pageTitle}}`, `{{metaDescription}}`, `{{metaKeywords}}` | Page metadata |

Never invent a token — there is no `{{heroImage}}`, no `{{description}}`, no
`{{keywords}}`; unknown `{{ }}` values ship as visible breakage on a live page.
Images in patterns are **attribute slots** (`src="slot:hero-image"`), filled at
build time with a real CDN URL sized for the slot.
