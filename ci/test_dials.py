"""Proof that the dial checks fire, and that they stay quiet on valid CSS.

Run: python ci/test_dials.py

Both halves matter. A check that never fires is worse than no check, because
it converts an unknown into a false assurance - but a check that fires on
`--type-scale: 1.1 !important` teaches whoever hits it to stop reading the
output, which arrives at the same place by a longer road.
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
    if failures:
        print(f"{len(failures)} dial check(s) not behaving: "
              + ", ".join(failures))
        return 1
    print(f"clean: {len(CASES) + 1} brand-dial cases and "
          f"{len(BYPASSES) + len(QUIET)} display-type cases behave as documented.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
