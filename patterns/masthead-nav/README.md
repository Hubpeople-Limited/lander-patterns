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
platform, and two words in the brand's language: `menu-label` on the button, and
`close-label` for that same button while the menu is showing. `home-url` is where
the mark links, usually `/`. Set the `<img>` `width` and `height` to the logo
file's own pixel size — they only fix its aspect ratio, and `--logo-height`
decides how tall it renders. Everything else is platform furniture, left as it is.

**Pairing.** It sits above everything, so it has no neighbours in the ordinary
sense. It is a `component`, not a `section`, on purpose: `ci/check_page.py` judges
the first *section* against the fold, and typing this as a section would take a
full-viewport hero out of that check. And when a recipe states this pattern's
ground and the section under it has the same one, the page checker reports two
neighbours running together — so state the header's ground only when it differs
from the opener's.

**Brand adaptability.** Three axes, all real modifier classes.

- `ground=plain|soft|brand` — the ladder. `--brand` inverts the join control to
  `--color-on-primary` on `--color-primary`, the pair the contract states a ratio
  for; every rung reads the same local properties, so no rule in the file knows
  which ground it is on.
- `layout=inline|centred` — `--inline` puts mark, menu and controls on one row.
  `--centred` gives the mark its own line with the menu centred beneath it and
  the controls parked in the corner, which is the editorial reading.
- `menu=drawer|panel|row` — what the menu does below `60rem`. **`--drawer`** is
  what a phone expects: a panel fixed to the inline-end edge, `min(20rem, 82vw)`
  wide and full height, sliding in over a dimmed page and scrolling on its own if
  the menu is long. The button does not move — it sits above the panel on its top
  corner and swaps `menu-label` for `close-label`. **`--panel`** drops the menu
  out of the header as a full-width sheet, which is lighter and right for two or
  three short labels with no submenus. **`--row`** drops the button entirely and
  runs the menu as a horizontally scrolling row beside the mark; a submenu there
  has to run on beside its parent rather than nest under it.

`--logo-height` carries a fallback, so a brand that never defines it still
renders. `--font-heading` on the menu items is most of what makes the bar look
like the brand rather than a generic navigation.

**No script, at any width.** The menu is a native `<details>`/`<summary>`, so the
browser gives the button its expanded state, keyboard operation and focus ring —
on markup this pattern cannot alter. A shut drawer is `visibility: hidden`, which
is what keeps it out of the tab order and out of find-in-page, so nothing is
trapped in it. Above `60rem` the same panel is forced open by CSS, and **two
declarations are needed for that** (`display` on the panel, `content-visibility`
on `::details-content`): engines hide a closed `<details>` in two different ways,
and removing either leaves the menu shut on some browsers.

**What `behaviours: drawer` adds.** `Escape` closes the drawer and returns focus
to the button, a press on the backdrop closes it, and the page behind holds still
while it is open. Without the bundle all three are simply absent: the drawer still
opens, closes, slides, scrolls and takes the keyboard. The behaviour acts only
while the panel is fixed to the viewport, so on `--panel`, on `--row` and above
`60rem` the hook is inert and can be left in place.

**Three things the generated markup forces.** *A parent item with both children
and a URL comes through as two `<li>` entries* — one plain link, one `has-submenu`
carrying the children — so the label appears twice. Nothing here hides one: the
only selector that could reach it is "the item before a `has-submenu` item", which
matches an ordinary neighbour just as often. The repair is in the menu data.
*The generated `<ul>` cannot carry `role="list"`*, so Safari drops the item count
once the markers go. *The `title` attribute is not escaped*, so check labels with
punctuation before a brand goes live.
