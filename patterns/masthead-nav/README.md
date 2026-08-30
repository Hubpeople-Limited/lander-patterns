# masthead-nav

**What it is and when to use it.** The site header: brand mark, primary
navigation, login and join. **Most of its markup is not in this pattern.** The
platform expands `{{menu.navigation}}` into a `<ul class="canvas-navigation-menu">`
with `<li class="has-submenu">` children and nested `<ul class="canvas-navigation-submenu">`,
and ships **no CSS at all** for any of it — unstyled, that menu renders as stacked
browser bullets over everything. This is the chassis around the placeholder plus
the stylesheet that makes the generated classes behave. It is page furniture,
chosen once for a site. Do not use it where the page already has a header, or
where the brand chose the self-contained `{{menu.navigation.default}}` menu.

**What it needs.** The brand's logo file, the menu items configured on the platform,
and two words in the brand's language: `menu-label` on the button, `close-label` for
that same button while the menu is showing. `home-url` is where the mark links,
usually `/`. Set the `<img>` `width` and `height` to the logo file's own pixel size
— they only fix its aspect ratio, and `--logo-height` decides how tall it renders.

**Pairing.** No neighbours in the ordinary sense, so `pairs-with` is empty. It is
a `component`, not a `section`, on purpose: `ci/check_page.py` judges the first
*section* against the fold, and typing this as a section would take a full-viewport
hero out of that check. State the header's ground only where it differs from the
opener's, or the page checker reports two sections running on.

**Login and join live inside the disclosure.** They lead the drawer, above the menu
items, and sit at the end of the bar above `60rem`. Do not move them out into the
bar at small widths: an open drawer covers the whole page, so a control outside it
is behind the scrim for exactly as long as somebody is reading the menu — which is
when they most want it. `ci/lint.py` fails a `{{join.url}}` or `{{login.url}}` left
outside a `<details>` the same pattern ships. An open drawer also pins the bar on
both `sticky` rungs: the drawer is fixed to the viewport and the button that shuts
it is not, so a scroll would otherwise part them and strand the reader.

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

`--drawer` is what a phone expects: `min(20rem, 82vw)` wide, full height, scrolling
on its own if the menu is long, with the button on its top corner swapping
`menu-label` for `close-label`. `--panel` is lighter and right for two or three
short labels. On `--row` a submenu runs on beside its parent rather than nesting.

A pinned bar is worth around 22% quicker navigation, and every pixel of it is page
nobody can see — so it suits `--inline` far better than `--centred`, which is two
rows tall before it starts.

There is deliberately **no rung hiding the menu behind a button at desktop width**:
Nielsen Norman Group measured hidden desktop navigation as missed almost twice as
often, 2.5 seconds slower and rated 15% harder. Use `--centred` for a quieter bar.
`--logo-height` carries a fallback; `--font-heading` on the menu items is most of
what makes the bar look like the brand.

**No script, at any width.** The menu is a native `<details>`/`<summary>`, so the
browser supplies the expanded state, keyboard operation and focus ring. A shut
drawer is `visibility: hidden`, keeping it out of the tab order and find-in-page.
Above `60rem` the tray is forced open by CSS and **two declarations are needed**
(`display` on the tray, `content-visibility` on `::details-content`).

**What `behaviours: drawer` adds.** `Escape` closes the drawer and returns focus to
the button, a press on the backdrop closes it, and the page behind holds still while
it is open. Without the bundle all three are absent and the drawer still opens,
closes, slides, scrolls and takes the keyboard. It acts only while the tray is fixed
to the viewport, so on `--panel`, `--row` and above `60rem` the hook is inert.

**Three things the generated markup forces.** *A parent item with both children
and a URL comes through as two `<li>` entries* — one plain link, one `has-submenu`
carrying the children — so the label appears twice; the repair is in the menu data.
*The generated `<ul>` cannot carry `role="list"`*, so Safari drops the item count
once the markers go. *The `title` attribute is not escaped*, so check labels with
punctuation before a brand goes live.
