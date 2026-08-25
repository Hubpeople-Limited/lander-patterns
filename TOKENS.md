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

The library used to spread heading emphasis across 600, 650, 700 and 800. It
never worked. `650` cannot exist on a static face at all — CSS font matching
snaps it to 700 — and the one place 600 and 700 sat side by side at the same
size was `masthead-nav`, on brands whose heading face is Georgia or Helvetica.
**Neither has a 600**, so that distinction had never once reached a screen.
Nine of the ten patterns that render more than one heading element already
separate them by size rather than weight, which is what the whole library now
does.

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

**Why they exist.** Across the four sample token sets, seven of the eight
spacing steps are byte-identical and the display sizes are hard-coded in the
patterns. Two brands could pick different colours, different faces and different
corners, and still lay out identically - which is what makes pages on a
multi-tenant platform read as siblings. Colour is the axis brands already vary;
size and rhythm were the two they could not.

**`--type-scale` in practice.** `0.92` is a quieter, more editorial register;
`1.08` to `1.15` reads as a consumer brand shouting. Supported range `0.9` to
`1.2`. Past that the `clamp()` floors stop being sensible at 320px and
headlines held to `16ch` start breaking in the wrong places, so a brand wanting
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

**All five are bare numbers, never lengths.** `--type-scale: 1.1rem` multiplies a length by a length, which makes the whole `calc()` invalid; the declaration drops and the heading falls back to inherited size. Nothing errors, the page just goes flat on every display size at once. `ci/brand_fit.py` checks for this, and it is the only place it can be caught, because a brand's stylesheet is outside this library's CI.

**`--heading-tracking` is the one that reads like a length and must not be one.** The patterns supply the unit, as `calc(-0.02em + var(--heading-tracking, 0) * 1em)`, so the dial is a number like the rest. Written as `--heading-tracking: 0.02em` it becomes an area inside that `calc()`, the declaration drops, and letter-spacing falls back to **`normal`** — not to the `-0.02em` the pattern designed. So the failure is not "my dial did nothing", it is every display heading in the brand losing the tracking it had before the brand touched anything. Verified in a browser, and it is silent.

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
