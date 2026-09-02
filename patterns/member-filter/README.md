# member-filter

**What it is and when to use it.** A row of pills that switches between two or
three live member blocks — everyone, then women, then men, or three age bands,
or three towns. Each pill reveals one `member-grid`, and each grid is scoped
differently by the platform.

It runs on a radio group and one CSS rule. **No JavaScript**, so it works on a
page that carries none, and it works before, during and after hydration because
there is nothing to hydrate.

Use it where a visitor genuinely arrives wanting one slice of the members and
the page can honestly offer it. Do **not** use it to pad a thin set: three pills
over the same twelve people is three controls that do nothing, and a visitor
finds that out in one tap. Where there is only one set worth showing, use
`member-grid` on its own — that is the normal case, not the fallback.

Not to be confused with `picker-chips`, which looks similar and does the
opposite: those pills leave the page for the join flow, these change what is on
it. One page should not carry both — two rows of pills that behave differently
is a page teaching the visitor that its controls are unpredictable.

**What it needs.** Two or three **genuinely different** member sets, the
brand's own word for each pill, and one word for what the pills do. Nothing
else, and nothing from the partner — the platform supplies the members.

Be aware of the cost: **each panel is another query the platform runs when the
page is built.** Three panels is three. Two is usually plenty.

**Pairing.** `member-grid` goes inside it — one per panel, and that is what it
is for. `heading-block` above it, because the fieldset's own legend labels the
pills, not the section. `cta-band` below.

**Brand adaptability.** `--color-primary` does most of the work: it is the
selected pill's fill, the unselected pill's text, and its hairline at 28%.
`--chip-radius` decides whether the pills read as pills or as tabs — full round
is friendlier, a small radius reads as a toolbar. `--color-primary-light` is
the hover ground.

There are no variants. The pills take the brand's shape from `--chip-radius`
like every other chip in the library, and a second look here would be a second
way to draw a control the visitor has already learned elsewhere on the page.

**Two things that will break it silently.** Every radio must stay a direct
child of the fieldset and sit **before** every panel — the switch is
`:checked ~ .member-filter-panel`, which reaches later siblings only. And
`filter-name` must be unique on the page: two radio groups sharing a name fight
each other, and the pills start deselecting one another.
