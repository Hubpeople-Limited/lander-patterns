# history-timeline

**What it is and when to use it.** The brand's own story as dated moments
down a hairline: when it began, its first event, an app, a place opened,
each with its date, a title, a line and, where there is one, a photograph.
On a wide screen the moments alternate either side of a centred line; on a
phone they stack beside a line at the start edge. Three to eight moments
read best. Use it on an about page or a landing page when the brand has
given the dates of its own story; it gives an about page with no founder to
put forward a shape of its own.

**Real moments, real dates.** It works best with the moments the brand
really had, in its own words, each with the date it happened, and its own
photographs of them. Every date and every figure is the brand's to give: a
date is never worked out or filled in, and a figure in a moment ("our
thousandth member") comes from the platform's own counts. A moment with no
date stays out. The photograph is optional (`requires: none`), so the slot
is `placeholder=no`: a moment without one closes up.

**The twin, `story-timeline`.** The same timeline for one couple's story, in
their words and their dates, with their OK. The same markup, the same
stylesheet and the same rungs; only the header differs, because it says who
may appear. `ci/test_gates.py` (`check_timelines`) holds the two files
identical. **A change to one is made to both, in the same commit.** They
avoid each other: one timeline per page.

**Four axes.**

| Axis | Rungs |
|---|---|
| `spine` | `centre`, the moments alternating either side of a centred line from 48rem (the default); `start`, every moment on one side at every width |
| `photos` | `with`, a photograph beside each moment that has one (the default); `without`, words only, the archive look |
| `ground` | `plain` (the default) or `soft`: light grounds only, because a hairline and small dates fade on a dark one |
| `motion` | `default`, still; `moving`, each moment eases in as the visitor reaches it |

**Dates and order.** The moments are an `<ol>` and each date a `<time>`
whose `datetime` takes the year, the month or the day (`2016`, `2016-05`,
`2016-05-14`); the date shown is the year alone unless the brand asked for
more. The line and the dots are drawing only. The date is a figure
(`.history-timeline-num`) and never breaks across a line.

**What it needs.** Three to eight moments, each with its date and a title; a
line only where something true fills it; the brand's own photograph at least
1200px wide in landscape where there is one, with alt text. A section
heading, and an eyebrow only when something true fills it.

**Not on a page with `zigzag-rows`:** alternating photographs and words down
the page is the same gesture twice.

**Pairing.** `prose-column` before it for the brand's own account, or after
a `hero-band` opener; `cta-band` after it. It suits an about page or a
landing page, not the homepage.

**Movement** (`motion`). Still by default. On `moving` each moment eases in
through the behaviour library's `reveal` as the visitor reaches it. The line
never draws itself as the page scrolls, and nothing moves under reduced
motion.

**Brand adaptability.** As `story-timeline`: `--font-heading` carries the
heading and the titles, `--color-primary` the dots, `--color-rule` the line,
`--card-radius` the photographs. The heading takes `--color-heading` on the
plain ground and `--color-text` on the soft one.
