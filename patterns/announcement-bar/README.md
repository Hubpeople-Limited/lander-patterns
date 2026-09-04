# announcement-bar

**What it is and when to use it.** A slim band above the site header carrying
one line and one link: "Free to join this month", "Now in Manchester", "Our
summer events are open". It is the cheapest conversion lever a site has,
because it is on every page a visitor lands on and costs nothing below it.
Use it when the brand has one piece of news that is true this month and a page
that carries it. Take it off when the news stops being news; a bar that has said
the same thing for a year is furniture, and visitors learn to skip furniture.

Not for a second call to action - the join control is the header's and the
page's - and not for anything that needs a second sentence. A second sentence
is a section, and sections go on the page.

**What it needs.** One line of real news the brand can stand behind: an offer
that exists, a place newly served, a date that is true. The page it links to,
which must exist. And a name for the bar itself (`bar-label`), two or three
words for assistive technology - "Announcement", "This month".

**Placement.** The first element of the page body, above `masthead-nav`. It
scrolls away with the page; a header on `sticky=pinned` or `sticky=compact`
pins as it did once the bar has gone. It is not sticky itself, on purpose: a
bar that stays takes 44px from every screen on a phone. `one-per-page` is
literal, and the same bar goes on every page of the site or on none - a
message that appears on the homepage and vanishes on the pricing page reads
as an error rather than a choice.

**Pairing.** Above the header, and nothing else. It does not count against a
recipe's ground run: it is furniture, decided once for the site, like the
header and the footer.

**Brand adaptability.** One axis.

| Axis | Rungs | What it moves |
|---|---|---|
| `ground` | `brand`, `deep` | the brand colour with `--color-on-primary`, or the dark ground with `--color-on-scrim` - the two rungs whose ink the contract promises. Choose the one the header is not on: a brand-colour bar over a brand-colour header is one tall bar |

The link is text, underlined and bold, in the ink of its ground; the focus
ring is that ink too, because `--color-focus` is a brand colour and would land
on a brand colour. The band is 44px at its shortest so the link is reachable by
thumb without being drawn as a button, which would compete with the join
control a few pixels below it.
