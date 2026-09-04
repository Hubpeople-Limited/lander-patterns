# colophon

**What it is and when to use it.** The site footer a page carries itself,
named for the print trade's closing page the way `masthead-nav` is named for
its opening one: the brand's managed footer menu, the four legal links every
brand serves, and a copyright line, set small on a quiet ground behind a
hairline - centred on one line, or spread across three columns with the
brand mark above them. Every full page ends with one; it is the page's own
markup, not something the platform adds around the page. What the platform
does is fill the links: each placeholder hydrates per brand at serve time,
which is why nothing here is ever replaced with a literal URL.

That sentence has history. This pattern was once withdrawn on the theory
that the platform injects a site footer under served pages and a built one
would double it. Measured against served canvas pages, a page built without
a footer serves without one - no copyright, no legal links - and the
platform's own default canvas page ships with footer markup for the same
reason this pattern exists.

**What it needs.** One line of real content: the copyright, in the brand's
name. With `mark=logo`, where the mark links to (`home-url`, the site root).
Everything else is platform furniture. `{{menu.footer}}` renders the footer
menu managed in the portal; on a brand that manages none it expands to
nothing, so delete the nav element rather than shipping an empty landmark -
the brand record says whether a managed secondary menu exists. `--columns`
notices the deletion and sets two columns instead of two and a hole.

**Placement.** The last element of the page body, always. `one-per-page` is
literal: a page with two footers has not decided where it ends. Patterns
whose comments say "before the footer" mean this pattern.

**Brand adaptability.** Three axes, all real modifier classes.

| Axis | Rungs | What it moves |
|---|---|---|
| `ground` | `plain`, `soft` | the page's own ground, or the brand's surface tint |
| `layout` | `line`, `columns` | everything centred and stacked; or, from `60rem` up, the menu, the legal links and the copyright as three columns, the menu and the legal links running down rather than along, the copyright set against the end edge. Below `60rem` both rungs are the stack |
| `mark` | `none`, `logo` | nothing, or the brand mark above the rest, drawn at `calc(var(--logo-height) * 1.1)` - a tenth over the header's, so it reads as a signature rather than a repeat of the bar |

After a full-bleed closing band either ground reads as an ending, because
the hairline and the drop to small quiet text do the work. Links take
`--color-text-soft` and reach `--color-text` on hover: a footer is reference
material, and nothing in it competes with the page's last call to action. The
focus ring is `--color-focus`, which is safe here because both grounds are
page-adjacent rather than the brand colour.

**The mark is the file as it is, on a page-adjacent ground.** Both grounds
sit next to the page colour, so a mark whose ink reads in the header on
`ground=plain` reads here too. There is no plate or silhouette rung, because
neither ground needs one; a brand whose mark is light ink for a dark header
keeps `mark=none` here rather than drawing a pale mark on a pale ground.
Set the `<img>` `width` and `height` to the file's own pixel size and let the
height rule decide the rendered size. Never put the height back to `auto`
under a `max-height`: a `viewBox`-only SVG has a ratio and no size, so two
ceilings resolve it to 0x0. `ci/check_logo.py` discovers the mark by its
`{{logo.src}}` image and holds it to the height this stylesheet declares, at
six widths, against the logo shapes real brands ship.

**The menu is styled by descent.** The platform decides the markup
`{{menu.footer}}` expands to, so the pattern's rules target elements under
`.colophon-menu` rather than any generated class name - they hold whatever
list the platform renders, on both layouts.

**Choose `columns` for a page full of designed sections.** A one-line footer
under a long, columned page reads as unfinished; three columns and the mark
are what a professional site closes with. `line` is right under a short page
or a one-screen landing, where a heavy footer would outweigh the page.
