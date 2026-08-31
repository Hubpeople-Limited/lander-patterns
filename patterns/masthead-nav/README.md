# masthead-nav

**What it is and when to use it.** The site header: brand mark, primary navigation, login and join.
**Most of its markup is not in this pattern.** The platform expands `{{menu.navigation}}` into a
`<ul class="canvas-navigation-menu">` with `has-submenu` children and nested
`canvas-navigation-submenu` lists, and ships **no CSS at all** for it — unstyled it is stacked browser
bullets. This is the chassis around that placeholder and the stylesheet that makes the generated
classes behave: page furniture, chosen once for a site. Not for a page that already has a header, or
a brand on the self-contained `{{menu.navigation.default}}` menu.

**What it needs.** The brand's logo file, the menu items configured on the platform, and two words in
the brand's language: `menu-label` on the button, `close-label` for that same button while the menu is
showing. Both are needed on both `toggle` rungs. `home-url` is where the mark links.

**The logo is sized by its height, and the width follows.** Set the `<img>` `width` and `height` to the
file's own pixel size — they fix the ratio, nothing more — and let `--logo-height` decide how tall it
renders. **Never put the height back to `auto` under a `max-height`.** Most brand marks are SVGs with a
`viewBox` and no dimensions: a ratio and no intrinsic size, so two ceilings leave one nothing to resolve
against and it renders 0×0 — which it did below `60rem` until `v7`, on every phone and tablet built on
it. `object-fit: contain` keeps it undistorted once the small-screen width cap bites, and the home link
holds its own 44px floor there, since `--logo-height` may be set under a thumb. `ci/check_logo.py`
renders the shapes real brands ship and fails a mark not drawn at `--logo-height`.

**Pairing.** No neighbours in the ordinary sense, so `pairs-with` is empty. It is a `component`, not a
`section`, on purpose: `ci/check_page.py` judges the first *section* against the fold, so typing this as
a section would take a full-viewport hero out of that check. State the header's ground only where it
differs from the opener's.

**Login and join live inside the disclosure.** They lead the drawer and end the bar above `60rem`. Do
not move them into the bar at small widths: an open drawer covers the page, so a control outside it is
behind the scrim for as long as somebody is reading the menu. `ci/lint.py` fails a `{{join.url}}` or
`{{login.url}}` left outside the `<details>`. An open drawer also pins the bar on both `sticky` rungs,
or a scroll parts it from the button that shuts it.

**Brand adaptability.** Eight axes, all real modifier classes. Below `60rem` means the small-screen
arrangement; above it the menu is a row in the bar.

| Axis | Rungs | What it moves |
|---|---|---|
| `ground` | `plain`, `soft`, `brand` | the ladder. `--brand` inverts the join control to the `--color-on-primary` on `--color-primary` pair the contract states a ratio for |
| `layout` | `inline`, `centred` | `--inline` puts mark, menu and controls on one row; `--centred` gives the mark its own line with the menu centred beneath and the controls in the corner |
| `menu` | `drawer`, `panel`, `row` | what the menu does below `60rem`. `--drawer` is what a phone expects: a `min(20rem, 82vw)` panel over a dimmed page, full height, scrolling on its own, the button in its top corner. `--panel` is a lighter full-width sheet out of the header, for two or three short labels. `--row` drops the button and runs the items in a scrolling row, submenus on beside their parent |
| `sticky` | `static`, `pinned` | `--pinned` holds the bar at the top of the viewport and compacts its padding above `60rem`. Worth around 22% quicker navigation and a strip of every screen, so it suits `--inline` far better than two-row `--centred` |
| `menu-align` | `menu-start`, `menu-centre`, `menu-end` | which edge the items inside the sheet are set against. It does not move the sheet, and is inert on `--row`. `menu-centre` drops the submenu's rule, which has no correct side once centred |
| `menu-side` | `side-start`, `side-end` | which side the menu button sits on, and the side the drawer slides in from. One axis, not two, so the button cannot end up on the scrim beside a sheet on the other edge. Inert on `--row` |
| `toggle` | `labelled`, `icon` | whether the menu button below `60rem` carries its word beside the three bars. Inert on `--row`, which has no button |
| `edge` | `rule`, `shadow`, `flush` | the bar's bottom edge — a hairline on `--masthead-nav-edge`, no line and `--card-shadow` under the bar instead, or neither |

There is deliberately **no rung hiding the menu behind a button at desktop width**: Nielsen Norman
Group measured it missed almost twice as often, 2.5 seconds slower and rated 15% harder. Use
`--centred` for a quieter bar; `--font-heading` on the items is most of what makes the bar look like
the brand.

**Prefer `labelled`.** A word beside the bars is found faster and more often than bars alone, which are
recognised only once somebody looks for them — so `--labelled` is the safer default and `--icon` a
deliberate trade for a brand with a short bar, a wide mark and a returning audience. Neither rung
changes what is announced: both words stay real text and `--icon` clips the live one with `clip-path`,
so a screen reader, voice control and machine translation still have it; an `aria-label` would serve
none of the three. The button keeps a square `--masthead-nav-tap` floor there, or without the word it
falls to the icon's width, under a thumb.

**`edge` costs no height.** Every rung keeps the same `1px` border and changes only what paints it, so
`--page-header-height` holds and the bar renders identically tall on all three. `--shadow` reads as a
floating bar and suits `sticky=pinned`; `--flush` is for an opener carrying its own ground.

**No script, at any width.** The menu is a native `<details>`/`<summary>`, so the browser supplies the
expanded state, keyboard operation and focus ring. A shut drawer is `visibility: hidden`, out of the
tab order and find-in-page. Above `60rem` the tray is forced open by **two** declarations (`display`,
and `::details-content`).

**What `behaviours: drawer` adds.** `Escape` closes the drawer and returns focus to the button, a press
on the backdrop closes it, and the page behind holds still. Without it the drawer still opens, closes,
slides, scrolls and takes the keyboard. It acts only while the tray is fixed, so `--panel`, `--row` and
anything above `60rem` leave the hook inert.

**Three things the generated markup forces.** *A parent item with both children and a URL comes through
as two `<li>` entries* — one plain link, one `has-submenu` — so the label appears twice; the repair is
in the menu data. *The generated `<ul>` cannot carry `role="list"`*, so Safari drops the item count once
the markers go. *The `title` attribute is not escaped*, so check punctuated labels before a brand goes
live.
