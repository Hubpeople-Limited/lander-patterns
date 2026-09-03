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
import re
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

    # The v58 dials. Leading is a multiplier and takes the rules above
    # unchanged; the other two do not, and that is the whole reason
    # _dials.DIALS carries a kind rather than a list of names.
    ("leading with a unit",   ":root{%s--heading-leading:1.1rem;}", 1),
    ("leading at zero",       ":root{%s--heading-leading:0;}", 1),
    ("leading negative",      ":root{%s--heading-leading:-1;}", 1),
    ("leading, valid",        ":root{%s--heading-leading:1.05;}", 0),

    # Tracking is an OFFSET. Zero is its documented default and negative is
    # the ordinary case - 40 of the 41 tracking values in the library are
    # negative, because display type is drawn tight. Reading these two as a
    # multiplier would fail the build on the most obviously correct values a
    # brand can set, which is what these two cases exist to prevent.
    ("tracking at zero, the default", ":root{%s--heading-tracking:0;}", 0),
    ("tracking negative, the ordinary case",
     ":root{%s--heading-tracking:-0.02;}", 0),
    # ...but the unit trap still applies, and here it is at its worst: the
    # declaration drops to `normal`, so the brand loses the tracking the
    # pattern designed rather than merely failing to change it.
    ("tracking with a unit",  ":root{%s--heading-tracking:0.02em;}", 1),
    ("tracking out of range", ":root{%s--heading-tracking:0.9;}", 0),

    ("display weight, valid",   ":root{%s--weight-display:600;}", 0),
    ("display weight at zero",  ":root{%s--weight-display:0;}", 1),
    ("display weight with a unit", ":root{%s--weight-display:700px;}", 1),

    # The brand's own indirection is left alone, and its FALLBACK is not. The
    # fallback is in the same declaration and is the value that ships whenever
    # the brand's property is not set, so exempting the whole var() reopened
    # the unit trap on the dial TOKENS.md calls the worst in the library:
    # var(--brand-track, 0.02em) computes letter-spacing to `normal`.
    ("a unit in the var() fallback, tracking",
     ":root{%s--heading-tracking:var(--brand-track, 0.02em);}", 1),
    ("a unit in the var() fallback, type",
     ":root{%s--type-scale:var(--brand-density, 1.1rem);}", 1),
    ("a unit in the var() fallback, weight",
     ":root{%s--weight-display:var(--brand-weight, 700px);}", 1),
    ("a unit in a NESTED var() fallback",
     ":root{%s--heading-tracking:var(--a, var(--b, 0.5px));}", 1),
    ("an empty var() fallback",
     ":root{%s--heading-tracking:var(--brand-track,);}", 1),
    # ...and the two shapes that must stay quiet, or the exemption's whole
    # reason for existing is gone.
    ("a valid var() fallback",
     ":root{%s--type-scale:var(--brand-density, 1.05);}", 0),
    ("a var() with no fallback at all",
     ":root{%s--heading-tracking:var(--brand-track);}", 0),

    # An empty declaration is a declaration. `--heading-tracking:;` is legal
    # CSS whose value is the empty token sequence: var() substitutes nothing,
    # the calc() is invalid, and letter-spacing computes to `normal`. It is
    # not equivalent to leaving the dial alone, and a value pattern requiring
    # one character could not see it.
    ("an empty declaration", ":root{%s--heading-tracking:;}", 1),
    ("an empty declaration with whitespace",
     ":root{%s--heading-tracking: ;}", 1),

    # Scientific notation is a bare number in CSS. `1e-2` is 0.01 and computes
    # exactly like it, so calling it fatal fails a build on a valid value.
    ("scientific notation", ":root{%s--heading-tracking:1e-2;}", 0),
    ("scientific notation, capital E", ":root{%s--type-scale:1.05E0;}", 0),
    ("scientific notation carrying a unit",
     ":root{%s--type-scale:1e-2rem;}", 1),
]

# Two of the five `lost` sentences named a fallback the browser does not use,
# and a message that sends the reader to the wrong place is worse than one
# that says nothing. Each dial's message must name where the value ACTUALLY
# lands, probed in Chromium:
#
#   --weight-display  font-weight is inherited, so an invalid substitution
#                     hands the element its ANCESTOR's weight, not the
#                     pattern's 700. Ancestor 300 + dial 700px computes 300.
#   --heading-leading calc(1.02 * 1.1rem) is number x length, which is VALID
#                     CSS: 17.952px, fixed and inherited, not a drop.
LOST_PHRASES = {
    ("heading-tracking", "0.02em"): "`normal`",
    ("weight-display", "700px"): "ANCESTOR",
    ("heading-leading", "1.1rem"): "17.952px",
    ("type-scale", "1.1rem"): "inherited",
    ("space-scale", "1.2px"): "fall to 0",
}
# The same dial, wrong on a different axis: an empty --heading-leading really
# does drop, so its message must NOT claim the value stays valid.
LOST_ABSENT = {("heading-leading", ""): "drops"}


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


# A header whose menu is a <details> and whose join control is outside it puts
# the primary call to action behind the scrim for as long as the menu is
# showing. Every other gate here passed that markup: it is valid, its contrast
# is fine, its targets are 44px and it does not scroll sideways. What is wrong
# is which box the control is in.
#
# The quiet half carries the two shapes that would make the check unusable if
# it got them wrong - a pattern with no disclosure at all, which is most of the
# library, and a disclosure nested in a disclosure, where a lazy match ends the
# outer element early and reports a control that is plainly inside it.
DISCLOSURE_FIRES = {
    "the join control outside the disclosure":
        '<details><summary>Menu</summary><nav>x</nav></details>'
        '<a href="{{join.url}}">Join</a>',
    "the login control outside the disclosure":
        '<details><summary>Menu</summary><nav>x</nav></details>'
        '<a href="{{login.url}}">Log in</a>',
    "a numbered join token outside the disclosure":
        '<details><summary>Menu</summary><nav>x</nav></details>'
        '<a href="{{join.0.url}}">Join</a>',
    "a control after the disclosure closes, not before it":
        '<a href="{{login.url}}">Log in</a>'
        '<details><summary>Menu</summary><nav>x</nav></details>',
    "one control inside and one outside":
        '<details><summary>Menu</summary><a href="{{login.url}}">In</a></details>'
        '<a href="{{join.url}}">Out</a>',
}

DISCLOSURE_QUIET = {
    "both controls inside the disclosure":
        '<details><summary>Menu</summary>'
        '<a href="{{login.url}}">Log in</a><a href="{{join.url}}">Join</a>'
        '<nav>x</nav></details>',
    "a pattern with no disclosure at all":
        '<section><a href="{{join.url}}">Join</a></section>',
    "a disclosure holding a second disclosure":
        '<details><summary>Menu</summary>'
        '<details><summary>More</summary><nav>x</nav></details>'
        '<a href="{{join.url}}">Join</a></details>',
    "a control named only in a comment":
        '<details><summary>Menu</summary><nav>x</nav></details>'
        '<!-- the {{join.url}} control belongs inside the disclosure -->',
    "a disclosure with no controls anywhere":
        '<details><summary>Menu</summary><nav>x</nav></details>',
}


def check_disclosure():
    """The gate this change exists for, both directions."""
    import lint
    failures = []
    here = Path(__file__)
    print("ci/lint.py, controls inside the disclosure")

    def run(cases, want):
        for name, markup in cases.items():
            before = len(lint.findings)
            lint.check_disclosure_holds_the_controls(here, markup)
            got = len(lint.findings) - before
            del lint.findings[before:]
            ok = (got > 0) == bool(want)
            verb = "catches" if want else "quiet on"
            extra = "" if ok else f" (got {got} finding(s))"
            print(f"  {'ok  ' if ok else 'FAIL'} {verb}: {name}{extra}")
            if not ok:
                failures.append(name)

    run(DISCLOSURE_FIRES, 1)
    run(DISCLOSURE_QUIET, 0)

    # And against the real pattern, which is the only reason the rule exists.
    # A synthetic fixture proves the function works; this proves the library
    # is actually in the state the function is checking for.
    header = HERE.parent / "patterns" / "masthead-nav" / "pattern.html"
    before = len(lint.findings)
    lint.check_disclosure_holds_the_controls(
        header, header.read_text(encoding="utf-8"))
    got = len(lint.findings) - before
    del lint.findings[before:]
    ok = got == 0
    print(f"  {'ok  ' if ok else 'FAIL'} quiet on: masthead-nav as it ships"
          + ("" if ok else f" ({got} control(s) outside the disclosure)"))
    if not ok:
        failures.append("masthead-nav keeps a control outside its disclosure")
    return failures


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


# A rung is reached by building the class `<pattern-name>--<value>`. That is
# what ci/check_page.py does, what ci/compose.py does through it, and what the
# two browser tools composing from the published bundle do. A pattern that
# spells its modifier any other way ships a rung that is declared, offered in
# the chooser, and returns the default when anybody picks it - with nothing
# anywhere reporting a fault.
MODIFIER_CASES = [
    (".demo-sticky--pinned { position: sticky; }", "sticky=pinned", 1,
     "a modifier with the axis name wedged in the middle"),
    (".demo--static {} .demo--pinned { position: sticky; }",
     "sticky=static|pinned", 0,
     "both rungs spelled the way a variant is applied"),
    (".demo-align--end {}", "menu-align=end", 1,
     "the spelling that shipped a rung nothing could reach"),
    (".demo--menu-end {}", "menu-align=menu-end", 0,
     "a hyphenated value, still reachable"),
    (".demo--ruled {}", "rule=default|ruled", 0,
     "`default` names the markup as it ships and needs no class"),
]


def check_modifier_spelling():
    """A declared rung has to be reachable, not merely present in the file."""
    import lint
    failures = []
    print("ci/lint.py, a declared rung is reachable by the applier")
    root = Path(tempfile.mkdtemp())
    folder = root / "demo"
    folder.mkdir(parents=True)
    html, css = folder / "pattern.html", folder / "pattern.css"
    html.write_text('<div class="demo"></div>', encoding="utf-8")
    # lint.find reports a path relative to the repo, and these fixtures are not
    # in it. Point lint at the fixture root for the duration rather than writing
    # a throwaway pattern into patterns/, where an interrupted run leaves one
    # behind and every later check counts it as part of the library.
    held_root = lint.ROOT
    lint.ROOT = root
    try:
        for sheet, variants, want, name in MODIFIER_CASES:
            css.write_text(sheet, encoding="utf-8")
            before = len(lint.findings)
            lint.check_variants(html, css, {"variants": variants}, "demo")
            got = 1 if len(lint.findings) > before else 0
            del lint.findings[before:]
            ok = got == want
            verb = "catches" if want else "quiet on"
            print(f"  {'ok  ' if ok else 'FAIL'} {verb}: {name}"
                  + ("" if ok else f" (got {got}, want {want})"))
            if not ok:
                failures.append(name)
    finally:
        lint.ROOT = held_root
        shutil.rmtree(root, ignore_errors=True)

    # And the library itself, which is the half that catches the regression.
    unreachable = []
    for pattern in sorted(p for p in (HERE.parent / "patterns").iterdir()
                          if p.is_dir()):
        meta = lint.parse_header(
            (pattern / "pattern.html").read_text(encoding="utf-8"),
            pattern / "pattern.html")
        before = len(lint.findings)
        lint.check_variants(pattern / "pattern.html", pattern / "pattern.css",
                            meta, pattern.name)
        if len(lint.findings) > before:
            unreachable.append(pattern.name)
        del lint.findings[before:]
    ok = not unreachable
    print(f"  {'ok  ' if ok else 'FAIL'} quiet on: every rung in the library"
          + ("" if ok else f" - unreachable in {', '.join(unreachable)}"))
    if not ok:
        failures.append("unreachable rung in the library")
    return failures


# The spelling check above reads the stylesheet and reasons about a selector.
# This one asks the question the reader actually cares about - "if I pick this
# rung, do I get it?" - by putting the markup through the applier every
# consumer uses and looking at what came out. That is a different question, and
# it is the one that was answered wrongly: a rung can have a perfectly good
# selector and still not arrive, because arriving is a property of the swap
# rather than of the CSS.
#
# It is also the check that generalises past this library. `apply_variants` is
# reimplemented in the two browser tools that compose from the published
# bundle, and nothing here can see those. What it CAN do is guarantee the thing
# they all depend on: that every rung this library ships is one the shared
# algorithm can reach.
def previous_applier(name, meta, markup, mods):
    """`apply_variants` as it stood before it worked on class tokens.

    Kept verbatim so the sweep below can be shown to catch something. A check
    proven only against code that passes it is a check that would pass just as
    well if it measured nothing, which is what this file says about every
    other gate in it.
    """
    from check_page import axes_of
    body = markup
    for key, value in mods.items():
        swapped = False
        for known in sorted(axes_of(meta).get(key, ())):
            old = f'{name}--{known}'
            if old in body:
                body = body.replace(old, f'{name}--{value}')
                swapped = True
                break
        if not swapped:
            body = re.sub(r'(class="[^"]*\b' + re.escape(name) + r')(")',
                          r'\1 ' + f'{name}--{value}' + r'\2', body, count=1)
    return body


def rung_faults(name, meta, markup, axes, applier=None):
    """Every declared rung that does not arrive, applied one at a time."""
    from check_page import apply_variants as current
    apply_variants = applier or current
    out = []
    for axis, values in axes.items():
        siblings = [v for v in values if v != "default"]
        for value in siblings:
            body = apply_variants(name, meta, markup, {axis: value})
            classes = set()
            for attr in re.findall(r'class="([^"]*)"', body):
                classes.update(attr.split())
            want = f"{name}--{value}"
            if want not in classes:
                out.append(f"{axis}={value} did not arrive")
                continue
            # And the rung it replaced has to be gone. An applier that appends
            # without swapping leaves two rungs of one axis on the element and
            # lets source order pick the winner, which is nobody's choice.
            stuck = sorted(f"{name}--{o}" for o in siblings
                           if o != value and f"{name}--{o}" in classes)
            if stuck:
                out.append(f"{axis}={value} arrived beside {', '.join(stuck)}")
    return out


def check_every_rung_applies():
    """Ask the applier for every rung in the library, and look at the answer."""
    import lint
    failures = []
    print("ci/check_page.py, every declared rung actually arrives")

    # The controls first, so the sweep below is known to be able to fail. Both
    # are the real patterns and the previous applier - the two defects this
    # sweep was written to find, run against the code that had them.
    for name, axis, value in (("opener-split", "rule", "ruled"),
                              ("hero-stated", "alignment", "centred")):
        folder = HERE.parent / "patterns" / name
        text = (folder / "pattern.html").read_text(encoding="utf-8")
        meta = lint.parse_header(text, folder / "pattern.html")
        markup = re.sub(r"\s*<!--\n.*?\n-->", "", text, count=1, flags=re.S)
        axes = {axis: lint.parse_variants(meta["variants"])[axis]}
        caught = bool(rung_faults(name, meta, markup, axes, previous_applier))
        quiet = not rung_faults(name, meta, markup, axes)
        print(f"  {'ok  ' if caught else 'FAIL'} catches: {name} {axis}={value} "
              f"under the applier that shipped it")
        print(f"  {'ok  ' if quiet else 'FAIL'} quiet on: {name} {axis}={value} "
              f"under the applier that replaced it")
        if not caught:
            failures.append(f"{name} {axis}={value} control")
        if not quiet:
            failures.append(f"{name} {axis}={value} still not arriving")

    # A pattern with no element carrying its own bare name has nowhere for a
    # rung to land, and the sweep has to say so rather than pass it.
    demo_meta = {"variants": "sticky=static|pinned"}
    got = rung_faults("demo", demo_meta, '<div class="demo-wrapper"></div>',
                      lint.parse_variants(demo_meta["variants"]))
    ok = len(got) == 2
    print(f"  {'ok  ' if ok else 'FAIL'} catches: markup with no element to "
          f"put the rung on" + ("" if ok else f" (got {len(got)}, want 2)"))
    if not ok:
        failures.append("no-root-element control")

    swept = 0
    for folder in sorted(p for p in (HERE.parent / "patterns").iterdir()
                         if p.is_dir()):
        text = (folder / "pattern.html").read_text(encoding="utf-8")
        meta = lint.parse_header(text, folder / "pattern.html")
        axes = lint.parse_variants(meta.get("variants", "")) or {}
        if not axes:
            continue
        markup = re.sub(r"\s*<!--\n.*?\n-->", "", text, count=1, flags=re.S)
        faults = rung_faults(folder.name, meta, markup, axes)
        swept += sum(len([v for v in vs if v != "default"]) for vs in axes.values())
        if faults:
            failures.append(folder.name)
            for f in faults:
                print(f"  FAIL {folder.name}: {f}")
    ok = not failures
    print(f"  {'ok  ' if ok else 'FAIL'} quiet on: {swept} rung(s) across the "
          f"library, each applied and found on the element")
    return failures


# A chooser reads these words straight out of the library. Every way they can
# go quietly wrong is a rung somebody picks without knowing what it does, or a
# note describing something the pattern stopped offering.
NOTE_CASES = [
    ("a rung with no words",
     lambda d: d["rule"]["rungs"]["ruled"].update({"note": ""})),
    ("a rung the pattern does not offer",
     lambda d: d["rule"]["rungs"].update({"invented": {"label": "X", "note": "Y"}})),
    ("a rung with no note at all",
     lambda d: d["rule"]["rungs"].pop("ruled")),
    ("an axis the pattern does not declare",
     lambda d: d.update({"nonsense": {"label": "X", "note": "Y", "rungs": {}}})),
    ("an axis with no label",
     lambda d: d["rule"].update({"label": "  "})),
]


def check_variant_notes():
    """The words beside a rung, held to the rungs the pattern actually offers."""
    import lint
    failures = []
    print("ci/lint.py, the words a chooser shows for a rung")
    folder = HERE.parent / "patterns" / "opener-split"
    html = folder / "pattern.html"
    meta = lint.parse_header(html.read_text(encoding="utf-8"), html)
    good = json.loads((folder / "variants.json").read_text(encoding="utf-8"))

    def findings_for(doc):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "variants.json").write_text(json.dumps(doc), encoding="utf-8")
        held = lint.ROOT
        lint.ROOT = tmp
        before = len(lint.findings)
        try:
            lint.check_variant_notes(tmp, tmp / "pattern.html", meta)
            return len(lint.findings) - before
        finally:
            del lint.findings[before:]
            lint.ROOT = held
            shutil.rmtree(tmp, ignore_errors=True)

    for label, mutate in NOTE_CASES:
        doc = json.loads(json.dumps(good))
        mutate(doc)
        got = findings_for(doc)
        ok = got > 0
        print(f"  {'ok  ' if ok else 'FAIL'} catches: {label}")
        if not ok:
            failures.append(label)

    ok = findings_for(good) == 0
    print(f"  {'ok  ' if ok else 'FAIL'} quiet on: the pattern's own notes")
    if not ok:
        failures.append("quiet on real notes")

    # And the library, which is the half that catches a regression.
    bad = []
    for pattern in sorted(p for p in (HERE.parent / "patterns").iterdir() if p.is_dir()):
        m = lint.parse_header((pattern / "pattern.html").read_text(encoding="utf-8"),
                              pattern / "pattern.html")
        before = len(lint.findings)
        lint.check_variant_notes(pattern, pattern / "pattern.html", m)
        if len(lint.findings) > before:
            bad.append(pattern.name)
        del lint.findings[before:]
    ok = not bad
    print(f"  {'ok  ' if ok else 'FAIL'} quiet on: every pattern in the library"
          + ("" if ok else " - %s" % ", ".join(bad)))
    if not ok:
        failures.append("library notes")
    return failures


# The named type pairings a chooser offers. They carry `dials`, so a bad one is
# a page outside the range TOKENS.md states its contrast guarantees across -
# and they are the only place in this repository that names a font by URL.
PAIRING_CASES = [
    ("a dial outside the documented range",
     lambda d: d["pairings"][0]["dials"].update({"type-scale": 1.6})),
    ("a dial TOKENS.md does not document",
     lambda d: d["pairings"][0]["dials"].update({"letter-spacing": 1})),
    ("a dial written as a string",
     lambda d: d["pairings"][0]["dials"].update({"type-scale": "1.05"})),
    ("a stack that does not name its own family",
     lambda d: d["pairings"][0]["heading"].update({"stack": "Georgia, serif"})),
    ("a pairing with nothing to load the font",
     lambda d: d["pairings"][1].update({"url": ""})),
    ("a font URL that is not Google Fonts",
     lambda d: d["pairings"][1].update({"url": "https://example.com/f.css"})),
    ("two pairings sharing one id",
     lambda d: d["pairings"][1].update({"id": d["pairings"][0]["id"]})),
]


def check_type_pairings():
    """Both halves, on the file the chooser actually reads."""
    import copy
    import lint
    failures = []
    print("ci/lint.py, the named type pairings")
    path = HERE.parent / "type-pairings.json"
    good = json.loads(path.read_text(encoding="utf-8"))

    def findings_for(doc):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "type-pairings.json").write_text(json.dumps(doc), encoding="utf-8")
        held_root, held_file = lint.ROOT, lint.PAIRINGS_FILE
        lint.ROOT, lint.PAIRINGS_FILE = tmp, tmp / "type-pairings.json"
        before = len(lint.findings)
        try:
            lint.check_type_pairings()
            return len(lint.findings) - before
        finally:
            del lint.findings[before:]
            lint.ROOT, lint.PAIRINGS_FILE = held_root, held_file
            shutil.rmtree(tmp, ignore_errors=True)

    for label, mutate in PAIRING_CASES:
        doc = copy.deepcopy(good)
        mutate(doc)
        ok = findings_for(doc) > 0
        print(f"  {'ok  ' if ok else 'FAIL'} catches: {label}")
        if not ok:
            failures.append(label)

    ok = findings_for(good) == 0
    print(f"  {'ok  ' if ok else 'FAIL'} quiet on: the twelve as they ship "
          f"({len(good['pairings'])} pairings)")
    if not ok:
        failures.append("quiet on the real pairings")
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
    ("a rung the pattern does not offer",
     ["homepage", "hero-stated:ground=soft", "cta-band"], "variant"),
    ("a misspelled axis, which used to pass silently",
     ["homepage", "hero-stated:groudn=deep", "cta-band"], "variant"),
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
    mutated = kept.replace(
        b"min-height: calc(100svh - var(--page-header-height, 9.5rem));",
        b"min-height: 100svh;")

    # If the search string has gone stale, the "mutation" is a no-op and the
    # case reports ok for a file it never changed - or, worse, reports ok
    # because a previous interrupted run left the file already broken. Assert
    # the edit did something before trusting what the check says about it.
    label = "a full-viewport opener that subtracts nothing"
    if mutated == kept:
        failures.append(label)
        print(f"  FAIL  {label:<46} the search string no longer matches "
              f"hero-overlay/pattern.css - this test needs updating, the check "
              f"is not necessarily broken")
    else:
        try:
            css.write_bytes(mutated)
            code, out = run_page(["homepage", "hero-overlay", "stats-band", "cta-band"])
            ok = code == 1 and "[the fold]" in out
            print(f"  {'ok  ' if ok else 'FAIL'} {label:<46} exit={code} want=1 [the fold]")
            if not ok:
                failures.append(label)
        finally:
            css.write_bytes(kept)

    # Assert the mutation is gone, not that the file matches git.
    #
    # This compared against `git diff --quiet`, to catch two overlapping runs
    # where the second snapshots the first's mutation and faithfully restores
    # it - a case `kept` cannot see. That case is real, but it is already
    # caught, and caught earlier: a leaked mutation means the search string is
    # absent, so `mutated == kept` and the run fails above with "the search
    # string no longer matches" before ever reaching here.
    #
    # What the git comparison did add was a false failure on any uncommitted
    # change to hero-overlay, so editing the pattern legitimately turned a
    # green suite red for a mutation that had never been left behind. Assert
    # the property directly instead. It holds whatever the working tree is
    # doing, and does not care whether the edit has been committed yet.
    now = css.read_bytes()
    leaked = (b"min-height: 100svh;" in now
              and b"min-height: calc(100svh - var(--page-header-height" not in now)
    if leaked or now != kept:
        failures.append("the fold case left hero-overlay mutated")
        print("  FAIL  patterns/hero-overlay/pattern.css was not restored after "
              "the fold case")

    # The other end of the same rule, and it needs its own case: a page whose
    # opener allows for the header perfectly and forgets the footer under it
    # passed the check above, and shipped 177px of scroll on a pattern whose
    # whole premise is that there is none. Only `whole-page` patterns owe this
    # second term, so the mutation is made on the one that carries the field.
    folder = HERE.parent / "patterns" / "hero-squeeze"
    css = folder / "pattern.css"
    kept = css.read_bytes()
    mutated = kept.replace(
        b"min-height: calc(100svh\n"
        b"    - var(--page-header-height, 9.5rem)\n"
        b"    - var(--page-footer-height, 12.5rem));",
        b"min-height: calc(100svh - var(--page-header-height, 9.5rem));")

    label = "a whole-page opener with no footer allowance"
    if mutated == kept:
        failures.append(label)
        print(f"  FAIL  {label:<46} the search string no longer matches "
              f"hero-squeeze/pattern.css - this test needs updating, the check "
              f"is not necessarily broken")
    else:
        try:
            css.write_bytes(mutated)
            code, out = run_page(["landing", "hero-squeeze"])
            ok = code == 1 and "[the fold]" in out
            print(f"  {'ok  ' if ok else 'FAIL'} {label:<46} exit={code} want=1 [the fold]")
            if not ok:
                failures.append(label)
        finally:
            css.write_bytes(kept)
    now = css.read_bytes()
    if now != kept:
        failures.append("the footer case left hero-squeeze mutated")
        print("  FAIL  patterns/hero-squeeze/pattern.css was not restored after "
              "the footer case")

    # The library sweep. The recipes only ever cover the patterns somebody
    # thought to write down; this covers all of them.
    code, out = run_page(["--sweep"])
    ok = code == 0
    print(f"  {'ok  ' if ok else 'FAIL'} {'every pattern swept as an opener':<46} exit={code} want=0")
    if not ok:
        failures.append("library sweep")
        for line in out.splitlines():
            if "FAIL" in line:
                print(f"        {line.strip()}")

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


# --------------------------------------------------------------- phone width
#
# ci/check_phone.py. Every suite above this one reasons about source - CSS
# text, a metadata header, a token census. This one lays a pattern out in a
# browser at 320 and 360 and measures the result, which is the only way the
# three defects that reached live sites were ever going to be seen.
#
# The fixtures are synthetic on purpose. Proving the gate against the real
# library would prove nothing about the half that matters: a check that never
# fires passes a clean library perfectly.

PHONE_FIRES = [
    ("a fixed width wider than the phone",
     ".t-box { width: 400px; background: #eee; }",
     "<div class='t-box'>Sample</div>", "scrolls sideways"),
    ("a long unbreakable word",
     ".t-head { font-size: 2rem; }",
     "<h2 class='t-head'>Sample-unbreakablewordarealbrandwouldship</h2>",
     "scrolls sideways"),
    ("a padded link too short to hit",
     ".t-cta { display: inline-block; padding: 4px 20px;"
     " background: #ddd; text-decoration: none; }",
     "<a class='t-cta' href='#'>Sample join</a>", "tap target"),
    ("a small square button",
     ".t-icon { width: 30px; height: 30px; }",
     "<button class='t-icon'>x</button>", "tap target"),
    ("a summary too short to hit",
     ".t-q { font-size: 14px; line-height: 1.2; }",
     "<details><summary class='t-q'>Sample question</summary>"
     "<p>Sample answer.</p></details>", "tap target"),
    ("text below the legibility floor",
     ".t-fine { font-size: 9px; }",
     "<p class='t-fine'>Sample small print for the preview.</p>",
     "renders at"),
    ("a form field iOS will zoom into",
     ".t-field { box-sizing: border-box; font-size: 14px; padding: 14px;"
     " width: 100%; }",
     "<label for='e'>Sample email</label>"
     "<input class='t-field' id='e' type='email'>", "iOS zooms"),
    # No box-sizing, and that is the whole fixture. A full-width box whose
    # padding sits outside its width is the shape that took a panel to 930px
    # where it declared 832 and scrolled every article shell sideways - and
    # it passed, because the harness used to inject a reset the shipped
    # stylesheet does not.
    ("a full-width box whose padding sits outside it",
     ".t-panel { width: 100%; padding: 24px; border: 1px solid #ddd; }",
     "<div class='t-panel'>Sample panel copy.</div>", "scrolls sideways"),
]

# Valid work the gate must not complain about. Half of these are the exact
# shapes that made the first version of the tap rule unusable: it fired on
# every prose link and every row title in the library, which is the state a
# gate never recovers from because people stop reading it.
PHONE_QUIET = {
    "a horizontal rail, which is meant to be wider than the screen":
        (".t-rail { overflow-x: auto; display: flex; gap: 8px; }"
         " .t-rail > .t-cell { flex: 0 0 200px; height: 60px; background: #ddd; }",
         "<div class='t-rail'><div class='t-cell'></div>"
         "<div class='t-cell'></div><div class='t-cell'></div></div>"),
    "an image cover-cropped by its frame":
        (".t-frame { overflow: hidden; height: 100px; }"
         " .t-frame img { width: 600px; }",
         "<div class='t-frame'><img src='sample-wide.svg' alt='Sample'></div>"),
    "a link inside a sentence":
        (".t-copy { padding: 16px; }",
         "<p class='t-copy'>Sample copy with <a href='#'>a link</a> in it.</p>"),
    "a row title blockified by its grid parent":
        (".t-row { display: grid; padding: 16px; }"
         " .t-title { font-size: 19px; text-decoration: none; }",
         "<div class='t-row'><a class='t-title' href='#'>Sample entry</a></div>"),
    "a button drawn at a proper size":
        (".t-btn { min-height: 48px; padding: 0 24px; background: #ddd;"
         " border: 0; }",
         "<button class='t-btn'>Sample join</button>"),
    "a small checkbox with a big label":
        (".t-lab { display: block; min-height: 48px; padding: 14px; }",
         "<label class='t-lab' for='c'>"
         "<input id='c' type='checkbox'> Sample consent</label>"),
    "ordinary body copy":
        (".t-copy { padding: 16px; font-size: 16px; }",
         "<p class='t-copy'>Sample body copy that wraps onto a second line.</p>"),
    "a footnote marker, which is small by definition":
        (".t-note { font-size: 16px; } .t-note sup { font-size: 10px; }",
         "<p class='t-note'>Sample claim<sup>1</sup></p>"),
    "a control that is not rendered at all":
        (".t-hide { display: none; }",
         "<button class='t-hide'>Sample hidden</button>"),
    "a field at the size iOS leaves alone":
        (".t-field { box-sizing: border-box; font-size: 16px; padding: 14px;"
         " width: 100%; }",
         "<label for='e2'>Sample email</label>"
         "<input class='t-field' id='e2' type='email'>"),
}


def check_phone():
    """Both halves, then the library.

    Skipping is a first-class outcome here and not a pass: with no browser
    this prints SKIPPED and returns no failures, because a contributor
    working in the GitHub web editor cannot install Chromium and must not be
    blocked by that. The skip PATH itself is tested below, which is the only
    thing that stops it becoming a way for the gate to go quiet everywhere.
    """
    print("ci/check_phone.py, rendered at phone widths")
    sys.path.insert(0, str(HERE))
    import check_phone

    why = check_phone.browser_unavailable()
    if why:
        print(f"  SKIP  no browser here - {why}")
        print("  Nothing was measured at a phone width. This is not a pass.")
        return []

    failures = []
    tokens = check_phone.token_set("brand")

    def page(css, markup):
        return check_phone.SHELL.format(name="fixture", width=320,
                                        tokens=tokens, css=css, markup=markup)

    # One browser for every case. Launching Chromium costs sixty times what
    # measuring a page costs, so a launch per fixture would turn a two second
    # suite into a two minute one.
    with check_phone.Phone((320,)) as phone:
        for label, css, markup, needle in PHONE_FIRES:
            found = phone.faults("fixture", page(css, markup))
            ok = any(needle in line for line in found)
            print(f"  {'ok  ' if ok else 'FAIL'} catches: {label}")
            if not ok:
                failures.append(label)
                for line in found:
                    print(f"        got: {line}")
                if not found:
                    print("        got: nothing")
        for label, (css, markup) in PHONE_QUIET.items():
            found = phone.faults("fixture", page(css, markup))
            print(f"  {'ok  ' if not found else 'FAIL'} quiet on: {label}")
            if found:
                failures.append(label)
                for line in found:
                    print(f"        got: {line}")

    # The skip path, exercised for real rather than asserted about. A shim
    # package on the path makes `import playwright` raise, which is exactly
    # what a machine without it does. Without this case the skip is the one
    # branch in the file that nothing has ever run - and it is the branch
    # that decides whether a red build is a real failure or an empty one.
    shim = Path(tempfile.mkdtemp(prefix="lander-phone-noplaywright-"))
    (shim / "playwright").mkdir()
    (shim / "playwright" / "__init__.py").write_text(
        "raise ImportError('no playwright here')", encoding="utf-8")
    try:
        env = dict(os.environ, PYTHONPATH=str(shim))
        got = subprocess.run(
            [sys.executable, str(HERE / "check_phone.py"), "cta-band"],
            capture_output=True, text=True, encoding="utf-8", env=env)
        out = (got.stdout or "") + (got.stderr or "")
        ok = got.returncode == 0 and "SKIPPED" in out
        print(f"  {'ok  ' if ok else 'FAIL'} skips cleanly with no browser "
              f"installed        exit={got.returncode} want=0")
        if not ok:
            failures.append("clean skip with no browser")
            print(f"        got: {out.strip()[:300]}")
    finally:
        shutil.rmtree(shim, ignore_errors=True)

    # The library itself. `new` is anything not in check_phone.ACCEPTED, so
    # this fails the day a pattern acquires a phone-width fault - while the
    # four the library already has stay visible in the output instead of
    # being excluded by a rule nobody can see.
    new, known, stale = check_phone.sweep()
    ok = not new and not stale
    print(f"  {'ok  ' if ok else 'FAIL'} the library at 320 and 360"
          f"                     {len(new)} new, {len(known)} known")
    if new:
        failures.append("new phone-width fault in the library")
        for line in new:
            print(f"        {line}")
    if stale:
        failures.append("stale phone-width baseline entry")
        for line in stale:
            print(f"        baseline entry matched nothing - {line}")

    return failures


# ------------------------------------------------------------ display measures
#
# ci/check_measures.py. Three separable things, and they fail for different
# reasons, so they are tested separately:
#
#   the discovery   which declarations are display measures at all. A body
#                   measure in ch is correct and must stay quiet; a display
#                   measure in ch is the defect.
#   the calibration whether the hostile sample brand is actually hostile. This
#                   is the only part of the gate whose answer depends on what
#                   is installed on the machine, so it is exercised on numbers
#                   here rather than only ever on this one laptop's fonts.
#   the measurement the library itself, and the positive control.

MEASURE_FIRES = {
    "a display measure in ch, the defect the gate exists for":
        (".x-title { font-family: var(--font-heading); max-width: 16ch; }",
         [(".x-title", "max-width", 16.0, "ch")]),
    "a display measure reached through the pattern's own custom property":
        (".x { --x-title-measure: 8.75em; }\n"
         ".x-title { font-family: var(--font-heading);"
         " max-width: var(--x-title-measure); }",
         [(".x-title", "max-width", 8.75, "em")]),
    "a heading with no face set on it, named as display type":
        (".x-heading { max-width: 11.25em; }",
         [(".x-heading", "max-width", 11.25, "em")]),
    "a measure declared in a media query":
        (".x-title { font-family: var(--font-heading); }\n"
         "@media (min-width: 60rem) { .x-title { max-width: 10.75em; } }",
         [(".x-title", "max-width", 10.75, "em")]),
}

MEASURE_QUIET = {
    "a body measure in ch, which is the job ch is for":
        ".x-copy { max-width: 68ch; }",
    "a container held to a rem width":
        ".x-wrap { max-width: 72rem; }",
    "body text under a heading, sharing neither the face nor the name":
        ".x-title { font-family: var(--font-heading); }\n"
        ".x-lede { max-width: 42ch; }",
}

# {full, bare, fallback} in em, as the browser probe returns them. `bare` is
# the same stack with the fixture family removed, which is what the page would
# have rendered in had the @font-face resolved nothing.
MEASURE_CALIBRATION = [
    ("the fixture's @font-face resolved nothing and it fell back silently",
     {"display": {"full": 0.7012, "bare": 0.7012, "fallback": "Georgia"},
      "brand": {"full": 0.7012, "bare": 0.7012, "fallback": "serif"}},
     True),
    ("the fixture is not the widest sample brand",
     {"display": {"full": 0.62, "bare": 0.44, "fallback": "Georgia"},
      "brand": {"full": 0.7012, "bare": 0.7012, "fallback": "serif"}},
     True),
    ("there is no hostile sample brand at all",
     {"brand": {"full": 0.7012, "bare": 0.7012, "fallback": "serif"}},
     True),
    ("the fixture as this repository ships it",
     {"display": {"full": 0.9957, "bare": 0.7012, "fallback": "Georgia"},
      "brand": {"full": 0.7012, "bare": 0.7012, "fallback": "serif"},
      "sharp": {"full": 0.5562, "bare": 0.5562, "fallback": "sans-serif"}},
     False),
    ("the chain landed on a narrow serif: adjusted, but barely the widest",
     {"display": {"full": 0.7100, "bare": 0.5000, "fallback": "Georgia"},
      "brand": {"full": 0.7012, "bare": 0.7012, "fallback": "serif"}},
     False),
]


def check_measures():
    """The discovery and the calibration on numbers; the library in a browser.

    The browser half skips with no browser installed, for the same reason
    ci/check_phone.py's does. The two halves above it do not, so a contributor
    with no Chromium still has the parts of this gate that can be tested
    without one - which is most of it.
    """
    print("ci/check_measures.py, display measures across the sample brands")
    sys.path.insert(0, str(HERE))
    import check_measures

    failures = []
    base = Path(tempfile.mkdtemp(prefix="lander-measure-gate-"))
    try:
        folder = base / "patterns" / "fixture"
        folder.mkdir(parents=True)
        real = check_measures.PATTERNS
        check_measures.PATTERNS = base / "patterns"
        try:
            for label, (css, want) in MEASURE_FIRES.items():
                (folder / "pattern.css").write_text(css, encoding="utf-8")
                got = [(s, p, n, u) for s, p, _d, n, u
                       in check_measures.measures("fixture")]
                ok = got == want
                print(f"  {'ok  ' if ok else 'FAIL'} finds: {label}")
                if not ok:
                    failures.append(label)
                    print(f"        got: {got}")
            for label, css in MEASURE_QUIET.items():
                (folder / "pattern.css").write_text(css, encoding="utf-8")
                got = check_measures.measures("fixture")
                ok = not got
                print(f"  {'ok  ' if ok else 'FAIL'} quiet on: {label}")
                if not ok:
                    failures.append(label)
                    print(f"        got: {got}")
        finally:
            check_measures.PATTERNS = real
    finally:
        shutil.rmtree(base, ignore_errors=True)

    for label, seen, want_fatal in MEASURE_CALIBRATION:
        fatal, _lines = check_measures.calibration_faults(seen)
        ok = bool(fatal) == want_fatal
        print(f"  {'ok  ' if ok else 'FAIL'} calibration "
              f"{'stops' if want_fatal else 'passes'}: {label}")
        if not ok:
            failures.append(label)
            print(f"        got: {fatal or 'no fault'}")

    why = check_measures.browser_unavailable()
    if why:
        print(f"  SKIP  no browser here - {why}")
        print("  No measure was rendered on any brand. This is not a pass.")
        return failures

    sets = check_measures.sample_sets()
    names = sorted(f.name for f in check_measures.PATTERNS.iterdir()
                   if f.is_dir())
    with check_measures.Ruler() as ruler:
        cal, _lines = check_measures.calibrate(ruler, sets,
                                               check_measures.WIDTHS[0])
        ok = not cal
        print(f"  {'ok  ' if ok else 'FAIL'} the display fixture is hostile "
              f"on this machine")
        if not ok:
            failures.append("display fixture calibration")
            for line in cal:
                print(f"        {line}")
        rows, faults, _notes = check_measures.sweep(
            ruler, names, sets, check_measures.WIDTHS)
        bad = faults + [line for row in rows
                        for good, line in [check_measures.verdict(row)]
                        if not good]
        # The control. Same rendering, every display measure back in ch, and
        # the gate has to fire - otherwise a clean run above proves nothing
        # except that nothing was compared.
        ch_rows, _f, _n = check_measures.sweep(
            ruler, names, sets, check_measures.WIDTHS, ch=True)
    ok = not bad
    print(f"  {'ok  ' if ok else 'FAIL'} every display measure identical "
          f"across {len(sets)} brands  "
          f"{check_measures.spread_of(rows):.2f}% spread, {len(rows)} measured")
    if not ok:
        failures.append("display measure differs across sample brands")
        for line in bad:
            print(f"        {line}")
    ch_spread = check_measures.spread_of(ch_rows)
    four = check_measures.spread_of(ch_rows, without={check_measures.HOSTILE})
    ok = ch_spread > 5
    print(f"  {'ok  ' if ok else 'FAIL'} the same measures in ch diverge     "
          f"     {ch_spread:.1f}% spread, {four:.1f}% without the fixture")
    if not ok:
        failures.append("positive control did not fire")
    return failures


# ------------------------------------------------------------------- the fold
#
# ci/check_fold.py. It answers a question no other gate here asks: given a page
# assembled the way the platform serves one - a real header above, a site
# footer below - does a full-viewport pattern actually fit the viewport it
# promised?
#
# The part worth testing on numbers is the one judgement in it. A page can
# overflow for two reasons, and only one of them is this library's arithmetic:
# the section is sitting on the height calc() gave it, or the content grew past
# that height. The first is a sum that is wrong wherever it lands; the second
# is the failure mode hero-squeeze's README documents on purpose, and depends
# on the copy somebody placed. Confusing them either way is fatal - fail the
# second and the gate is an opinion about sample content, miss the first and it
# is the gate that let 177px of scroll onto a live site.

FOLD_BOUND = [
    ("a section sitting exactly on its floor",
     {"section": 472.0, "floor": "472px"}, True),
    ("half a pixel under, which is a rounding artefact",
     {"section": 472.6, "floor": "472px"}, True),
    ("content that has grown past the floor",
     {"section": 496.9, "floor": "472px"}, False),
    ("min-height: auto, so there is no floor to sit on",
     {"section": 500.0, "floor": "auto"}, False),
    ("a floor the browser could not resolve",
     {"section": 500.0, "floor": ""}, False),
]

# (label, whole_page, observation, a fault is expected)
FOLD_VERDICT = [
    ("whole-page, at its floor, and the footer pushes it over", True,
     {"viewport": 800, "scroll": 998, "header": 124.2, "section": 708,
      "foot": 832.2, "footer": 166, "floor": "708px"}, True),
    ("whole-page, over, but the content grew past the floor", True,
     {"viewport": 568, "scroll": 804, "header": 125, "section": 482,
      "foot": 607, "footer": 197, "floor": "240px"}, False),
    ("whole-page and it fits", True,
     {"viewport": 844, "scroll": 844, "header": 125, "section": 516,
      "foot": 641, "footer": 197, "floor": "516px"}, False),
    ("an opener whose foot is below the fold at its own floor", False,
     {"viewport": 800, "scroll": 998, "header": 124.2, "section": 708,
      "foot": 832.2, "footer": 166, "floor": "708px"}, True),
    ("an opener whose foot is below the fold on grown content", False,
     {"viewport": 568, "scroll": 800, "header": 125, "section": 527.2,
      "foot": 652.2, "footer": 197, "floor": "440px"}, False),
    ("an opener whose foot lands on the fold", False,
     {"viewport": 800, "scroll": 800, "header": 124.2, "section": 672,
      "foot": 796.2, "footer": 166, "floor": "672px"}, False),

    # The six above are the table this gate shipped with, and every one of them
    # keeps the verdict it had when the test moved from the overflow to the
    # allowance. That is the point of leaving them alone: a rule that changed
    # its answer on the cases it was built from would be a different rule
    # wearing the same name. The four below are the half that was unreachable.
    #
    # A section whose CONTENT has grown past its floor was silent whatever its
    # arithmetic said, because the overflow could no longer be attributed. The
    # allowance still can: the header rendered 173.8 where the token set aside
    # 152, and that is wrong whether or not the content also overflowed. This
    # is the shape of the 2026-08-26 CI failure, and hero-squeeze is in this
    # state at most viewports in this library.
    ("an opener whose header outgrew the token, on content-bound section", False,
     {"viewport": 800, "scroll": 900, "header": 173.8, "section": 700,
      "foot": 873.8, "footer": 166, "floor": "648px"}, True),
    ("whole-page whose furniture outgrew both tokens, content-bound", True,
     {"viewport": 844, "scroll": 1100, "header": 173.8, "section": 600,
      "foot": 773.8, "footer": 197, "floor": "492px"}, True),
    # No floor is no claim. A section that never said how tall it would be has
    # made no arithmetic this file can be wrong about, however far it overflows.
    ("a page in ruins, but the section claimed no height at all", False,
     {"viewport": 800, "scroll": 1200, "header": 173.8, "section": 900,
      "foot": 1073.8, "footer": 166, "floor": "auto"}, False),
    ("a header one pixel over, which is the rounding tolerance", False,
     {"viewport": 800, "scroll": 800, "header": 153, "section": 648,
      "foot": 801, "footer": 166, "floor": "648px"}, False),
]

# (label, whole_page, observation, expected (allowed, rendered) or None)
#
# The reading itself, kept apart from the verdict because it is the half that
# has to be right about the PAGE. The allowance is the viewport minus the
# resolved min-height, never the token re-derived from CSS text: a brand that
# sets --page-header-height in a media query, in em, or not at all must all
# measure the same, and reading the stylesheet instead is how a gate ends up
# checking a claim against itself.
FOLD_FURNITURE = [
    ("an opener counts the header and nothing under it", False,
     {"viewport": 800, "header": 124.2, "footer": 166, "floor": "648px"},
     (152.0, 124.2)),
    ("a whole-page pattern counts the footer too", True,
     {"viewport": 800, "header": 124.2, "footer": 166, "floor": "448px"},
     (352.0, 290.2)),
    ("a token that is not the default reads back as itself", False,
     {"viewport": 844, "header": 145, "footer": 197, "floor": "668px"},
     (176.0, 145.0)),
    ("min-height: auto is no claim to check", False,
     {"viewport": 800, "header": 124.2, "footer": 166, "floor": "auto"}, None),
    ("a floor the browser could not resolve", False,
     {"viewport": 800, "header": 124.2, "footer": 166, "floor": ""}, None),
]


def check_fold():
    """The judgement on numbers; the library and its control in a browser."""
    print("ci/check_fold.py, a full-viewport pattern in a page with furniture")
    sys.path.insert(0, str(HERE))
    import check_fold

    failures = []
    for label, got, want in FOLD_BOUND:
        ok = check_fold.box_bound(got) == want
        print(f"  {'ok  ' if ok else 'FAIL'} "
              f"{'box-bound' if want else 'content-bound'}: {label}")
        if not ok:
            failures.append(label)

    for label, whole, got, want in FOLD_FURNITURE:
        seen = check_fold.furniture(got, whole)
        rounded = None if seen is None else (round(seen[0], 3), round(seen[1], 3))
        ok = rounded == want
        print(f"  {'ok  ' if ok else 'FAIL'} reads {want or 'nothing'}: {label}")
        if not ok:
            failures.append(label)
            print(f"        got: {rounded}")

    for label, whole, got, want in FOLD_VERDICT:
        line = check_fold.verdict("fixture", whole, got, 0, 0)
        ok = bool(line) == want
        print(f"  {'ok  ' if ok else 'FAIL'} "
              f"{'fails on' if want else 'quiet on'}: {label}")
        if not ok:
            failures.append(label)
            print(f"        got: {line or 'no fault'}")

    why = check_fold.browser_unavailable()
    if why:
        print(f"  SKIP  no browser here - {why}")
        print("  No page was assembled. This is not a pass.")
        return failures

    names = check_fold.candidates()
    ok = bool(names)
    print(f"  {'ok  ' if ok else 'FAIL'} the library has full-viewport "
          f"pattern(s) to measure  {', '.join(names) or 'none found'}")
    if not ok:
        return failures + ["nothing full-viewport to measure"]

    tokens = check_fold.token_set("brand")
    with check_fold.Shell() as shell:
        faults, _rows = check_fold.sweep(shell, names, tokens,
                                         check_fold.VIEWPORTS)
        # The control, and it is not optional: the run above passes just as
        # cleanly on a gate that measures nothing at all. Same pages, the
        # furniture tokens back the way the live defect had them.
        broken, _rows = check_fold.sweep(shell, names, tokens,
                                         check_fold.VIEWPORTS,
                                         check_fold.BROKEN)
    ok = not faults
    print(f"  {'ok  ' if ok else 'FAIL'} every full-viewport pattern fits a "
          f"page with furniture")
    if not ok:
        failures.append("a full-viewport pattern does not fit")
        for line in faults:
            print(f"        {line}")
    ok = bool(broken)
    print(f"  {'ok  ' if ok else 'FAIL'} the same pages with a header-only "
          f"allowance do not      {len(broken)} fault(s)")
    if not ok:
        failures.append("fold control did not fire")
    return failures


def check_lost_messages():
    """An exit code is not the whole gate. The message is the gate.

    A brand author reads one sentence and goes looking. Two of these sentences
    named a fallback the browser does not use, so the reader went looking in
    the pattern's own defaults for a value the ancestor was supplying. Both
    halves have to hold: the right phrase present, and the wrong one absent.
    """
    from _dials import check_dials
    failures = []
    print("ci/_dials.py, what a message says the value falls back to")
    for (dial, value), want in LOST_PHRASES.items():
        out = check_dials("acme", ":root{--%s:%s;}" % (dial, value))
        said = " ".join(m for _fatal, m in out)
        ok = bool(out) and want in said
        print(f"  {'ok  ' if ok else 'FAIL'} --{dial}: {value:<8} names {want!r}")
        if not ok:
            failures.append(f"--{dial} message")
    for (dial, value), want in LOST_ABSENT.items():
        out = check_dials("acme", ":root{--%s:%s;}" % (dial, value))
        said = " ".join(m for _fatal, m in out)
        ok = bool(out) and want in said and "17.952px" not in said
        print(f"  {'ok  ' if ok else 'FAIL'} --{dial}: empty    names {want!r}, "
              f"not the unit case")
        if not ok:
            failures.append(f"--{dial} empty message")
    return failures


# ci/build_preview.py, the shell half. Most of these guard a silent
# corruption rather than a crash: a shell concatenates several patterns whose
# slot names collide, so filling the whole document from one pattern's sample
# would put the opener's copy into the steps section and render a page that
# looks entirely fine. Nothing downstream could tell.
SHELL_BANNER = """<!-- ================================================================
     section {n} of 2 : {name} v1
     ================================================================ -->
"""


def _bannered(first, second):
    return (SHELL_BANNER.format(n=1, name=first) + '<section class="a"></section>'
            + SHELL_BANNER.format(n=2, name=second) + '<section class="b"></section>')


def check_shells():
    sys.path.insert(0, str(HERE))
    import build_preview as bp
    failures = []

    got = [name for name, _ in bp.shell_sections(_bannered("hero-split", "cta-band"))]
    ok = got == ["hero-split", "cta-band"]
    print(f"  {'ok  ' if ok else 'FAIL'} reads the pattern name off every section banner")
    if not ok:
        failures.append(f"shell_sections named {got}")

    # A banner format change in compose.py has to stop the build, not quietly
    # produce a shell filled from nothing.
    try:
        bp.shell_sections('<section class="a"></section>')
        caught = False
    except SystemExit:
        caught = True
    print(f"  {'ok  ' if caught else 'FAIL'} refuses a shell body carrying no section banner")
    if not caught:
        failures.append("shell_sections accepted a bannerless body")

    # The real assertion, on a real shell: steps-plain and faq-details both
    # carry a `section-title` slot and their sample values differ. Both have to
    # be on the page, in that order. A whole-document fill puts one of them in
    # both places, and the page still renders.
    conversion = HERE.parent / "compositions" / "homepage-conversion@2"
    if not conversion.exists():
        print("  ok   skipped: homepage-conversion@2 is not in this tree")
        return failures

    rendered, patterns = bp.build_shell(conversion)
    steps, questions = "Sample steps heading", "Sample questions heading"
    ok = (steps in rendered and questions in rendered
          and rendered.index(steps) < rendered.index(questions))
    print(f"  {'ok  ' if ok else 'FAIL'} fills each section from its own pattern's sample")
    if not ok:
        failures.append("build_shell crossed sample content between sections")

    ok = "slot:" not in rendered and "<!--" not in rendered
    print(f"  {'ok  ' if ok else 'FAIL'} leaves no slot marker and no comment in a shell")
    if not ok:
        failures.append("build_shell left a slot or a comment in the output")

    ok = patterns == ["hero-split", "steps-plain", "faq-details", "cta-band",
                      "colophon"]
    print(f"  {'ok  ' if ok else 'FAIL'} reports the patterns it placed, in page order")
    if not ok:
        failures.append(f"build_shell reported {patterns}")

    return failures


# ci/build_configurator.py. The first case is the one that matters: a content
# slot IS an HTML comment, so stripping a pattern's placement comments takes
# every slot with it unless the strip knows better. That happened, and it was
# invisible to everything structural - a shell composed from the bundle had the
# right sections, in the right order, with the right variant class on each, and
# no words in any of them. It was caught by rendering one and diffing the text
# against the shipped shell.
def check_configurator():
    import re as _re
    sys.path.insert(0, str(HERE))
    import build_configurator as bc
    failures = []

    bundle = bc.build()

    slots = sum(p["html"].count("<!-- slot:") for p in bundle["patterns"].values())
    ok = slots > 0
    print(f"  {'ok  ' if ok else 'FAIL'} keeps the slot markers when it strips "
          f"comments   {slots} slot(s)")
    if not ok:
        failures.append("build_configurator stripped every slot marker")

    leftover = sum(1 for p in bundle["patterns"].values()
                   if _re.search(r"<!--(?!\s*slot\s*:)", p["html"]))
    ok = leftover == 0
    print(f"  {'ok  ' if ok else 'FAIL'} strips every comment that is not a slot")
    if not ok:
        failures.append(f"{leftover} pattern(s) kept a non-slot comment")

    # Every pattern a shell names must be in the same bundle, or a consumer
    # composes a page with a hole where a section should be.
    missing = sorted({p["name"] for s in bundle["shells"].values()
                      for p in s["patterns"]} - set(bundle["patterns"]))
    ok = not missing
    print(f"  {'ok  ' if ok else 'FAIL'} every pattern a shell names is in the bundle")
    if not ok:
        failures.append(f"shells name absent pattern(s): {missing}")

    # A dial the token contract does not document would let a chooser produce a
    # design the toolkit cannot rebuild from the recipe it hands over.
    held = dict(bc.DIALS)
    try:
        bc.DIALS["letter-spacing"] = {"default": 0}
        try:
            bc.check_dials_documented()
            caught = False
        except SystemExit:
            caught = True
    finally:
        bc.DIALS.clear()
        bc.DIALS.update(held)
    print(f"  {'ok  ' if caught else 'FAIL'} refuses a dial TOKENS.md does not document")
    if not caught:
        failures.append("check_dials_documented accepted an invented dial")

    # Data URIs, so the bundle answers from an origin holding none of these
    # files. A relative filename would render as a broken image off Pages.
    bad = [k for k, v in bundle["placeholders"].items() if not v.startswith("data:")]
    ok = not bad and bundle["furniture"]["{{logo.src}}"].startswith("data:")
    print(f"  {'ok  ' if ok else 'FAIL'} carries its images as data URIs")
    if not ok:
        failures.append(f"image(s) not inlined: {bad}")

    return failures


# ------------------------------------------------------------------ recipes
#
# ci/check_recipes.py. A recipe is the layer above a shell - which shell, which
# ground each band sits on, how the page opens and closes - and every fault it
# can carry is invisible to a reader. A shell name with no composition behind
# it, four rungs for a five-band shell, a pin that disagrees with its own
# filename: all of them read perfectly, and all of them hand a builder a
# decision nobody made. So the fires below are the ones a person cannot see.
#
# The quiet half matters as much here as anywhere else, and more than usual in
# one respect: `look` and `notes` are optional, so a gate quietly requiring
# either would reject most of the menu on the day somebody wrote a plain one.

RECIPE_VALID = """```recipe
recipe: gate-fixture@1
shape: reference
shell: pricing
look: hero-stated alignment=centred
grounds: plain, soft, plain, brand
opens: a claim, with the price named in the line under it
closes: a full-width band in the brand colour
signature: stated opener, tier cards, questions, band
pairing: brand
notes: a fixture, never offered to anybody
```

A fixture recipe. It exists to be checked.
"""

# (label, the stem the file is judged under, the text, the kind it must raise)
RECIPE_FIRES = [
    ("prose with no fenced block in it", "gate-fixture@1",
     "Words and no recipe.\n", "fence"),
    ("a field the grammar has no room for", "gate-fixture@1",
     RECIPE_VALID.replace("shape:", "mood: airy\nshape:"), "fields"),
    ("the fence broken by a blank line", "gate-fixture@1",
     RECIPE_VALID.replace("grounds:", "\ngrounds:"), "fields"),
    ("shape and shell the wrong way round", "gate-fixture@1",
     RECIPE_VALID.replace("shape: reference\nshell: pricing",
                          "shell: pricing\nshape: reference"), "fields"),
    ("a filename that disagrees with the pin", "gate-fixture@2",
     RECIPE_VALID, "pin"),
    ("a content shape outside the seven", "gate-fixture@1",
     RECIPE_VALID.replace("shape: reference", "shape: gallery"), "shape"),
    ("a shell pinned to a version", "gate-fixture@1",
     RECIPE_VALID.replace("shell: pricing", "shell: pricing@3"), "shell"),
    ("a shell no composition provides", "gate-fixture@1",
     RECIPE_VALID.replace("shell: pricing", "shell: checkout"), "shell"),
    ("a look dial the pattern does not offer", "gate-fixture@1",
     RECIPE_VALID.replace("alignment=centred", "alignment=justified"), "look"),
    ("a look naming a pattern that is not there", "gate-fixture@1",
     RECIPE_VALID.replace("hero-stated align", "hero-imagined align"), "look"),
    ("one rung short of the shell's bands", "gate-fixture@1",
     RECIPE_VALID.replace("plain, soft, plain, brand", "plain, soft, plain"),
     "grounds"),
    ("a rung that is not on the ladder", "gate-fixture@1",
     RECIPE_VALID.replace("grounds: plain", "grounds: muted"), "grounds"),
    ("a signature that is a description instead", "gate-fixture@1",
     RECIPE_VALID.replace(
         "signature: stated opener, tier cards, questions, band",
         "signature: a stated opener above three tier cards, then the "
         "questions, then a closing band"), "signature"),
    ("a pairing that names a face", "gate-fixture@1",
     RECIPE_VALID.replace("pairing: brand", "pairing: Fraunces and Inter"),
     "pairing"),
]

# Valid shapes the gate must leave entirely alone. Every one of these is a form
# a real recipe in the menu takes today.
RECIPE_QUIET = [
    ("the full form, every field present",
     RECIPE_VALID),
    ("no look, which is the commoner case",
     RECIPE_VALID.replace("look: hero-stated alignment=centred\n", "")),
    ("no notes",
     RECIPE_VALID.replace("notes: a fixture, never offered to anybody\n", "")),
    ("neither optional field",
     RECIPE_VALID.replace("look: hero-stated alignment=centred\n", "")
                 .replace("notes: a fixture, never offered to anybody\n", "")),
    ("two look entries, separated by a semicolon",
     RECIPE_VALID.replace("look: hero-stated alignment=centred",
                          "look: hero-stated alignment=centred; "
                          "link-cluster ground=soft")),
    ("two dials on one pattern in look",
     RECIPE_VALID.replace("look: hero-stated alignment=centred",
                          "look: masthead-nav sticky=pinned menu=drawer")),
    ("a three-band shell with three rungs",
     RECIPE_VALID.replace("shell: pricing", "shell: safety")
                 .replace("look: hero-stated alignment=centred\n", "")
                 .replace("grounds: plain, soft, plain, brand",
                          "grounds: brand, plain, brand")),
    ("a seven-band shell with seven rungs",
     RECIPE_VALID.replace("shell: pricing", "shell: article-guide")
                 .replace("look: hero-stated alignment=centred\n", "")
                 .replace("grounds: plain, soft, plain, brand",
                          "grounds: plain, soft, plain, plain, plain, soft, "
                          "brand")),
    ("a signature of exactly ten words",
     RECIPE_VALID.replace(
         "signature: stated opener, tier cards, questions, band",
         "signature: one two three four five six seven eight nine ten")),
]


# compose.py --check and the one field a release moves on its own.
RELEASE_TAG_CASES = [
        ("a manifest whose tag alone has moved", "x@1/manifest.json",
         json.dumps({"composition": "x", "library": "v41",
                     "patterns": [{"name": "hero-split", "version": "9"}]}),
         True),
        ("a manifest naming a pattern version that is not there",
         "x@1/manifest.json",
         json.dumps({"composition": "x", "library": "v103",
                     "patterns": [{"name": "hero-split", "version": "8"}]}),
         False),
        ("a stale tag AND a stale pattern version together",
         "x@1/manifest.json",
         json.dumps({"composition": "x", "library": "v41",
                     "patterns": [{"name": "hero-split", "version": "8"}]}),
         False),
        ("a page.css whose text differs", "x@1/page.css",
         ".x { color: red }", False),
        ("a manifest that is not readable as JSON", "x@1/manifest.json",
         "{ not json", False),
]


def check_release_tag_is_not_freshness():
    """compose.py --check ignores the release tag and nothing else.

    `library` is the one field in a manifest that moves without any pattern or
    recipe moving, and the job that rewrites it cannot run until this check
    passes. Both halves are asserted here: a tag-only difference is not
    staleness, and a tag-only difference is not a licence to miss a real one.
    """
    sys.path.insert(0, str(HERE))
    import compose
    failures = []
    print("ci/compose.py, the release tag and the freshness check")

    fresh = json.dumps({"composition": "x", "library": "v103",
                        "patterns": [{"name": "hero-split", "version": "9"}]})
    for label, rel, held, want in RELEASE_TAG_CASES:
        got = compose.only_the_release_tag_moved(rel, held, fresh)
        ok = got == want
        print(f"  {'ok  ' if ok else 'FAIL'} {label:<52} "
              f"ignored={got} want={want}")
        if not ok:
            failures.append(label)
    return failures


def check_recipes():
    sys.path.insert(0, str(HERE))
    import check_recipes as cr
    failures = []
    print("ci/check_recipes.py, the recipe grammar")

    known, axes = cr.shells(), cr.pattern_axes()

    for label, stem, text, want in RECIPE_FIRES:
        kinds = [k for k, _ in cr.faults_in(stem, text, known, axes)]
        ok = want in kinds
        print(f"  {'ok  ' if ok else 'FAIL'} {label:<46} [{want}] "
              f"got {kinds or ['nothing']}")
        if not ok:
            failures.append(label)

    for label, text in RECIPE_QUIET:
        kinds = [k for k, _ in cr.faults_in("gate-fixture@1", text, known, axes)]
        ok = not kinds
        print(f"  {'ok  ' if ok else 'FAIL'} {label:<46} got "
              f"{kinds or ['nothing']}")
        if not ok:
            failures.append(label)

    # The control, as a subprocess: it is the step the workflow runs, and a
    # gate whose own control has stopped firing is the case this whole file
    # exists for.
    got = subprocess.run([sys.executable, str(HERE / "check_recipes.py"),
                          "--broken"], capture_output=True, text=True,
                         encoding="utf-8")
    ok = got.returncode == 0
    print(f"  {'ok  ' if ok else 'FAIL'} {'the positive control still fires':<46} "
          f"exit={got.returncode} want=0")
    if not ok:
        failures.append("recipe positive control")

    # And the committed menu against the recipes it is generated from. Nobody
    # edits recipes/README.md, so the only way it goes wrong is a recipe
    # changing without the file being rewritten.
    got = subprocess.run([sys.executable, str(HERE / "check_recipes.py"),
                          "--check"], capture_output=True, text=True,
                         encoding="utf-8")
    ok = got.returncode == 0
    print(f"  {'ok  ' if ok else 'FAIL'} "
          f"{'recipes/README.md is what they generate':<46} "
          f"exit={got.returncode} want=0")
    if not ok:
        failures.append("recipes/README.md is stale")
        for line in got.stdout.splitlines():
            if "FAIL" in line:
                print(f"        {line.strip()}")

    return failures


def check_header_fit():
    """ci/check_header.py, both directions: the shipped header holds one row
    against the long menu, and the positive control fires when the fold is
    switched off. Skips, and says so, without a browser."""
    import check_phone
    failures = []
    why = check_phone.browser_unavailable()
    if why:
        print(f"  skip check_header: {why}")
        return failures
    for label, argv, want in (
            ("header gate quiet on the shipped header (1280 only)",
             ["--widths", "1280", "1024"], 0),
            ("header gate fires with the fold switched off", ["--broken"], 0)):
        got = subprocess.run([sys.executable, str(HERE / "check_header.py")] + argv,
                             capture_output=True, text=True, encoding="utf-8")
        ok = got.returncode == want
        print(f"  {'ok  ' if ok else 'FAIL'} {label} exit={got.returncode} want={want}")
        if not ok:
            print("      " + (got.stdout.strip().splitlines() or ["(no output)"])[-1])
            failures.append(label)
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
    failures += check_lost_messages()
    print()
    failures += check_display_type()
    print()
    failures += check_modules()
    print()
    failures += check_header()
    print()
    failures += check_disclosure()
    print()
    failures += check_modifier_spelling()
    print()
    failures += check_every_rung_applies()
    print()
    failures += check_variant_notes()
    print()
    failures += check_type_pairings()
    print()
    failures += check_pages()
    print()
    failures += check_phone()
    print()
    failures += check_measures()
    print()
    failures += check_fold()
    print()
    failures += check_shells()
    print()
    failures += check_configurator()
    print()
    failures += check_release_tag_is_not_freshness()
    print()
    failures += check_recipes()
    print()
    failures += check_header_fit()
    print()
    if failures:
        print(f"{len(failures)} gate check(s) not behaving: "
              + ", ".join(failures))
        return 1
    recipes = json.loads((HERE / "page-recipes.json").read_text(encoding="utf-8"))
    total = (len(CASES) + 1 + len(LOST_PHRASES) + len(LOST_ABSENT)
             + len(BYPASSES) + len(QUIET) + len(LEGIBILITY)
             + len(SPACING) + len(EXTERNAL_CSS) + len(EXTERNAL_HTML)
             + len(HEADING) + len(SHAPE_CASES) + len(VARIANT_CASES)
             + len(DISCLOSURE_FIRES) + len(DISCLOSURE_QUIET) + 1
             + len(MODIFIER_CASES) + 1 + 6 + len(NOTE_CASES) + 2
             + len(PAIRING_CASES) + 1
             + len(PAGE_FIRES) + 2 + len(recipes["recipes"])
             + len(RELEASE_TAG_CASES)
             + len(PHONE_FIRES) + len(PHONE_QUIET) + 2
             + len(MEASURE_FIRES) + len(MEASURE_QUIET)
             + len(MEASURE_CALIBRATION) + 3
             + len(FOLD_BOUND) + len(FOLD_FURNITURE) + len(FOLD_VERDICT) + 3
             + 5 + 5
             + len(RECIPE_FIRES) + len(RECIPE_QUIET) + 2)
    print(f"clean: {total} gate cases across thirteen modules behave as documented.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
