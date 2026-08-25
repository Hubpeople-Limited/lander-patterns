# masthead-nav

**What it is and when to use it.** The site header: brand mark, primary
navigation, login and join. **Most of its markup is not in this pattern.** The
platform expands `{{menu.navigation}}` into a `<ul class="canvas-navigation-menu">`
with `<li class="has-submenu">` children and `<ul class="canvas-navigation-submenu">`
nested inside them — and it ships **no CSS at all** for any of that. On a brand
whose stylesheet does not style those classes, the menu renders as stacked
browser bullets over the top of everything. So what this supplies is the chassis
around the placeholder plus the stylesheet that makes the generated classes
behave, at every width. It is page furniture: chosen once for a site, on every
page, which is why it names nothing in `pairs-with`. Do not use it where the page
already has a header, or where the brand chose the platform's self-contained
`{{menu.navigation.default}}` menu, which brings its own small-screen behaviour
and fights this one.

**What it needs.** The brand's logo file, the menu items configured on the
platform, and one word for the small-screen menu button in the brand's language
(`menu-label`). `home-url` is where the mark links, usually `/`. Set the `<img>`
`width` and `height` to the logo file's own pixel size — they only fix its aspect
ratio, and `--logo-height` decides how tall it renders. Everything else — menu,
logo, login and join — is platform furniture and is left exactly as it is.

**Pairing.** It sits above everything, so it has no neighbours in the ordinary
sense. Two things to know. It is a `component`, not a `section`, on purpose:
`ci/check_page.py` judges the first *section* against the fold, and typing this
as a section would take a full-viewport hero out of that check. And when a recipe
states this pattern's ground and the section under it has the same one, the page
checker reports two neighbours running together — so state the header's ground
only when it differs from the opener's, which is the case worth looking at.

**Brand adaptability.** Three axes, all real modifier classes.

- `ground=plain|soft|brand` — the ladder. `--brand` inverts the join control to
  `--color-on-primary` on `--color-primary`, the pair the contract states a ratio
  for; every rung reads the same local properties, so no rule in the file knows
  which ground it is on.
- `layout=inline|centred` — `--inline` puts mark, menu and controls on one row.
  `--centred` gives the mark its own line with the menu centred beneath it and
  the controls parked in the corner, which is the editorial reading.
- `menu=drawer|row` — the small-screen behaviour. `--drawer` folds the menu
  behind a button; `--row` drops the button and runs the menu as a horizontally
  scrolling row beside the mark. Pick `--row` only for two to four short labels
  with no submenus, because a submenu there has to run on beside its parent
  rather than nest under it.

`--logo-height` carries a fallback, so a brand that never defines it still
renders. `--font-heading` on the menu items is most of what makes the bar look
like the brand rather than a generic navigation.

**No script, at any width.** The small-screen menu is a native
`<details>`/`<summary>`, so the browser gives the button its expanded state,
keyboard operation and find-in-page — on markup this pattern cannot alter,
because it wraps that markup rather than changing it. On wide screens the same
panel is forced open by CSS, and **two declarations are needed for that**
(`display` on the panel, `content-visibility` on `::details-content`): engines
hide a closed `<details>` in two different ways, and removing either leaves the
menu shut on some browsers. Wide-screen submenus are faded rather than removed,
so keyboard focus can reach them and `:focus-within` brings them up; below the
breakpoint every level is visible in the drawer.

**Three things the generated markup forces.**

*A parent item with both children and a URL comes through as two `<li>`
entries* — one plain link, one `has-submenu` carrying the children — so the label
appears twice in a row. Nothing here hides one of them: the only selector that
could reach the duplicate is "the item before a `has-submenu` item", which
matches an ordinary neighbour just as often and would delete real items from
menus that have no duplicate at all. Both entries work, and the bare `<a>` gets
no pointer and no underline so it does not read as a dead link. The repair is in
the menu data — give the parent no URL, or make its landing page a child.

*The generated `<ul>` cannot carry `role="list"`.* Dropping the markers takes
list semantics away in Safari, and the usual repair is an attribute on a tag this
pattern does not own. The menu stays operable; VoiceOver just will not announce
the item count.

*The `title` attribute is not escaped*, so a label containing a quote leaks into
it. Check labels with punctuation before a brand goes live.
