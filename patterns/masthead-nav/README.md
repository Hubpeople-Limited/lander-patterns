# masthead-nav

**What it is and when to use it.** The site header: brand mark, primary
navigation, login and join. **Most of its markup is not in this pattern.** The
platform expands `{{menu.navigation}}` into a `<ul class="canvas-navigation-menu">`
with `has-submenu` children and nested `canvas-navigation-submenu` lists, and ships
**no CSS at all** for any of it — unstyled it is stacked browser bullets. This is
the chassis around that placeholder and the stylesheet that makes the generated
classes behave: page furniture, chosen once for a site. Not for a page that already
has a header, or a brand on the self-contained `{{menu.navigation.default}}` menu.

**What it needs.** The brand's logo file, the menu items configured on the platform,
and two words in the brand's language: `menu-label` on the button, `close-label` for
that same button while the menu is showing. `home-url` is where the mark links,
usually `/`.

**The logo is sized by its height, and the width follows.** Set the `<img>` `width`
and `height` to the file's own pixel size — they fix the ratio and nothing else — and
let `--logo-height` decide how tall it renders. **Never put the height back to `auto`
under a `max-height`.** Most brand marks are SVGs exported with a `viewBox` and no
dimensions: a ratio and no intrinsic size, so two ceilings leave one nothing to
resolve against and it renders 0×0. That is what this pattern did below `60rem` until
`v7`, and the mark was absent from every phone and tablet built on it.
`object-fit: contain` keeps it undistorted once the small-screen width cap bites, and
the home link holds a 44px floor of its own there, since `--logo-height` may be set
under a thumb's size. `ci/check_logo.py` renders the shapes real brands ship and
fails a mark not drawn at `--logo-height`.

**Pairing.** No neighbours in the ordinary sense, so `pairs-with` is empty. It is a
`component`, not a `section`, on purpose: `ci/check_page.py` judges the first *section*
against the fold, and typing this as a section would take a full-viewport hero out of
that check. State the header's ground only where it differs from the opener's.

**Login and join live inside the disclosure.** They lead the drawer and sit at the
end of the bar above `60rem`. Do not move them into the bar at small widths: an open
drawer covers the page, so a control outside it is behind the scrim for exactly as
long as somebody is reading the menu. `ci/lint.py` fails a `{{join.url}}` or
`{{login.url}}` left outside the `<details>`. An open drawer also pins the bar on
both `sticky` rungs, or a scroll parts it from the button that shuts it.

**Brand adaptability.** Six axes, all real modifier classes. Below `60rem`
means the small-screen arrangement; above it the menu is a row in the bar.

| Axis | Rungs | What it moves |
|---|---|---|
| `ground` | `plain`, `soft`, `brand` | the ladder. `--brand` inverts the join control to the `--color-on-primary` on `--color-primary` pair the contract states a ratio for |
| `layout` | `inline`, `centred` | `--inline` puts mark, menu and controls on one row; `--centred` gives the mark its own line with the menu centred beneath and the controls in the corner |
| `menu` | `drawer`, `panel`, `row` | what the menu does below `60rem` — a side panel over a dimmed page, a full-width sheet out of the header, or no button and a scrolling row of items |
| `sticky` | `static`, `pinned` | `--pinned` holds the bar at the top of the viewport and compacts its padding above `60rem` |
| `menu-align` | `menu-start`, `menu-centre`, `menu-end` | which edge the items inside the sheet are set against. It does not move the sheet, and is inert on `--row`. `menu-centre` drops the submenu's rule, which has no correct side once centred |
| `menu-side` | `side-start`, `side-end` | which side the menu button sits on, and the side the drawer it opens slides in from. One axis, not two, so the button cannot end up on the scrim beside a sheet on the other edge. Inert on `--row`, which has no button |

`--drawer` is what a phone expects: `min(20rem, 82vw)` wide, full height, scrolling on
its own, the button in its top corner swapping `menu-label` for `close-label`. `--panel`
is lighter, for two or three short labels. On `--row` a submenu runs on beside its parent.

A pinned bar is worth around 22% quicker navigation, and every pixel of it is page
nobody can see — so it suits `--inline` far better than two-row `--centred`.

There is deliberately **no rung hiding the menu behind a button at desktop width**:
Nielsen Norman Group measured hidden desktop navigation as missed almost twice as often,
2.5 seconds slower and rated 15% harder. Use `--centred` for a quieter bar.
`--font-heading` on the menu items is most of what makes the bar look like the brand.

**No script, at any width.** The menu is a native `<details>`/`<summary>`, so the
browser supplies the expanded state, keyboard operation and focus ring. A shut drawer
is `visibility: hidden`, out of the tab order and find-in-page. Above `60rem` the tray
is forced open by **two** declarations (`display`, and `::details-content`).

**What `behaviours: drawer` adds.** `Escape` closes the drawer and returns focus to
the button, a press on the backdrop closes it, and the page behind holds still. Without
the bundle all three are absent and the drawer still opens, closes, slides, scrolls and
takes the keyboard. It acts only while the tray is fixed, so `--panel` and `--row` and
anything above `60rem` leave the hook inert.

**Three things the generated markup forces.** *A parent item with both children and
a URL comes through as two `<li>` entries* — one plain link, one `has-submenu` — so
the label appears twice; the repair is in the menu data. *The generated `<ul>` cannot
carry `role="list"`*, so Safari drops the item count once the markers go. *The `title`
attribute is not escaped*, so check punctuated labels before a brand goes live.
