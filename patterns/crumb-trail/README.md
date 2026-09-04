# crumb-trail

**What it is and when to use it.** The breadcrumb: one quiet line under the
site header saying where this page sits - the root, the parents that exist,
and the page itself as plain text. Every page below the root carries one;
the homepage and a campaign landing page do not, because neither sits under
anything. It is named `crumb-trail` rather than `breadcrumb` because a
`breadcrumb` class family already exists in the stylesheet brands ship, and a
pattern taking that name would collide with it on append.

**What it needs.** The site root's relative path, with a trailing slash, and
its label; the label and extensionless relative path of each parent page that
actually exists; and the current page's own title. Only link to pages that
exist: a parent that has not been built is written as text in its place, never
linked. The markup is the shape a page must carry whatever builds it - the
root first, `aria-current="page"` on the last item, the separators decorative
and hidden - so a trail built by hand and one placed from here read the same
to assistive technology.

**Placement.** Directly under `masthead-nav`, above the opener. `one-per-page`
is literal. Duplicate the parent link and its separator for each level between
the root and this page; delete both where the page sits directly under the
root, leaving the root and the current page.

**Pairing.** It sits under the header on any page below the root and pairs
with nothing in particular. It does not count against a recipe's ground run:
like the header, it is furniture decided once.

**Brand adaptability.** One axis.

| Axis | Rungs | What it moves |
|---|---|---|
| `width` | `page`, `column` | the page's container (`--container-max`), which every full-width shell uses; or the 52rem article column, so on an article page the trail's left edge is the writing's left edge and not a second one |

Links take `--color-text-soft` and reach `--color-text` on hover; the current
page is `--color-text` at a heavier weight so the eye lands on where it is.
The separator is a single right-pointing angle quotation mark, which does not
depend on the heading face. Nothing here is a control drawn as a button: the
links are text, so they are held to the text rules rather than the 44px
thumb target.
