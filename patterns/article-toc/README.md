# article-toc

**What it is and when to use it.** In-page contents for a long piece: a short
list of anchor links to the sections below, inside a native disclosure so a
reader can put it away again. It sits directly under the page's opener —
`article-masthead` on an article, a hero on a safety page, since the masthead
is for `article` only — and above the first run of `prose-column`.

Use it where the piece is long enough that a reader arrives wanting to know its
shape — roughly a thousand words and up, four sections and up. That is the
material search rewards on a dating brand, and on a phone it is the difference
between a page you navigate and a page you scroll.

Do **not** put one on a short article. Three headings over eight hundred words
do not get a contents list, they get read; a list of three is a list that costs
a screen and saves nothing. Nor is it a menu: every link goes to a heading on
this page, never to another page, which is `link-cluster`'s job. And where the
sections have more than one level, list the top level only — a nested contents
list is a second document about the first.

**Zero JavaScript, and the ids are yours to write.** This is a list of
`<a href="#…">` and nothing else. The `id`s it points at go on the headings in
`prose-column`, written by whoever places the pattern. **A contents list
pointing at ids nobody added is a page of dead links that fails silently** —
the browser simply stays where it is, no error, nothing in the console. Write
the ids first, then the list, then click every entry.

Anchors land the heading at the very top of the viewport, which puts it under a
sticky header where a brand has one. `scroll-margin-block-start` on the target
headings is the fix, and it belongs in the brand's own stylesheet, not here:
only the brand knows how tall its header is.

**One form, not two.** The list ships inside a `<details>` that is live at
every width, with `open` in the markup so it arrives showing. Forcing it open
above a breakpoint instead takes two declarations — `display` on the content
and `content-visibility` on `::details-content` — and leaves the `<summary>` a
control that is still focusable, still announced as collapsed or expanded, and
no longer changes anything. Hiding the summary at that width instead takes away
the list's only label. So the reader's choice is honoured at every width, and a
brand that would rather it arrived shut deletes `open`.

Arriving open is the decision worth stating. A closed list orients nobody: the
reason to place one is that a reader can see the shape of the piece before
committing to it, and a shut row shows no shape. The disclosure is there so the
list can be put away once it has been used — on a phone, where it costs most.

**`one-per-page` is `yes`.** The list is the page's map, and two maps of one
page is not a map — a reader who finds a second one has to work out which of
them covers where they are. A very long piece in parts is the case for a list
per part, and it is a piece that wants splitting instead. The mechanism agrees:
the label carries a fixed `id` that two copies would collide on.

**What it needs.** The article's own section headings, in the order they
appear, worded the way the body words them. A contents entry rewritten to read
better than its heading is a promise the section then breaks. And an `id` on
every heading it names — see above; that is the half that gates use.

**Accessibility.** The root is a `<nav>`, labelled by the summary's own text
through `aria-labelledby`, so it is announced as navigation and named rather
than being one more unlabelled landmark. It carries no heading of its own on
purpose: a contents list that appears in the contents is noise, and the
document outline belongs to the article. Every link is drawn as a row with a
44px floor, which is the gate a tight list of short titles fails first.

**Pairing.** The page's opener above it, `key-takeaways` or `prose-column`
below it, and `author-note` at the foot of the same page. Nothing else sits
between the opener and this — a reader who has decided to read wants the list
or the first sentence, not a third thing.

**Brand adaptability.** It paints no ground and offers no variants, so it takes
the ink of whatever it is placed on. `--color-rule` draws the two hairlines and
the divider between entries, decorative in all three places: the list is a real
`<ol>` and the disclosure a real `<details>`, so a brand may set that token as
soft as it likes without losing anything. `--font-heading` sets the label,
which is the one piece of display type here and moves with `--type-scale` — at
`0.875rem` rather than the `0.8125rem` the library's undialled eyebrows use,
because a size that moves has to clear the 12px text floor at the `0.9` bottom
of that dial as well as at `1`. The links stay body-sized: they are the
headings' words, and a reader is scanning them.
With the library, `scrollspy` underlines the link for the section being read; without it the list is the list.
