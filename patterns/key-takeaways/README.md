# key-takeaways

**What it is and when to use it.** The summary box near the top of a piece: a
heading and three to five one-line points that give a reader what the article
concludes without making them read it. It sits between the page's opening
block and the first run of body copy.

Use it on any article long enough that a reader may not finish, and on a
safety page, which is the same shape of writing under a different name — a
long explanation somebody arrives at holding one question. The opener differs
between the two: `article-masthead` is for `article` only, so a safety page
opens on a hero and this sits under that instead.

Do **not** use it as a contents list, a set of selling points, or a place to
put a call to action. It summarises the piece it sits inside and asks for
nothing. And do not use it on a page whose whole body is already short: a
summary of four paragraphs is four paragraphs with a box drawn round them.

**Opens at `h2`.** The page's `h1` comes from whatever opens it, and the
heading here is the reader's label for the box — "In short", "What this
covers" — never the article's title again.

**What it needs.** Three to five points, and every one of them held to three
tests at once:

1. **True on its own.** The point is a complete statement. Not a topic
   ("safety"), not a fragment ("how to spot a fake profile"), but the thing
   the article actually says about it.
2. **Answerable from the body.** Every point is supported further down. A
   point the piece never returns to is an assertion the reader cannot check,
   and it is the one they will remember.
3. **Not the headline reworded.** The title and the lede are already on the
   page, directly above. A box repeating them is padding, and both search
   engines and readers treat a page that pads as one that has little to say.

Three is the floor because two points are a sentence, and five is the ceiling
because a list a reader has to scroll is not a summary. If the piece will not
reduce to five, the piece is two articles.

This is the block that answer engines and search result summaries lift when
they describe the page, so it earns its place twice: once for the reader
skimming, once for whatever is reading on their behalf. That is a reason to
make each line stand alone, not a reason to write it for a machine.

**Pairing.** Under the opener — `article-masthead` on an article, a hero on a
safety page — and above `prose-column`. Where the page also carries
`article-toc`, the contents list takes the row directly under the opener and
this sits below it: the list is the shape of the piece and this is what the
piece concludes, so a reader meets them in that order. It is `one-per-page`: a
second summary box on one page is two answers to the same question, and the
reader has no way to tell which is the real one.

No `avoid-with` entry. It paints one quiet block, carries no image and makes
no ask.

**Brand adaptability.** `--color-surface-soft` fills it and `--card-radius`
rounds it, so the block picks up the corner language the brand already uses on
its cards. `--card-border` draws the edge, which matters on a brand whose soft
surface sits close to its page ground: without it the block would be the
heading and nothing else.

**`--card-shadow` is deliberately not taken.** A shadow lifts the box off the
page, and the whole point of this one is that it is *inside* the article — a
reader should read it as the writing's own summary, not as something the site
put there. The same reasoning keeps `--color-primary` out of it entirely.

The heading takes `--color-text` rather than `--color-heading`, on both
grounds that token's contract sets: the block paints a surface, and the label
is nowhere near the 24px the heading ink is guaranteed at. It reads as a
heading through the display face, the weight and the uppercase setting.

One dial: `--key-takeaways-measure` (default `68ch`) is the column width, and
it is the same number `prose-column` holds its body to. Both are in `ch`
against the same body size, so the box and the paragraphs under it line up on
every brand. Change one and change the other, or the article gains a step in
its left edge.
