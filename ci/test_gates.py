"""Proof that each gate fires, and that it stays quiet on valid CSS.

Run: python ci/test_gates.py

Both halves matter. A check that never fires is worse than no check, because
it converts an unknown into a false assurance - but a check that fires on
`--type-scale: 1.1 !important` teaches whoever hits it to stop reading the
output, which arrives at the same place by a longer road.

This file covers every module the gates live in. It began covering two of
them, and the three it left out are precisely the three that a later review
found nine defects in - so the scope of this file is not a detail, it is the
thing that decides which defects survive.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import brand_fit  # noqa: E402

EVERY = sorted({t for n in brand_fit.pattern_needs().values() for t in n})
COMPLETE = "".join("%s:#c2185b;" % t for t in EVERY)

# Every brand below defines every token the patterns need, so the only thing
# that can move the exit code is the dial. That is the point: the first
# version of this check returned an exit code derived from the token census,
# which made it look like it was working on any incomplete brand.
CASES = [
    ("a unit",                ":root{%s--type-scale:1.2rem;}", 1),
    ("zero",                  ":root{%s--type-scale:0;}", 1),
    ("negative",              ":root{%s--type-scale:-1;}", 1),
    ("a unit on the density dial", ":root{%s--space-scale:1.2px;}", 1),
    ("out of the documented range", ":root{%s--type-scale:999;}", 0),
    ("valid with !important", ":root{%s--type-scale:1.1 !important;}", 0),
    ("valid with a comment",  ":root{%s--type-scale:1.1 /* airy */;}", 0),
    ("valid, plain",          ":root{%s--type-scale:1.1;}", 0),
    ("valid, no dial at all", ":root{%s}", 0),
    ("a unit inside calc()", ":root{%s--type-scale:calc(1.1px);}", 1),
    ("a viewport unit inside calc()", ":root{%s--type-scale:calc(1.1vmin);}", 1),
    ("a unit inside clamp()",
     ":root{%s--type-scale:clamp(0.9, 1.1vmin, 1.2);}", 1),
    ("a genuine computation", ":root{%s--type-scale:calc(16 / 16);}", 0),
    ("the brand's own indirection",
     ":root{%s--type-scale:var(--brand-density, 1);}", 0),
    ("ramp defined on a dial that is never declared",
     ":root{%s--space-1:calc(0.25rem * var(--space-scale));}", 1),
    ("ramp on a dial with a fallback",
     ":root{%s--space-1:calc(0.25rem * var(--space-scale, 1));}", 0),
]


# Every technique that got a hard-coded display size past the first version of
# check_display_type_carries_the_dial. Each one is a real way a stylesheet
# gets written, not a contrivance - which is why the gate missed them.
BYPASSES = {
    "face and size declared in separate rules":
        ".a, .b { font-family: var(--font-heading); } .a { font-size: 2rem; }",
    "media-query override of a size that does carry the dial":
        ".a { font-family: var(--font-heading);"
        " font-size: calc(2rem * var(--type-scale, 1)); }"
        "@media (width < 30rem) { .a { font-size: 1.5rem; } }",
    "no trailing semicolon on the last declaration":
        ".a { font-family: var(--font-heading); font-size: 2rem }",
    "a second font-size overriding a scaled one":
        ".a { font-family: var(--font-heading);"
        " font-size: calc(2rem * var(--type-scale, 1)); font-size: 2rem; }",
    "the font shorthand":
        ".a { font: 800 2rem/1.02 var(--font-heading); }",
    "a -title class with the face set on an ancestor":
        ".card { font-family: var(--font-heading); } .card-title { font-size: 2rem; }",
    "a bare h2 with no face declared anywhere":
        ".x h2 { font-size: 2rem; }",
}

# Valid CSS the gate must stay quiet on. A check that cries wolf on the
# standard button reset teaches people to stop reading its output, which
# arrives at a blind gate by a longer road.
QUIET = {
    "a correctly scaled size":
        ".a { font-family: var(--font-heading);"
        " font-size: calc(2rem * var(--type-scale, 1)); }",
    "font: inherit on a button":
        ".a { font-family: var(--font-heading); } .a button { font: inherit; }",
    "body copy":
        ".a-sub { font-size: 1rem; }",
    "font-size: inherit":
        ".a { font-family: var(--font-heading); } .a span { font-size: inherit; }",
}


def check_display_type():
    from _display_type import display_faults
    failures = []
    for label, css in BYPASSES.items():
        caught = bool(display_faults(css))
        print(f"  {'ok  ' if caught else 'FAIL'} catches: {label}")
        if not caught:
            failures.append(label)
    for label, css in QUIET.items():
        quiet = not display_faults(css)
        print(f"  {'ok  ' if quiet else 'FAIL'} quiet on: {label}")
        if not quiet:
            failures.append(label)
    return failures


# ci/legibility.py. Every case below is one a review found: the first five
# were false positives introduced by widening the check, the rest are the
# defect it exists to catch, written the ways it could not previously see.
LEGIBILITY = [
    ('.t::before { content: ""; background: red; opacity: 0.08; }', 0,
     "a decorative scrim"),
    ('.t:disabled { opacity: 0.5; }', 0, "a disabled control"),
    ('.t img:hover { opacity: 0.85; }', 0, "an image fade"),
    ('.t-label { opacity: 0.95; }', 0, "a cosmetically irrelevant fade"),
    ('.t-label { opacity: 95%; }', 0, "the same, as a percentage"),
    ('.t-label { opacity: 0.08; }', 1, "text faded, no ink named"),
    ('.t-label { color: var(--color-text); opacity: 0.08; }', 1,
     "text faded with an ink"),
    ('.t-label { opacity: 8%; }', 1, "a fade written as a percentage"),
    ('.t-label { opacity: var(--fade); }', 1, "an unverifiable fade"),
    ('.t-label { filter: opacity(8%); }', 1, "the filter form"),
    ('.t svg + .t-label { opacity: 0.08; }', 1,
     "an element name in an ancestor, not the subject"),
    ('.t-item::before, .t-label { opacity: 0.08; }', 1,
     "a list with one decorative member"),
    ('.t::before { content: "Step one"; opacity: 0.3; }', 1,
     "a pseudo-element carrying words"),
    ('@media (min-width: 1px) { .t-label { display: none; } }', 1,
     "an at-rule true on every device"),
    ('@supports (color: var(--x)) { .t-label { display: none; } }', 1,
     "an at-rule true on every engine"),
    ('@media (min-width: 48rem) { .t-label { display: none; } }', 0,
     "an at-rule that genuinely discriminates"),
    # These three had NO coverage, and that is why a `continue` added to the
    # fade block above them turned all three off without anything noticing.
    # They are the checks this file exists for: nothing else in the repository
    # compares an ink to a ground.
    ('.t-label { color: var(--color-bg); }', 1,
     "ink painted in the page's own ground"),
    ('.t-label { color: var(--color-surface-soft); }', 1,
     "ink painted in a surface"),
    ('.t-label { position: absolute; left: -9999px; }', 1, "moved off canvas"),
    ('.t-label { color: color-mix(in srgb, var(--color-text) 8%, '
     'transparent); }', 1, "ink mixed to near-transparent"),
    ('.t-label { opacity: 0.95; color: var(--color-bg); }', 1,
     "a cosmetic fade must not mask the ground check beneath it"),
    ('.t-label { color: var(--color-text); }', 0, "an ordinary ink"),
    # Subject resolution, which decides whether a fade is on text.
    ('.t img[alt~="icon"] { opacity: 0.3; }', 0,
     "an attribute selector on an image"),
    ('.t img:not(.a > .b) { opacity: 0.3; }', 0,
     "a functional pseudo-class on an image"),
    ('.t-label[data-x~="a b"] { opacity: 0.3; }', 1,
     "an attribute selector on text"),
    ('.t-label { filter: opacity(0); }', 1, "a fully-zero filter fade"),
    # Every spelling of nothing. Narrowing one regex left two of these
    # matching neither it nor the other.
    ('.t-label { opacity: .0; }', 1, "a fade written .0"),
    ('.t-label { opacity: 00%; }', 1, "a fade written 00%"),
    ('.t-label { opacity: 1; }', 0, "fully opaque"),
    ('.t-label { opacity: 100%; }', 0, "fully opaque, as a percentage"),
    # Subjects that a change made for one reason switched off.
    ('.btn[disabled] { opacity: 0.4; }', 0, "a disabled control by attribute"),
    ('.btn[aria-disabled="true"] { opacity: 0.4; }', 0, "aria-disabled"),
    ('.card :is(img, svg) { opacity: 0.4; }', 0, ":is() naming the subject"),
    ('.card :where(img, svg) { opacity: 0.4; }', 0, ":where() naming it"),
    ('.card:has(> img) { opacity: 0.4; }', 1, ":has() qualifying text"),
    # Subject resolution across nested brackets. Each of these came from a
    # fix that worked on the simple form and not on the nested one.
    ('.t-label:not(:is(img)) { opacity: 0.3; }', 1,
     "a rule that explicitly excludes images"),
    ('.card:has(.media :is(img, svg)) { opacity: 0.3; }', 1,
     ":has() wrapping an :is()"),
    ('.card :is(img, .t-label) { opacity: 0.3; }', 1,
     "a mixed :is() list, decorative member first"),
    ('.card :is(.t-label, img) { opacity: 0.3; }', 1,
     "the same list, other order - the verdict must not depend on it"),
    ('img[ alt="x" ] { opacity: 0.3; }', 0,
     "legal whitespace inside a bracket"),
    ('img/*c*/.hero-label { opacity: 0.3; }', 0,
     "a comment inside a compound selector joins, it does not separate"),
    # The subject is expanded into the selectors it stands for. Every one of
    # these was a defect in a previous version of that expansion.
    ('.tile :is(.lead, .meta)::before { opacity: 0.4; content: ""; }', 0,
     "a decorative pseudo-element whose compound carries an :is()"),
    ('.card :is(.a, .b):is(img, svg) { opacity: 0.3; }', 0,
     "two :is() groups, decorative group last"),
    ('.card :is(img, svg):is(.a, .b) { opacity: 0.3; }', 0,
     "the same two groups, decorative group first"),
    ('.card :is(img, svg).b { opacity: 0.3; }', 0,
     "a class written after the group"),
    ('.card :is(.t-label:nth-of-type(2), img) { opacity: 0.3; }', 1,
     "a nested paren inside the :is() argument"),
    ('.card :is(.t-label, :is(img)) { opacity: 0.3; }', 1, "a nested :is()"),
    ('.t-label:is() { opacity: 0.3; }', 1,
     "an empty list stands for nothing, not for everything"),
    # Expansion has to fail CLOSED wherever it gives up.
    ('.card :is(.x,.y):is(.x,.y):is(.x,.y):is(.x,.y):is(img,.t-label)'
     ' { opacity: 0.3; }', 1, "more groups than the expansion will expand"),
    ('.card :is(.x:is(.x:is(.x:is(.x:is(img,.t-label))))) { opacity: 0.3; }',
     1, "nested deeper than the expansion will go"),
    ('.t-label:is(imgx { opacity: 0.3; }', 1, "an unterminated group"),
    ('.card .x:is(img .b, svg .b) { opacity: 0.3; }', 1,
     "a complex member whose ancestor is decorative and whose subject is not"),
    ('.card :is(img .b, svg .b) { opacity: 0.3; }', 1, "the headless form"),
    # The cap must not fire on a subject that is already concrete: testing it
    # before looking for a group made four groups report and three not.
    (".card:is(.dark,.light):is(.a0,.b0):is(.a1,.b1):is(.a2,.b2)::after"
     " { content: ''; opacity: 0.35; }", 0,
     "four groups, fully expanded, decorative"),
    (".card:is(.dark,.light):is(.a0,.b0):is(.a1,.b1)::after"
     " { content: ''; opacity: 0.35; }", 0, "three groups, the control"),
    # An unterminated group fails closed in BOTH directions - the raw text
    # must never reach the decorative search.
    ('.t-label:is(img { opacity: 0.3; }', 1,
     "unterminated, with a decorative name inside it"),
    ('.t-label:where(svg { opacity: 0.3; }', 1, "unterminated :where()"),
    ('.card :is(.t-label, .z:is(img) { opacity: 0.3; }', 1,
     "unterminated outer group, terminated inner one"),
    # :is() attaches to its compound, so a complex member contributes its
    # ancestors as ancestors - only its last compound joins the head.
    ('img:where(.prose *) { opacity: 0.4; }', 0,
     "an image qualified by an ancestor"),
    ('img:is(.card *, .tile *) { opacity: 0.4; }', 0,
     "the same, with two members"),
    ('svg:where(.btn *) { opacity: 0.4; }', 0,
     "an svg qualified by an ancestor"),
]

# ci/_containment.py, spacing half.
SPACING = [
    ("a { padding: 96px; }", 1, "a hardcoded length"),
    ("a { margin-top: -24px; }", 1, "a negative length"),
    ("a { padding: 72pt; }", 1, "an absolute unit that is not px"),
    ("a { padding: 96px 1%; }", 1, "a percentage beside a length"),
    ("a { padding: var(--nope, 96px); }", 1, "a var() fallback"),
    ("a { --x: 96px; padding: var(--x); }", 1, "one hop of indirection"),
    ("a { --a: 96px; --b: var(--a); padding: var(--b); }", 1, "two hops"),
    ("a { grid-gap: 96px; }", 1, "the legacy alias"),
    ("a { padding: var(--space-8); }", 0, "on the ramp"),
    ("a { padding: calc(var(--space-4) * 2); }", 0, "calc on the ramp"),
    ("a { --a: var(--space-4); --b: var(--a); padding: var(--b); }", 0,
     "two hops onto the ramp"),
    ("a { gap: 1px; }", 0, "a hairline"),
    ("a { gap: 0.1em; }", 0, "an optical nudge"),
    ("a { margin: 0 auto; }", 0, "auto centring"),
    ("a { margin-left: calc(50% - 50vw); }", 0, "a full-bleed breakout"),
    ("a { margin-top: -100vh; }", 0, "a curtain pulled up one screen"),
    # A token NAME that embeds a unit is a name, not a length.
    ("a { padding: var(--gutter-16px); }", 0, "a token name embedding a unit"),
    ("a { gap: var(--icon-24px); }", 0, "the same, on a gap"),
    (":root{--a:var(--gutter-16px);} a { padding: var(--a); }", 0,
     "a unit-bearing name surviving one hop"),
    (":root{--a:96px;} a { padding: var(--a); }", 1,
     "a real length through one hop"),
    (":root{--a:var(--space-6, 96px);} a { padding: var(--a); }", 0,
     "a local that reaches the ramp, with a fallback"),
    (":root{--a:calc(var(--space-4) + 8px);} a { padding: var(--a); }", 0,
     "a local computed from the ramp"),
    ("a { padding: calc(var(--space-4) + 8px); }", 0,
     "the same value written inline"),
    (":root{--a:var(--b) 96px; --b:var(--space-2);}"
     " a { padding: var(--a); }", 1,
     "a literal beside a ramp reference, one hop"),
    (":root{--a:var(--b); --b:var(--c) 96px; --c:var(--space-2);}"
     " a { padding: var(--a); }", 1, "the same, two hops down"),
    (":root{--b:var(--space-2);} a { padding: var(--b) 96px; }", 1,
     "the inline equivalent of both"),
    (":root{--a:var(--b); --b:calc(var(--space-4) + 8px);}"
     " a { padding: var(--a); }", 0, "the ramp reached two hops out"),
    (":root{--a:var(--b); --b:var(--space-6, 96px);}"
     " a { padding: var(--a); }", 0, "the same, with a fallback"),
    (":root{--a:var(--b); --b:96px;} a { padding: var(--a); }", 1,
     "a hardcoded length two hops out"),
    (":root{--a:var(--b); --b:var(--a);} a { padding: var(--a); }", 0,
     "a reference cycle must terminate"),
]

# ci/_containment.py, external half.
EXTERNAL_CSS = [
    ('@import url("https://x.invalid/e.css");', 1, "@import"),
    ("a { background-image: url(https://x.invalid/t.png); }", 1,
     "a remote background"),
    ("@font-face { src: url(//x.invalid/f.woff2); }", 1, "a remote font"),
    ("a { background: image-set('a.png' 1x, '//x.invalid/b.png' 2x); }", 1,
     "a later image-set candidate"),
    ("/* @namespace note */ a { background: url(https://x.invalid/x.png); }", 1,
     "a comment mentioning an at-rule"),
    ("@namespace svg url(https://www.w3.org/2000/svg);", 0,
     "a real namespace declaration"),
    ("a { background: url(./local.png); }", 0, "a relative path"),
    ("a { background: url(data:image/svg+xml,%3Csvg/%3E); }", 0, "a data URI"),
    ('/* was: @import url("https://x.invalid/e.css"); */', 0,
     "a commented-out import"),
    # One reference is one finding - and two references are two, even when
    # they name the same URL on the same line.
    ("a { background: url(https://a.invalid/1.png), "
     "url(https://a.invalid/1.png); }", 2, "the same URL twice on one line"),
    ("a{background:url(https://x.invalid/a.png);"
     "background-image:url(https://x.invalid/b.png);}", 2,
     "two distinct URLs"),
]

EXTERNAL_HTML = [
    ('<img src="https://x.invalid/t.gif">', 1, "a third-party image"),
    ("<img src=https://x.invalid/t.gif>", 1, "unquoted"),
    ('<img src="&#104;ttps://x.invalid/t.gif">', 1, "an entity-encoded scheme"),
    ('<img srcset="a.png 1x, //x.invalid/b.png 2x">', 1, "a srcset candidate"),
    ('<a href="/x" ping="https://x.invalid/t">go</a>', 1, "a ping attribute"),
    ('<use href="https://x.invalid/s.svg#i"/>', 1, "a remote sprite"),
    ('<img src="slot:hero-image">', 0, "a slot placeholder"),
    ('<a href="{{join.url}}">j</a>', 0, "platform furniture"),
]

# ci/_heading_size.py.
HEADING = [
    ('.x { color: var(--color-heading); font-size: clamp(1.5rem,3vw,2rem); }',
     1, "a floor under the bar"),
    ('.x { color: var(--color-heading); '
     'font-size: calc(1.25rem * var(--type-scale, 1)); }', 1,
     "the form the display gate itself prescribes"),
    ('.x { color: var(--color-heading); font-size: max(1.5rem, 2vw); }', 1,
     "max() rather than clamp()"),
    ('.x { color: var(--color-heading); } .x { font-size: 1.25rem; }', 1,
     "ink and size in separate rules"),
    ('.m { --i: var(--color-heading); } .x { color: var(--i); '
     'font-size: 1.25rem; }', 1, "the ink reached through a ground modifier"),
    ('.x { color: var(--color-heading); '
     'font-size: clamp(1.75rem,3vw,2.25rem); }',
     0, "a floor that clears the bar across the dial range"),
    ('.x { color: var(--color-heading); font-size: 1.25rem; '
     'font-weight: 700; }', 1, "bold, and still under its own lower bar"),
    ('.x { color: var(--color-text); font-size: 1rem; }', 0,
     "body ink at any size"),
    ('.x { color: var(--color-heading); '
     'font-size: clamp(2rem, 1.2rem + 3vw, 3.4rem); }', 0,
     "a middle argument smaller than the floor"),
]


# Header validation lives in lint.py and had no coverage here at all - which is
# the shape of this file's own docstring warning, since the three modules it
# originally left out are the three a later review found nine defects in. Both
# gates below were added in one session and proven by breaking something once;
# once is not every push.
SHAPE_CASES = [
    ("peer set", 0, "a shape the building skill names"),
    ("comparison", 0, "the shape a new pattern was built for"),
    ("question and answer", 0, "a multi-word shape"),
    ("ordered set", 1, "the library's own old spelling"),
    ("single article", 1, "the library's other old spelling"),
    ("matrix", 1, "a shape nobody defined"),
    ("Peer Set", 1, "the right shape, wrong case"),
    ("", 1, "an empty shape"),
]

VARIANT_CASES = [
    ("ground=plain|soft|brand|deep", 0, "all four rungs of the ladder"),
    ("ground=plain; alignment=default|centred", 0, "two axes, one line"),
    ("rule=default|ruled", 0, "an axis that is not the ground"),
    ("ground=light", 1, "the rung spelling that predates the ladder"),
    ("ground=inverse", 1, "a rung nobody defined"),
    ("ground=plain|soft|midnight", 1, "one bad rung among good ones"),
    ("Ground = Plain, Soft", 1, "the shape a person would write by hand"),
    ("ground", 1, "an axis with no values"),
    ("ground=", 1, "an axis with an empty value list"),
]


def check_header():
    """The two header gates added with the variation work, both directions."""
    import lint
    failures = []

    def run(label, cases, fn):
        for value, want, name in cases:
            before = len(lint.findings)
            fn(value)
            got = 1 if len(lint.findings) > before else 0
            del lint.findings[before:]
            ok = got == want
            verb = "catches" if want else "quiet on"
            extra = "" if ok else f" (got {got}, want {want})"
            print(f"  {'ok  ' if ok else 'FAIL'} {label} {verb}: {name}{extra}")
            if not ok:
                failures.append(f"{label}: {name}")

    here = Path(__file__)

    def shape(value):
        if value and value not in lint.SHAPES:
            lint.find(here, "header", f"content-shape {value!r}")
        elif not value:
            lint.find(here, "header", "missing content-shape")

    def variants(value):
        axes = lint.parse_variants(value)
        if axes is None:
            lint.find(here, "variants", f"malformed {value!r}")
            return
        for rung in axes.get("ground", []):
            if rung not in lint.GROUND_RUNGS:
                lint.find(here, "variants", f"ground={rung}")

    run("content-shape", SHAPE_CASES, shape)
    run("ground ladder", VARIANT_CASES, variants)
    return failures


def check_modules():
    """Every gate module, both directions."""
    import legibility
    from _containment import external_faults, spacing_faults
    from _heading_size import heading_size_faults
    failures = []

    def run(label, cases, fn):
        # EXACT counts, not truthiness. A `want` of 1 compared with `if fn(x)`
        # passed on one finding or five, so the deduplication work in
        # _containment had no test that could have failed if it regressed.
        for source, want, name in cases:
            got = len(fn(source))
            ok = got == want
            verb = "catches" if want else "quiet on"
            extra = "" if ok else f" (got {got}, want {want})"
            print(f"  {'ok  ' if ok else 'FAIL'} {label} {verb}: {name}{extra}")
            if not ok:
                failures.append(f"{label}: {name}")

    def legible(css):
        out = []
        legibility.check(css, lambda d: out.append(d),
                         "<p class='t-label'>x</p>")
        return out

    run("legibility", LEGIBILITY, legible)
    run("spacing", SPACING, spacing_faults)
    run("external", EXTERNAL_CSS, lambda s: external_faults(s, "css"))
    run("external", EXTERNAL_HTML, lambda s: external_faults(s, "html"))
    run("heading-size", HEADING, heading_size_faults)
    return failures


def run(base):
    return subprocess.run([sys.executable, str(HERE / "brand_fit.py"), base],
                          capture_output=True, text=True).returncode


# --------------------------------------------------------------- page level
#
# Every other suite here proves a gate fires on one pattern. This one proves
# the page-level checks fire on one PAGE, which is a different question and
# the reason ci/check_page.py exists: the defect that made the case for it
# passed every single-pattern gate in this repo.

PAGE_FIRES = [
    ("two openers that name each other",
     ["homepage", "hero-overlay", "hero-split"], "avoid-with"),
    ("the same one-per-page section twice",
     ["homepage", "hero-overlay", "hero-overlay", "stats-band"], "one per page"),
    ("a pricing section on a homepage",
     ["homepage", "pricing-tiers", "cta-band"], "page type"),
    ("a heading level skipped between neighbours",
     ["homepage", "hero-stated:ground=deep", "benefit-tiles"], "headings"),
    ("two neighbours on the same ground",
     ["homepage", "hero-stated:ground=deep", "claim-stack:ground=deep"], "ground"),
    ("no h1 anywhere on the page",
     ["homepage", "stats-band", "cta-band"], "headings"),
]


def run_page(argv):
    got = subprocess.run([sys.executable, str(HERE / "check_page.py")] + argv,
                         capture_output=True, text=True, encoding="utf-8")
    return got.returncode, (got.stdout or "") + (got.stderr or "")


def check_pages():
    """Both halves, as everywhere else: it fires, and it stays quiet.

    The quiet half is the fixtures in page-recipes.json, and it is the half
    that earns its keep day to day - those are real compositions, so a pattern
    edit that breaks one is a page somebody would have shipped.
    """
    failures = []
    print("ci/check_page.py, page-level checks")

    for label, argv, want_label in PAGE_FIRES:
        code, out = run_page(argv)
        ok = code == 1 and ("[%s]" % want_label) in out
        print(f"  {'ok  ' if ok else 'FAIL'} {label:<46} exit={code} want=1 [{want_label}]")
        if not ok:
            failures.append(label)

    # The fold, proven against the build it actually shipped on. A rule tested
    # only against the fixed pattern proves nothing: it would pass just as well
    # if it were measuring the wrong thing, or nothing at all.
    # Bytes, not text, for the whole round trip. The first version of this read
    # and wrote through the text API and handed the file back with every line
    # ending rewritten - content identical, working copy modified, git warning
    # about CRLF on a file nobody had edited. A test that touches the repo has
    # to put it back byte for byte, and this one now asserts that it did.
    folder = HERE.parent / "patterns" / "hero-overlay"
    css = folder / "pattern.css"
    kept = css.read_bytes()
    try:
        css.write_bytes(
            kept.replace(b"min-height: calc(100svh - var(--hero-overlay-above, 4.5rem));",
                         b"min-height: 100svh;"))
        code, out = run_page(["homepage", "hero-overlay", "stats-band", "cta-band"])
        ok = code == 1 and "[the fold]" in out
        label = "a full-viewport opener that subtracts nothing"
        print(f"  {'ok  ' if ok else 'FAIL'} {label:<46} exit={code} want=1 [the fold]")
        if not ok:
            failures.append(label)
    finally:
        css.write_bytes(kept)

    if css.read_bytes() != kept:
        failures.append("the fold case did not restore hero-overlay byte for byte")
        print("  FAIL  the fold case left patterns/hero-overlay/pattern.css changed")

    recipes = json.loads((HERE / "page-recipes.json").read_text(encoding="utf-8"))
    for recipe in recipes["recipes"]:
        argv = [recipe["page"]] + recipe["patterns"]
        code, out = run_page(argv)
        ok = code == 0
        label = "%s: %s" % (recipe["page"], " ".join(recipe["patterns"]))
        print(f"  {'ok  ' if ok else 'FAIL'} {label[:46]:<46} exit={code} want=0")
        if not ok:
            failures.append(label)
            for line in out.splitlines():
                if "FAIL" in line:
                    print(f"        {line.strip()}")

    return failures


def main():
    base = os.path.join(tempfile.gettempdir(), "lander-dial-test")
    failures = []

    for label, template, want in CASES:
        shutil.rmtree(base, ignore_errors=True)
        os.makedirs(os.path.join(base, "acme"))
        Path(base, "acme", "global.css").write_text(template % COMPLETE,
                                                    encoding="utf-8")
        got = run(base)
        ok = got == want
        print(f"  {'ok  ' if ok else 'FAIL'} {label:<46} exit={got} want={want}")
        if not ok:
            failures.append(label)

    # A brand ships more than one stylesheet, and the fault only has to be in
    # the one the live page loads. Scanning only the deepest global.css missed
    # exactly this pair.
    label = "fault in a sheet the token census skips"
    shutil.rmtree(base, ignore_errors=True)
    os.makedirs(os.path.join(base, "acme", "assets"))
    os.makedirs(os.path.join(base, "acme", "for-toolkit", "site"))
    Path(base, "acme", "assets", "global.css").write_text(
        ":root{--type-scale:1.2rem;}", encoding="utf-8")
    Path(base, "acme", "for-toolkit", "site", "global.css").write_text(
        ":root{%s}" % COMPLETE, encoding="utf-8")
    got = run(base)
    ok = got == 1
    print(f"  {'ok  ' if ok else 'FAIL'} {label:<46} exit={got} want=1")
    if not ok:
        failures.append(label)

    shutil.rmtree(base, ignore_errors=True)
    print()
    failures += check_display_type()
    print()
    failures += check_modules()
    print()
    failures += check_header()
    print()
    failures += check_pages()
    print()
    if failures:
        print(f"{len(failures)} gate check(s) not behaving: "
              + ", ".join(failures))
        return 1
    recipes = json.loads((HERE / "page-recipes.json").read_text(encoding="utf-8"))
    total = (len(CASES) + 1 + len(BYPASSES) + len(QUIET) + len(LEGIBILITY)
             + len(SPACING) + len(EXTERNAL_CSS) + len(EXTERNAL_HTML)
             + len(HEADING) + len(SHAPE_CASES) + len(VARIANT_CASES)
             + len(PAGE_FIRES) + 1 + len(recipes["recipes"]))
    print(f"clean: {total} gate cases across seven modules behave as documented.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
