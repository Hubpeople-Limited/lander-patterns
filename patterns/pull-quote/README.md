# pull-quote

**What it is and when to use it.** One line lifted out of the running text and
set large between two runs of body copy. It breaks a long column, gives the
eye somewhere to land, and carries a single idea from the piece into a reader
who is skimming it.

Use it in the middle of a long read, and only there. Two or three across a
long article is normal; the pattern is not `one-per-page`.

**It is not `quote-feature`.** That one is a full-width testimonial stage, it
`requires: consented-people`, and it exists to show that somebody outside the
brand said something. This is the article's own words about itself, so it
requires nothing and attributes nothing. **There is no attribution slot, and
adding one is the signal that the wrong pattern is in use:** a quote with a
name beside it goes in the body, as `prose-column`'s `<blockquote>` and its
`<cite>` — neither testimonial pattern serves an `article` or a `safety` page.

Do **not** open a piece with one — the lede has that job — and never put a
line here that is not already in the body. A sentence that appears only in the
pull quote is a claim the article never makes.

It carries no heading, so it fits at any depth in a page without touching the
heading order.

**What it needs.** One sentence, word for word out of the body copy on the
same page, short enough to take in at a glance, carrying an idea rather than a
statistic. A figure pulled out large needs a source under it, which is
`source-note`'s job and makes this the wrong frame for it.

Repetition is the point of the pattern, so the line must genuinely be above or
below it. Shortening it to fit means shortening the sentence in the body too,
not writing a second version of it.

**Duplicated text, said once.** The element carries `aria-hidden="true"`,
because a screen reader that meets the same sentence twice in one column hears
a stutter with no visual cue to explain it — this is decoration made of words,
and the words are still in the article. `<aside>` is the element the HTML
specification names for exactly this case, and it stays the element under the
hidden attribute so the markup is still honest about what the block is.

**So nothing in the slot may take focus.** No link, no button. `aria-hidden`
removes the block from the accessibility tree and not from the tab order, so a
link dropped in here is one a keyboard user lands on and a screen reader cannot
name — and it is silent: the page looks right and every check in this library
passes it. A line that wants a link wants to be a paragraph in `prose-column`.

**Pairing.** Between two `prose-column` blocks. It is placed as a sibling of
the column rather than inside it: `prose-column` styles its own descendants,
so a quote dropped inside would take the column's paragraph rules and lose
this one's.

That is also the reason **no inset or floated variant ships**. A float only
wraps text inside the same block, which this pattern is never in, so the
obvious second look would do nothing where the pattern is actually placed. A
modifier that changes nothing is worse than no modifier.

No `avoid-with` entry. It paints no ground and makes no ask.

**Brand adaptability.** `--font-heading` and the negative tracking carry
almost all of the character; a brand with a strong display face gets a very
different pull quote from one on a system stack, with nothing changed here.
The size runs `clamp(1.375rem, 3.2vw, 2rem)` and rides `--type-scale`, so a
brand at the quieter end of that dial gets a quote that still reads as a break
rather than a shout.

The ink is `--color-text`, not `--color-heading`. The heading ink is
guaranteed only on genuinely large text, and this one's floor is 22px so it
would drop under that bar on any brand dialling type down.

`--color-rule` draws the hairline above and below. Nothing depends on those
lines being visible — the size alone marks the quote out — so a brand may set
the rule as soft as it likes, or effectively invisible, and it still reads.

One dial: `--pull-quote-measure` (default `68ch`) is the width of the band the
rules span, and it is the number `prose-column` and `key-takeaways` also hold
to. The three line up only while they agree, so change them together. The
quote's own text is held to a much shorter `15em` inside that band, which is
what keeps it two or three lines rather than a paragraph.
