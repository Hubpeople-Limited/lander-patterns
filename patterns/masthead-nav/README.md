# masthead-nav

**What it is and when to use it.** The site header: brand mark, primary navigation, login and join.
**Most of its markup is not in this pattern.** The platform expands `{{menu.navigation}}` into a
`<ul class="canvas-navigation-menu">` of `<li><a href title target>` items; a parent with children
arrives as `<li class="has-submenu"><a>label</a><ul class="canvas-navigation-submenu">…</ul></li>`,
its `<a>` with no `href`; a parent with both a URL and children arrives as **two** `<li>` entries; a
third level nests the same way under a class of its own. The platform ships **no CSS** for any of it,
and on a page whose menu switch is off it expands to nothing. This is the chassis around that
placeholder and the stylesheet that makes whatever it produces behave: page furniture, chosen once.

**The menu is styled by structure, not by the platform's class names.** Every menu rule targets `ul`,
`li`, `a` and `button` under `.masthead-nav-links`, and a parent is `li:has(> ul)`. A generated list,
a list three levels deep and a static list written by hand - a `<ul>` of `<li><a href>` with a nested
`<ul>` for children, no classes needed - all take the same styling. Not for a brand on
`{{menu.navigation.default}}`, which arrives as a complete navigation with its own button, drawer,
controls, stylesheet and script, and would sit beside this one as a second menu.

**What it needs.** The logo file, the menu configured on the platform, and three words in the brand's
language: `menu-label` on the button, `close-label` for it while the menu shows, and `more-label` for
the item `overflow=more` folds the rest into - all three on every rung. `home-url` is where the mark
links.

**The logo is sized by its height, and the width follows.** Set the `<img>` `width` and `height` to
the file's own pixel size and let `--logo-height` decide how tall it renders. Never put the height
back to `auto` under a `max-height`: a `viewBox`-only SVG has a ratio and no size, so two ceilings
resolve it to 0x0. `object-fit: contain` keeps it undistorted once the small-screen cap bites.

**The mark on a coloured ground is the `mark` axis, not a second file.** `--plate` sets the mark on a
small `--color-bg` panel, which adds `--space-2` above and below to the bar. `--mono` draws it as a
white silhouette, right only for a mark whose meaning survives one colour on a dark enough ground.

**Pairing.** None; a `component`, not a `section`, so `ci/check_page.py` still judges the first
section against the fold. **Login and join live inside the disclosure**: an open drawer covers the
page, so a control outside it is behind the scrim, and `ci/lint.py` fails one left outside.

**Brand adaptability.** Twelve axes, all real modifier classes. Below `60rem` is the small-screen
arrangement; above it the menu is a row in the bar.

| Axis | Rungs | What it moves |
|---|---|---|
| `ground` | `plain`, `soft`, `brand` | the ladder; `--brand` inverts the join control to the on-primary pair |
| `layout` | `inline`, `centred` | one row, or the mark on its own line with the menu centred beneath |
| `menu` | `drawer`, `panel`, `row` | below `60rem`: a `min(20rem, 82vw)` side panel over a dimmed page; a lighter full-width sheet, for two or three labels; no button and a scrolling row |
| `overflow` | `wrap`, `more`, `scroll` | above `60rem` when the items do not fit: a second row and a taller bar; a fold into one last item in the brand's word, opened like any submenu, needing the behaviour library and `--wrap` without it; one row scrolling sideways under a fade, its submenus run on inline |
| `submenu` | `dropdown`, `mega` | a `12rem` panel under the item, or one panel the width of the bar with the children in columns. Both are the platform's labels and links, well set |
| `nav` | `full`, `minimal` | `--minimal` renders no menu at any width: the mark, the join control, and login from `60rem` up. The placeholder stays, so the menu returns when the rung does. For a page reached from an advert |
| `sticky` | `static`, `pinned`, `compact` | `--pinned` holds the bar at the top and compacts it above `60rem`; `--compact` also tightens it and draws the mark at four fifths once the page has scrolled, via the library, and is `--pinned` without it |
| `mark` | `direct`, `plate`, `mono` | above |
| `menu-align` | `menu-start`, `menu-centre`, `menu-end` | which edge the items in the sheet are set against; inert on `--row` |
| `menu-side` | `side-start`, `side-end` | the side the button sits on and the drawer slides in from; inert on `--row` |
| `toggle` | `labelled`, `icon` | the word beside the bars, or the bars alone (the word clipped, still announced); on `--icon` the mark takes the row up to the button below `60rem` |
| `edge` | `rule`, `shadow`, `flush` | a hairline, `--card-shadow`, or neither; the bar is the same height on all three |

**Choose `overflow` from the menu.** Up to four short items fit beside any mark. Five or more, a long
label or a wide wordmark is `--more`: the library measures on every resize and after the fonts arrive,
folds from the end until the row fits and unfolds when room returns. `--scroll` is for a brand with no
submenus that wants every item in view. `--wrap` is chosen knowingly, and measures
`--page-header-height` at the width where the row breaks. **Choose `submenu` from the children**: two
to six is `--dropdown`, ten or more is `--mega`; `--mega` cannot combine with `--scroll`.

No rung hides the menu behind a button at desktop width: a hidden menu is missed
almost twice as often. **Prefer `labelled`**: a word beside
the bars is found faster than bars alone. **`edge` costs no height.**

**No script, at any width.** The menu is a native `<details>`/`<summary>`; a shut drawer is
`visibility: hidden`. Submenus open on hover and `:focus-within`; the bar clips sideways, so a
faded panel never widens the page, and the last two items hang their panels from the end edge.
One limit stays without the library: on a row that has wrapped, a parent at a row's right edge
has its panel clipped at the bar, because CSS cannot tell which item ends a row; `menu` measures
it and turns the panel round, and every shell carries the bundle. **The four behaviours add**:
`drawer`, Escape, a backdrop press and a held page; `menu`, every parent an operable control with
`aria-expanded`, Escape, outside press, arrow keys, hover grace, and a panel that would leave the
viewport anchored to its other edge; `overflow` and `shrink`, the two rungs above. Each acts only
while the stylesheet has the header in that state, so every rung renders complete without the
library. `ci/check_header.py` renders this pattern against three-, six- and nine-item menus with
submenus, beside two ratio-only marks, at eight widths, library on and off.

**The generated markup forces three things.** A parent with both children and a URL arrives as
two `<li>` entries; the generated `<ul>` cannot carry `role="list"`; `title` is not escaped.
