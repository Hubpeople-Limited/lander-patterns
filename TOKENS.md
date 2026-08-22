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
| `--font-heading`, `--font-body` | The two typefaces (with real fallback stacks) |
| `--space-1` `-2` `-3` `-4` `-5` `-6` `-8` `-12` | The spacing scale. Eight steps, not twelve — the gaps are deliberate, and a step that is not on this list is not defined on any brand |
| `--container-max` | Content max width (commonly `72rem`) |

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

Two optional tokens. **Every other token in this document is one a brand must
define; these two are ones it may.** Both carry a fallback in every use, so a
brand that never mentions them renders exactly as it does today, and a brand
that sets one changes its whole register in one line.

| Token | Default | What it does |
|---|---|---|
| `--type-scale` | `1` | Multiplies display type only - every size in a rule that also sets `--font-heading`. Body copy does not move. |
| `--space-scale` | `1` | Multiplies the spacing ramp, once, where the ramp is defined. Patterns never reference it. |

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

**Both are bare numbers, never lengths.** `--type-scale: 1.1rem` multiplies a length by a length, which makes the whole `calc()` invalid; the declaration drops and the heading falls back to inherited size. Nothing errors, the page just goes flat on every display size at once. `ci/brand_fit.py` checks for this, and it is the only place it can be caught, because a brand's stylesheet is outside this library's CI.

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
