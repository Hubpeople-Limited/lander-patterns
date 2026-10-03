# story-timeline

**What it is and when to use it.** One couple's story as dated moments down a
hairline: each a date, a title, a line or two in their words and, where they
have one, a photograph. On a wide screen the moments alternate either side of
a centred line; on a phone they stack beside a line at the start edge. Three
to eight moments read best, the range wedding sites settle on, because
captions get read and essays get skipped. Use it on an about page or a
landing page when a couple who met through the brand has given their story
with its dates.

**A real couple, their dates, shown with their OK.** It works best with the
couple's own words and dates, as they gave them, and their own photographs.
Ask them before their story goes on a public page anyone can reach. The
library ships no sample couple and no drawn stand-in for one (the slot is
`placeholder=no`), and a date is never filled in for them: a moment with no
date stays out.

**The twin, `history-timeline`.** The same timeline for the brand's own
story: founded, a first event, an app, a place opened. The same markup, the
same stylesheet and the same rungs; they are two files because the header
says who may appear (`requires:`, `image-slots:`, `layout:`), and
`ci/test_gates.py` (`check_timelines`) holds the two files' markup,
stylesheet and rung words identical. **A change to one is made to both, in
the same commit.** They avoid each other: one timeline per page.

**Four axes.**

| Axis | Rungs |
|---|---|
| `spine` | `centre`, the moments alternating either side of a centred line from 48rem (the default); `start`, every moment on one side at every width |
| `photos` | `with`, a photograph beside each moment that has one (the default); `without`, words only |
| `ground` | `plain` (the default) or `soft`: light grounds only, because a hairline and small dates fade on a dark one |
| `motion` | `default`, still; `moving`, each moment eases in as the visitor reaches it |

**Dates and order.** The moments are an `<ol>`, so the order is in the
markup, and each date is a `<time>` whose `datetime` takes the year, the
month or the day (`2019`, `2019-06`, `2019-06-14`); the date shown is the
year alone unless the couple asked for more. The line and the dots are
drawing only. The date is a figure (`.story-timeline-num`) and never breaks
across a line.

**A moment with no photograph** closes up: delete its `<img>` and the moment
is its words alone, with no empty frame where the photograph was. On
`centre` its side of the line stays empty, which is the words-only timeline.

**What it needs.** One couple, three to eight moments, each with a date and
a title; a line in their words where they gave one; their own photograph at
least 1200px wide in landscape where they have one, with alt text saying who
is in it. A section heading, and an eyebrow only when something true fills
it.

**Not on a page with `zigzag-rows`:** alternating photographs and words down
the page is the same gesture twice. With `story-cards` on the same page it
can work, the cards for three couples and the timeline for one, but the same
couple in both reads as a repeat.

**Pairing.** `prose-column` before it, so the brand's own account comes
first; `cta-band` after it. It suits an about page or a landing page, not
the homepage.

**Movement** (`motion`). Still by default. On `moving` each moment eases in
through the behaviour library's `reveal` as the visitor reaches it. The line
never draws itself as the page scrolls, and nothing moves under reduced
motion.

**Brand adaptability.** `--font-heading` carries the heading and each
moment's title, `--color-primary` the dots, `--color-rule` the line, and
`--card-radius` rounds the photographs. The heading takes `--color-heading`
on the plain ground and `--color-text` on the soft one.
