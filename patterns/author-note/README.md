# author-note

**What it is and when to use it.** The block at the foot of a written piece
saying who wrote it and why they can be trusted on the subject: a label, the
writer's name, their standing, one paragraph of biography, and — where one
exists — a link to the rest of their work. It sits on a tinted panel under the
writing and above the site footer.

Use it on any article carrying advice a reader might act on. On a dating brand
that is most of them: safety, money, meeting a stranger, what to put in a
profile. Readers and search engines both weigh who stands behind advice, so an
unattributed page on those subjects is a weaker page than an attributed one.
It is listed for `safety` as well as `article` for that reason, and a safety
page is where it counts most, because nothing else on one carries a byline.

**Not the same thing as the byline.** `article-masthead`'s byline row answers
*who is speaking* before a word has been read; this answers *why listen to
them*, after. An article may carry both, and normally should — but not if all
this block can offer is the name and the role again, in which case drop it and
keep the byline. A safety page has no masthead, so nothing can be repeated.

Do **not** use it for a house account, an editorial team, or a name nobody
will stand behind — a block asserting expertise on behalf of nobody in
particular makes a claim the page cannot support. And it is not an "about us";
that is a page of its own, not the end of an article.

**It opens at `h2`,** and the heading names the block rather than the person;
the name is the line under it, set larger. It closes the writing's run of
`h2`s; a closing call to action below it carries one of its own. The root
is an `<aside>` labelled by that heading, so the block is reachable and
skippable as a landmark — and not a `<footer>`, because a page-level footer is
the contentinfo landmark `colophon` owns.

**No portrait, deliberately.** A photograph of a named person is
`consented-people` material, and requiring one would gate the pattern behind
something most brands do not hold for their writers. The weight comes from the
panel instead: a fill, a card edge, and a brand-coloured rule across the top.

**What it needs.** All of it real, and it gates use:

- **The name of the person who wrote the piece**, who is willing to be named.
- **What they do that bears on this subject** — the job, the qualification, the
  years, the body they belong to, the thing they built or ran. "Loves writing
  about dating" is worse than nothing: it fills the space where the reason
  should be and tells a reader there is not one.
- **One paragraph naming things a reader could go and check** — a register, a
  former employer, a study, a book. The test is whether a sceptical reader
  could leave the page and verify a sentence of it.
- **A link to more of their work, where a page of it exists.** Delete the last
  paragraph otherwise; a link into nothing costs more than it gives.

**Pairing.** Last in the run of writing: under the final `prose-column`, above
`colophon`. On an article, `article-masthead` at the top of the same page,
whose byline this completes; on a safety page the opener is a hero and there is
no byline to complete. `source-note` belongs with the claims inside the body
and answers a different question — where a figure came from, not who wrote it.

`one-per-page` is `yes`. A piece has one author block, and two of them is two
answers to one question; a co-written piece puts both names in the one block.

**Brand adaptability.** `--color-surface-soft` is the panel and `--card-radius`
and `--card-border` its shape, so the block inherits whatever a brand's cards
already look like. The top rule is `--color-primary` and is the only place the
brand colour appears; it is decoration, nothing depends on seeing it, and a
brand wanting the panel quieter can flatten the card edge and leave it.

`--font-heading` sets the label and the name, so both ride `--type-scale`. The
label is `0.875rem`, not the `0.8125rem` of the library's undialled eyebrows: a
size that moves has to clear the 12px text floor at the bottom of the dial's
documented range as well as at `1`, and `0.8125rem` renders 11.7px at `0.9`.
Nothing here measures that — every gate renders at the token set's own scale.
The name is the one display size and takes `--color-text`, not
`--color-heading`: that token is promised against the page ground, and this
text sits on a panel.

**The link inherits its ink** and is underlined. On a tinted panel the one ink
the contract guarantees is the body one, and colour alone never marks a link.
The bio stops at `62ch`, which is a body measure and holds a character count
rather than a width.
