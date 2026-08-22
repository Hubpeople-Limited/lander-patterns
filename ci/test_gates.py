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


def check_modules():
    """Every gate module, both directions."""
    import legibility
    from _containment import external_faults, spacing_faults
    from _heading_size import heading_size_faults
    failures = []

    def run(label, cases, fn):
        for source, want, name in cases:
            got = 1 if fn(source) else 0
            ok = got == want
            verb = "catches" if want else "quiet on"
            print(f"  {'ok  ' if ok else 'FAIL'} {label} {verb}: {name}")
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
    if failures:
        print(f"{len(failures)} gate check(s) not behaving: "
              + ", ".join(failures))
        return 1
    total = (len(CASES) + 1 + len(BYPASSES) + len(QUIET) + len(LEGIBILITY)
             + len(SPACING) + len(EXTERNAL_CSS) + len(EXTERNAL_HTML)
             + len(HEADING))
    print(f"clean: {total} gate cases across five modules behave as documented.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
