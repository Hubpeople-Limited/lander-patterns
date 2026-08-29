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

**Brand adaptability.** Five axes, all real modifier classes.
- `ground=plain|soft|brand` — the ladder. `--brand` inverts the join control to the
  `--color-on-primary` on `--color-primary` pair the contract states a ratio for.
- `layout=inline|centred` — `--inline` puts mark, menu and controls on one row.
  `--centred` gives the mark its own line with the menu centred beneath it and
  the controls parked in the corner, which is the editorial reading.
- `menu=drawer|panel|row` — what the menu does below `60rem`. **`--drawer`** is
  what a phone expects: a panel fixed to the inline-end edge, `min(20rem, 82vw)`
  wide and full height, sliding in over a dimmed page and scrolling on its own if
  the menu is long; the button stays on its top corner and swaps `menu-label` for
  `close-label`. **`--panel`** drops a full-width sheet out of the header instead,
  right for two or three short labels. **`--row`** drops the button and stacks the
  mark, a horizontally scrolling row of items and the controls as three bands; a
  submenu there runs on beside its parent rather than nesting under it.
- `sticky=no|yes` — `-sticky--yes` pins the bar to the top of the viewport. A
  persistent header reads as a signal that the offer is still there and is worth
  around 22% quicker navigation; the price is that every pixel of it is page
  nobody can see, on every screen. So it compacts its padding above `60rem`, and
  suits `--inline` far better than `--centred`, two rows tall before it starts.
- `menu-align=start|end` — which edge the items inside the small-screen sheet are
  set against. It does not move the sheet: `menu` decides that, and the drawer is
  at the inline end on both rungs. Inert above `60rem`, and on `--row`.

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
