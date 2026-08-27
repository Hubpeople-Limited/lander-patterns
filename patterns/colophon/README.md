# colophon

**What it is and when to use it.** The site footer a page carries itself,
named for the print trade's closing page the way `masthead-nav` is named for
its opening one: the brand's managed footer menu, the four legal links every
brand serves, and a copyright line, set small on a quiet ground behind a
hairline. Every full page ends with one — it is the page's own markup, not
something the platform adds around the page. What the platform does is fill
the links: each placeholder on it hydrates per brand at serve time, which is
why nothing here is ever replaced with a literal URL.

That sentence has history, so it is worth being plain. This pattern was once
withdrawn on the theory that the platform injects a site footer under served
pages and a built one would double it. Measured against served canvas pages,
that is not what happens: a canvas page is served as its stored document with
the tokens hydrated, and a page built without a footer serves without one —
no copyright, no legal links. The platform's own default canvas page ships
with footer markup for the same reason this pattern exists.

**What it needs.** One line of real content: the copyright, in the brand's
name. Everything else on it is platform furniture. `{{menu.footer}}` renders
the footer menu managed in the portal; on a brand that manages none it
expands to nothing, so delete the nav element rather than shipping an empty
landmark — the brand record says whether a managed secondary menu exists.

**Placement.** The last element of the page body, always. `one-per-page` is
literal: a page with two footers has not decided where it ends. Patterns
whose comments say "before the footer" — `cta-band`'s placement note — mean
this pattern.

**Brand adaptability.** The ground is the page's own (`--plain`) or the
brand's surface tint (`--soft`); after a full-bleed closing band either
reads as an ending, because the hairline and the drop to small quiet text do
the work. Links take `--color-text-soft` and reach `--color-text` on hover —
a footer is reference material, and nothing in it competes with the page's
last call to action. The focus ring is the library's usual `--color-focus`,
which is safe here because both grounds are page-adjacent rather than the
brand colour.

**The menu is styled by descent.** The platform decides the markup
`{{menu.footer}}` expands to, so the pattern's rules target elements under
`.colophon-menu` rather than any generated class name — they hold whatever
list the platform renders.

**No logo, deliberately.** A footer logo is a flourish some brands want and
most do not; a pattern that ships one makes every page pay for it. A brand
that wants its mark here adds it as its own line above the menu and sizes it
with its own `--logo-height`-derived value.
