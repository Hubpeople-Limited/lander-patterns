#!/usr/bin/env python3
"""Every display measure renders at the same width on every sample brand.

A measure is a `max-width` on display type - the number that decides whether a
headline lands on two lines or three. Until v57 those were written in `ch`,
and `ch` is not a length: it is the advance width of *zero in the face
actually used, at the weight actually used*. Georgia Bold is 0.7012em, Arial
Bold 0.5562em, and those are two of this library's own sample brands - so
`max-width: 16ch` was 26% wider on one brand than the other and one headline
had been rendering on two lines for some brands and three for others since it
was written. Nobody saw it, because seeing it needs two brands side by side
and a ruler.

v57 moved every display measure to `em`, which removes the typeface and keeps
the type scale. That was a claim, not a measurement. This file is the
measurement: render each measure on every sample token set and require the
resolved widths to be the same number.

It also fails a display measure written in `ch` at all, which is the defect
itself rather than its symptom. Body measures stay in `ch` on purpose - there
`ch` is doing the job it exists for, holding a line to a character count - so
only selectors carrying the heading face or a display name are judged. Which
selectors those are is ci/_display_type.py's answer, not a second copy of it.

    python ci/check_measures.py                every measure, every sample set
    python ci/check_measures.py hero-stated    named patterns only
    python ci/check_measures.py --width 1024   a viewport; repeatable
    python ci/check_measures.py --as-ch        the positive control, below
    python ci/check_measures.py --require-browser

THE POSITIVE CONTROL. `--as-ch` re-renders every measure in the pre-v57 form
and requires this check to FIRE. A gate that has only ever been run against
code that passes has not been shown to catch anything, and this repository has
shipped one of those before. Exit 0 means the defect was detected.

CALIBRATION. The whole check is worthless if the hostile sample brand is not
hostile. preview/tokens-display.css builds its face out of `@font-face` +
`size-adjust` over a `local()` chain, and if that chain resolves nothing the
family is simply unavailable, --font-heading falls through to Georgia, and the
fifth brand becomes a fifth ordinary one - silently, and looking exactly like
a pass. So the face is measured before anything is reported, against its own
fallback stack, and a run that cannot show the adjustment took effect reports
nothing at all. See make_brand_shim.calibrated() for the same rule applied to
a contrast implementation.

Exit codes: 0 clean, or skipped because no browser is available; 1 at least
one measure differs across brands or is written in `ch`; 2 the request itself
is unusable; 3 the display fixture failed calibration, so nothing was
reported.
"""
import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
PATTERNS = ROOT / "patterns"
PREVIEW = ROOT / "preview"

import _display_type as display_type                  # noqa: E402
from build_preview import fill, repeat_block          # noqa: E402
from check_phone import SHELL, browser_unavailable, token_set   # noqa: E402

# 1280 is where the measures actually bind. Several of them sit inside a
# min-width media query and compute to `none` below it, and a run at a phone
# width would therefore compare nothing and call it identical - which is the
# shape of a gate that passes because it measured nothing. 1024 is here as a
# second width because one of the six changes at the 900px breakpoint and a
# single width cannot show a measure that only agrees at one of them.
WIDTHS = (1280, 1024)

# The measures resolve from em against a font-size that is itself identical
# across the sample sets, so the widths should agree to the bit. The tolerance
# is for the decimal string the browser hands back, not for layout: anything
# a person would call "nearly the same width" is a fault here, because the
# claim being tested is that they are the same width.
SAME_PX = 0.05

# What the calibration demands of preview/tokens-display.css, and why each
# number is the number.
#
# The fixture declares size-adjust: 142%. Measured against its OWN fallback
# stack - the same stack with the fixture family removed - that is the figure
# that should come back, and it is machine-independent in a way the absolute
# advance is not: the local() chain lands on whichever serif is installed, and
# a CI runner has a different one from a laptop. 1.30 leaves room for the two
# ends resolving to different faces and none for the adjustment being absent,
# which lands at exactly 1.00.
ADJUST_MIN = 1.30

# Being the widest of the five is the fixture's entire job. Past 15% it is
# plainly past anything the library had - the real spread among the original
# four is 26% - and between 1 and 15% the chain has landed on a narrow serif
# and wants a wider one added to it. That is worth saying and not worth
# failing a build over, so it warns. At or below parity it is not hostile at
# all and the build stops.
WIDEST_WARN = 1.15

# The sample brand whose face is meant to be the awkward one. Named rather
# than inferred, so that removing the fixture from preview/ fails this gate
# loudly instead of quietly reducing it to four agreeable brands.
HOSTILE = "display"

# The conversion TOKENS.md records, used only by --as-ch to reconstruct the
# pre-v57 form. It is a reconstruction and not a restoration: no em value can
# equal a character count on every face at once, which is the whole reason the
# move happened, so hero-stated comes back as 17.2ch where it was really 16ch.
# The spread the control reports is a property of `ch` itself and does not
# depend on which of those two numbers is used.
EM_PER_CH = 0.625

DECLARED = re.compile(
    r"(?<![-\w])(max-width|width|max-inline-size|inline-size)\s*:\s*([^;}]+)")
OWN_PROP = re.compile(r"(--[\w-]+)\s*:\s*([^;}]+)")
LENGTH = re.compile(r"(?<![\w.])(\d*\.?\d+)(em|ch)\b")
VAR_USE = re.compile(r"var\(\s*(--[\w-]+)\s*(?:,[^()]*)?\)")

# A selector this file cannot hand to querySelectorAll. A pseudo-element has
# no node, so a measure declared on one is invisible here; saying so is the
# difference between "not checked" and "checked and fine".
PSEUDO = re.compile(r"::")


# ------------------------------------------------------------- what to check

def sample_sets():
    """Every sample token set in preview/, discovered rather than listed.

    ci/build_preview.py names its four-plus-one because the preview index has
    a sentence to write about each. Here the answer wanted is "all of them",
    and a hardcoded list is how a sixth brand gets added and silently skipped.
    """
    return sorted(p.stem.split("tokens-", 1)[1]
                  for p in PREVIEW.glob("tokens-*.css"))


def measures(name):
    """(selector, property, declared, number, unit) for one pattern.

    A measure written through the pattern's own custom property is resolved
    one level, because that is how three of the six in this library are
    written and a check that could not see through `var()` would report on
    half of them.
    """
    css = (PATTERNS / name / "pattern.css").read_text(encoding="utf-8")
    display = display_type.display_selectors(css)
    rules = display_type.rules(css)
    own = {}
    for _sels, body in rules:
        for prop, value in OWN_PROP.findall(body):
            own.setdefault(prop, value.strip())

    found = []
    for sels, body in rules:
        for sel in sels:
            if sel not in display:
                continue
            for prop, value in DECLARED.findall(body):
                raw = value.strip()
                resolved = VAR_USE.sub(
                    lambda m: own.get(m.group(1), m.group(0)), raw)
                for number, unit in LENGTH.findall(resolved):
                    found.append((sel, prop, raw, float(number), unit))
    return found


def as_ch(css):
    """The stylesheet with every display measure back in `ch`.

    Rewrites the resolved number wherever it is declared, custom property
    included, so a measure reached through var() is converted too.
    """
    display = display_type.display_selectors(css)
    wanted = set()
    for sels, body in display_type.rules(css):
        for sel in sels:
            if sel not in display:
                continue
            for _prop, value in DECLARED.findall(body):
                for number, unit in LENGTH.findall(value):
                    if unit == "em":
                        wanted.add(number)
                for prop in VAR_USE.findall(value):
                    wanted.add(prop)
    numbers = {n for n in wanted if not str(n).startswith("--")}
    props = {p for p in wanted if str(p).startswith("--")}

    def swap(m):
        return "%gch" % (float(m.group(1)) / EM_PER_CH)

    out = []
    for line in css.splitlines(True):
        prop = OWN_PROP.search(line)
        if prop and prop.group(1) in props:
            out.append(LENGTH.sub(
                lambda m: swap(m) if m.group(2) == "em" else m.group(0), line))
            continue
        if any(n + "em" in line for n in numbers):
            out.append(re.sub(r"(?<![\w.])(%s)em\b"
                              % "|".join(re.escape(n) for n in sorted(numbers)),
                              swap, line))
            continue
        out.append(line)
    return "".join(out)


# ------------------------------------------------------------- the rendering

def pattern_page(name, width, tokens, ch=False):
    """The pattern in the same bare shell ci/check_phone.py measures in.

    Its own copy rather than check_phone.pattern_page, for one reason: this
    gate has to render a MUTATED stylesheet for the positive control, and a
    shared helper that took a stylesheet transform would be a parameter
    existing for one caller. The shell itself is imported, so the two gates
    cannot drift apart on the thing that would matter.
    """
    folder = PATTERNS / name
    markup = (folder / "pattern.html").read_text(encoding="utf-8")
    markup = re.sub(r"\s*<!--\n.*?\n-->", "", markup, count=1, flags=re.S)
    css = (folder / "pattern.css").read_text(encoding="utf-8")
    if ch:
        css = as_ch(css)
    sample_path = folder / "preview-content.json"
    sample = json.loads(sample_path.read_text(encoding="utf-8")) if sample_path.exists() else {}
    filled = fill(markup, sample)
    repeat = sample.get("_repeat")
    if repeat:
        filled = repeat_block(filled, repeat["class"], int(repeat["count"]))
    return SHELL.format(name=name, width=width, tokens=tokens, css=css,
                        markup=filled)


# The measurement, and the calibration, in one pass in the page. Observations
# only; what any of it means is decided in Python where it can be read.
MEASURE = r"""
(wanted) => {
  const out = { widths: {}, missing: [] };
  for (const w of wanted) {
    const el = document.querySelector(w.sel);
    if (!el) { out.missing.push(w.sel); continue; }
    out.widths[w.sel + '|' + w.prop] = getComputedStyle(el)[w.prop];
  }
  return out;
}
"""

ADVANCE = r"""
() => {
  const stack = getComputedStyle(document.documentElement)
                  .getPropertyValue('--font-heading').trim();
  // The same stack with its first family removed. On the display fixture
  // that is the fixture family itself, so this is what the page WOULD have
  // rendered in had the @font-face resolved nothing.
  const fallback = stack.split(',').slice(1).join(',').trim() || 'serif';
  const probe = document.createElement('span');
  probe.style.cssText = 'position:absolute;white-space:pre;visibility:hidden;'
                      + 'font-size:100px;font-weight:700;line-height:normal;';
  probe.textContent = '0000000000';
  document.body.appendChild(probe);
  const advance = family => {
    probe.style.fontFamily = family;
    return probe.getBoundingClientRect().width / 10 / 100;
  };
  return { stack, fallback, full: advance(stack), bare: advance(fallback) };
}
"""


class Ruler:
    """One browser, held open across every pattern and every brand.

    Same reasoning as ci/check_phone.py's Phone: a Chromium launch costs about
    sixty times what measuring a page costs, and a gate that launches per
    measurement is a gate nobody runs.
    """

    def __init__(self):
        self._pw = None
        self._browser = None
        self._dir = None

    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=True)
        # A real directory on disk, so the sample SVGs resolve as they would
        # on a page. A missing image has different dimensions from a real one.
        self._dir = Path(tempfile.mkdtemp(prefix="lander-measure-"))
        for asset in PREVIEW.glob("*.svg"):
            shutil.copy(asset, self._dir / asset.name)
        return self

    def __exit__(self, *exc):
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()
        if self._dir:
            shutil.rmtree(self._dir, ignore_errors=True)
        return False

    def _open(self, html, width):
        page = self._dir / f"m-{width}.html"
        page.write_text(html, encoding="utf-8", newline="\n")
        tab = self._browser.new_page(viewport={"width": width, "height": 900},
                                     device_scale_factor=1)
        tab.goto(page.as_uri())
        return tab

    def widths(self, html, width, wanted):
        tab = self._open(html, width)
        try:
            return tab.evaluate(MEASURE, wanted)
        finally:
            tab.close()

    def advance(self, html, width):
        tab = self._open(html, width)
        try:
            return tab.evaluate(ADVANCE)
        finally:
            tab.close()


# ------------------------------------------------------------- calibration

def calibration_faults(seen):
    """(fatal, lines) from the advances measured for each sample brand.

    Kept apart from the browser work so the decision can be tested on numbers
    rather than only ever exercised on whatever this machine happens to have
    installed - which is the one thing about this check that is not the same
    everywhere. `seen` is {set name: {full, bare, fallback}}, all in em.
    """
    lines, fatal = [], []
    if HOSTILE not in seen:
        return ([f"there is no preview/tokens-{HOSTILE}.css, so no sample "
                 f"brand has a face this library was not designed against. "
                 f"Every measure would then agree for the trivial reason that "
                 f"every brand ships a system stack"], lines)
    if len(seen) < 2:
        return ([f"only one sample token set, so there is nothing to compare "
                 f"a measure across"], lines)

    for name in sorted(seen):
        lines.append(f"{name:<9} bold digit {seen[name]['full']:.4f}em")

    got = seen[HOSTILE]
    adjusted = got["full"] / got["bare"] if got["bare"] else 0
    lines.append(f"{HOSTILE:<9} against its own fallback stack: "
                 f"{adjusted:.3f}x (declared size-adjust is 1.42x)")
    if adjusted < ADJUST_MIN:
        fatal.append(
            f"the {HOSTILE} fixture's face is {adjusted:.3f}x its own fallback "
            f"stack, under {ADJUST_MIN}x. The @font-face in "
            f"preview/tokens-{HOSTILE}.css resolved nothing, --font-heading "
            f"fell through to {got['fallback']}, and this run would have "
            f"compared five ordinary brands while looking exactly like a pass. "
            f"Add a face this machine actually has to its local() chain")

    others = {k: v["full"] for k, v in seen.items() if k != HOSTILE}
    widest = max(others, key=others.get)
    margin = got["full"] / others[widest] if others[widest] else 0
    lines.append(f"{HOSTILE:<9} against {widest}, the widest of the others: "
                 f"{margin:.3f}x")
    if margin <= 1.0:
        fatal.append(
            f"the {HOSTILE} fixture is not the widest sample brand - {widest} "
            f"is. Its whole job is to be past anything this library has met")
    elif margin < WIDEST_WARN:
        lines.append(
            f"WARNING {HOSTILE} is only {(margin - 1) * 100:.1f}% wider than "
            f"{widest}. The local() chain landed on a narrow serif on this "
            f"machine; add a wider one ahead of it")
    return fatal, lines


def calibrate(ruler, sets, width):
    """Prove the hostile sample brand is hostile, or report nothing.

    A fixture that has quietly stopped being a fixture is the failure mode
    this whole file guards, so it is measured before a single width is
    reported rather than inferred afterwards from results that would look
    perfectly normal either way.

    hero-stated is the page it measures in because every sample set is loaded
    into the same shell and any pattern would do; naming one keeps the probe
    from moving when the library's first folder alphabetically changes.
    """
    seen = {}
    for name in sets:
        seen[name] = ruler.advance(
            pattern_page("hero-stated", width, token_set(name)), width)
    return calibration_faults(seen)


# ------------------------------------------------------------------ the sweep

def sweep(ruler, names, sets, widths, ch=False):
    """Returns (rows, faults, notes). One row per measure per width.

    A row is (pattern, selector, property, declared, width, {set: px}).
    """
    rows, faults, notes = [], [], []
    for name in names:
        wanted = measures(name)
        if not wanted:
            continue
        for sel, prop, declared, number, unit in wanted:
            if unit == "ch" and not ch:
                faults.append(
                    f"{name}: {sel} sets {prop}: {declared} on display type. "
                    f"ch is the advance of zero in the face actually used, so "
                    f"this is a different width on every brand - which is the "
                    f"defect this gate exists for. Use em: {number * EM_PER_CH:g}em "
                    f"is the ratio the rest of the library converted at")
        askable = [{"sel": s, "prop": p} for s, p, _d, _n, _u in wanted
                   if not PSEUDO.search(s)]
        # Named rather than dropped. A measure this gate cannot reach is the
        # one place it can be silently blind, so it says so in the output.
        for s in sorted({s for s, _p, _d, _n, _u in wanted if PSEUDO.search(s)}):
            notes.append(
                f"{name}: {s} is a pseudo-element, which has no node to "
                f"measure. Its measure is NOT checked by this gate")
        for width in widths:
            per_set = {}
            for set_name in sets:
                html = pattern_page(name, width, token_set(set_name), ch=ch)
                got = ruler.widths(html, width, askable)
                per_set[set_name] = got["widths"]
            for sel, prop, declared, number, unit in wanted:
                if PSEUDO.search(sel):
                    continue
                # In the control the stylesheet was mutated, so the declared
                # text in the source is not what rendered. Printing the source
                # form would send a reader to a line that no longer says it.
                shown = declared
                if ch and unit == "em":
                    shown = f"{declared} rendered as {number / EM_PER_CH:g}ch"
                key = f"{sel}|{prop}"
                px = {s: per_set[s].get(key) for s in sets}
                rows.append((name, sel, prop, shown, width, px))
    return rows, faults, notes


def as_px(value):
    """The px number in a computed value, or None for `none` and `auto`."""
    if not value:
        return None
    m = re.match(r"(-?\d*\.?\d+)px$", value.strip())
    return float(m.group(1)) if m else None


def verdict(row):
    """(ok, sentence) for one measured row."""
    name, sel, prop, declared, width, px = row
    numbers = {k: as_px(v) for k, v in px.items()}
    unmeasured = sorted(k for k, v in numbers.items() if v is None)
    have = {k: v for k, v in numbers.items() if v is not None}
    if not have:
        return True, (f"{name} {sel} {prop}: {declared} at {width}px - does "
                      f"not apply on any sample brand at this width")
    if unmeasured:
        return False, (
            f"{name}: {sel} {prop}: {declared} resolves to a width on "
            f"{', '.join(sorted(have))} and to nothing on "
            f"{', '.join(unmeasured)} at {width}px - the same measure is "
            f"present on some brands and absent on others")
    lo, hi = min(have.values()), max(have.values())
    if hi - lo <= SAME_PX:
        return True, (f"{name} {sel} {prop}: {declared} at {width}px - "
                      f"{hi:.1f}px on all {len(have)}")
    spread = (hi / lo - 1) * 100 if lo else float("inf")
    worst = ", ".join(f"{k} {v:.1f}px" for k, v in sorted(have.items(),
                                                          key=lambda kv: kv[1]))
    return False, (
        f"{name}: {sel} {prop}: {declared} at {width}px renders "
        f"{spread:.1f}% wider on one sample brand than another - {worst}. "
        f"A display measure that depends on the face is a headline that "
        f"breaks to a different number of lines per brand")


def spread_of(rows, without=()):
    """The worst spread across every row, as a percentage.

    `without` drops named sample brands before measuring, which is how the
    control reports what the original four brands could show on their own
    against what the fifth adds. The four are the reason this file exists:
    they agreed closely enough that a 26% divergence read as noise.
    """
    worst = 0.0
    for row in rows:
        have = [v for v in (as_px(x) for k, x in row[5].items()
                            if k not in without) if v is not None]
        if len(have) > 1 and min(have):
            worst = max(worst, (max(have) / min(have) - 1) * 100)
    return worst


def main():
    ap = argparse.ArgumentParser(
        description="Check display measures render identically on every brand.")
    ap.add_argument("patterns", nargs="*",
                    help="pattern names; default every pattern in the library")
    ap.add_argument("--width", type=int, action="append",
                    help="a viewport width; repeatable. Default 1280 and 1024")
    ap.add_argument("--as-ch", action="store_true",
                    help="re-render every display measure in the pre-v57 ch "
                         "form and require this check to fire. Exit 0 means "
                         "the defect was detected")
    ap.add_argument("--require-browser", action="store_true",
                    help="treat a missing browser as a failure, not a skip")
    args = ap.parse_args()

    why = browser_unavailable()
    if why:
        print(f"display measures: SKIPPED - {why}")
        print("  Nothing was measured. This is not a pass.")
        # Right for a contributor in the web editor, wrong for CI, and which
        # of the two this is cannot be worked out here. See check_phone.py.
        return 1 if args.require_browser else 0

    widths = tuple(args.width) if args.width else WIDTHS
    names = args.patterns or sorted(
        f.name for f in PATTERNS.iterdir() if f.is_dir())
    for name in names:
        if not (PATTERNS / name / "pattern.css").exists():
            print(f"display measures: no pattern called {name!r} in patterns/")
            return 2
    sets = sample_sets()
    if not sets:
        print("display measures: no sample token sets in preview/")
        return 2

    with Ruler() as ruler:
        fatal, lines = calibrate(ruler, sets, widths[0])
        print(f"display measures: {len(names)} pattern(s) on "
              f"{len(sets)} sample brand(s) - {', '.join(sets)} - at "
              f"{', '.join(str(w) for w in widths)}px\n")
        print("  calibration, the hostile brand:")
        for line in lines:
            print(f"    {line}")
        print()
        if fatal:
            for line in fatal:
                print(f"  CALIBRATION FAILED  {line}")
            print("\n  Nothing was measured against a face this library was "
                  "not designed on, so nothing is reported.")
            return 3

        rows, faults, notes = sweep(ruler, names, sets, widths, ch=args.as_ch)

    quiet = []
    for row in rows:
        ok, line = verdict(row)
        (quiet if ok else faults).append(line)

    if args.as_ch:
        # The control. A run that finds nothing here has not proved the gate
        # harmless, it has proved the gate blind.
        print("  positive control: display measures re-rendered in ch, the "
              "pre-v57 form\n")
        for line in faults:
            print(f"  fired {line}")
        for line in notes:
            print(f"  note  {line}")
        worst = spread_of(rows)
        original = spread_of(rows, without={HOSTILE})
        if faults:
            print(f"\n  ok: {len(faults)} measure(s) diverge in ch. Worst "
                  f"spread {worst:.1f}% across {len(sets)} sample brand(s), "
                  f"{original:.1f}% across the {len(sets) - 1} that ship a "
                  f"system stack. The check catches what it was written for")
            return 0
        print(f"\n  FAIL  every measure agreed even in ch, worst spread "
              f"{worst:.1f}%. Either the sample brands all ship the same "
              f"face, or this gate is measuring nothing")
        return 1

    for line in faults:
        print(f"  FAIL  {line}")
    for line in notes:
        print(f"  note  {line}")
    for line in quiet:
        print(f"  ok    {line}")
    worst = spread_of(rows)
    print()
    if faults:
        print(f"  {len(faults)} measure(s) do not render identically, worst "
              f"spread {worst:.1f}% across {len(sets)} sample brand(s)")
        return 1
    print(f"  clean: {len(rows)} rendered measure(s), {worst:.2f}% spread "
          f"across {len(sets)} sample brand(s), one of them a face this "
          f"library was not designed on")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
