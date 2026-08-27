# Image placeholders

Stand-in images for building a page before the brand's photography exists.
Three shapes, matched to what the photography patterns ask for:

| File | Shape | For |
|---|---|---|
| `wide.svg` | 16:9 | full-bleed heroes and closing bands (`hero-overlay`, `hero-centred`, `cta-image`) |
| `landscape.svg` | 4:3 | row and card images (`zigzag-rows`, `photo-cards`) |
| `portrait.svg` | 3:4 | step cards and tall slots (`steps-numbered`, `hero-split`) |

They are deliberately wordless, translucent grey on no ground, so they read on
a light page and a dark one alike and inherit nothing from the brand. A build
may tint one: the file is plain text, and swapping the `#808080` fills for a
soft tint of the brand's own colours is a two-line edit to the copy in
`site/images/` — never to the file here.

**The rules of use:**

- A placeholder is a stated stand-in, never a silent one. The page is shown
  and pushed with the words said out loud: these images are placeholders,
  replaced when the brand's photography arrives.
- Copy the file into the brand's own `site/images/` and reference it there;
  do not hot-link the library.
- The `alt` on a placeholder says what the **real** image will show, if that
  is known, or names it a placeholder — never invented detail.
- **Never for people.** A pattern that needs consented member photographs
  (`portrait-wall`, `member-strip`, the testimonial patterns,
  `media-card-grid`) takes real, consented material or is not used at all: a
  placeholder person is an invented person.
- A placeholder satisfies a pattern's *shape* requirement, not its `needs` —
  the real photograph the `needs` line describes is still owed, and the brand
  README's log records that it is.
