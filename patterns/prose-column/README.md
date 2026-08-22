# prose-column

**What it is and when to use it.** The body of a piece of writing: one column
held to a readable measure, with the headings, paragraphs, lists, quotes and
tables an article actually uses already set. Nothing inside it takes a class —
the column styles its own descendants, so a whole article can be pasted in
without touching every tag.

Until this existed, an article page had a masthead, an optional section opener,
a gallery and a sticky bar, and **no way to hold the writing itself**. Anyone
building one had to invent a prose treatment on the spot, which is how two
articles on one site end up with different type scales.

Use it for any run of real writing: an article body, a long safety explanation,
a founder's account, the middle of a guide. Several may sit on one page with
other sections between them.

Do **not** use it as a general text wrapper for a section that is really a
component. A single centred paragraph under a heading is `heading-block`'s
supporting line; a short claim is `opener-split`'s.

**What it needs.** Real writing, structured so it can be scanned and quoted:
headings that say what their section contains, information first, and each
section opening with a complete one-sentence answer to the question its heading
raises. That first sentence is what a reader skimming takes, and what an answer
engine lifts, so it has to stand on its own.

**Keep the material's own shape.** Where the writing is a comparison or a ranked
list, it ships as a real `<table>` or a real `<ol>` — the markup carries the
meaning, and a comparison laid out as paragraphs has thrown it away. The reverse
matters just as much: never bend prose into bullets to break up a page. Delete
every element in the skeleton the writing does not actually use.

**Headings start at `h2`.** The page's `h1` comes from `article-masthead` or the
page's own hero. Do not skip a level.

**Pairing.** Directly under `article-masthead`, which is the usual article
opener. `heading-block` or `opener-split` between two long runs where the piece
changes subject. `gallery-scroll` between runs where it has pictures. No
`avoid-with` entry: it paints no ground, carries no image and makes no call to
action.

**Brand adaptability.** `--color-text` carries the body and `--color-text-soft`
the marker glyphs, the caption and the citation — both contracted against the
grounds they sit on. `h2` is the one use of `--color-heading`, with both halves
of that token's contract met: the column paints no ground, so it sits on
`--color-bg`, and the `clamp()` floor is 28px, above the 24px it is promised at.

**`h3` deliberately does not take the heading colour.** At 20px it is under the
size that token covers — the contract is 24px, or 18.66px when bold, and 600
weight is not bold. So it takes `--color-text`, and reads as a heading through
size and weight instead.

Links are `--color-primary-dark`, which is the token contracted as a dark ink
for small text on a light ground, and they are underlined. **The underline is
not decoration and must not be removed**: in a run of prose, colour alone is the
only thing marking a link, and colour alone is never enough.

`--color-rule` draws the quote's edge and the table's row lines, decorative in
both places — the `<blockquote>` element carries the quotation and the `<th>`
cells carry the table's structure, so nothing is lost where a brand sets it
soft. `--color-surface-soft` fills the table header and `--card-radius` rounds
its top corners.

One dial: `--prose-column-measure` (default `68ch`) is the column width. It is
the single most consequential number here — much wider and long paragraphs stop
being readable, much narrower and a table has nowhere to go.

**The table scrolls inside its own box.** It carries `min-width: 28rem` inside a
`figure` with `overflow-x: auto`, so on a phone the table scrolls sideways and
the page does not. A page that scrolls sideways because of one wide table is the
commonest reflow failure there is.
