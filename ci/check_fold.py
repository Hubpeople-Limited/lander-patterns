#!/usr/bin/env python3
"""Put a full-viewport pattern in a page with real furniture and measure it.

`ci/check_page.py` reads source: it knows a section subtracts SOMETHING for
what sits above it. `ci/check_phone.py` renders, but it renders one pattern
alone in a bare document - no header above it and no site footer below it, at
a fixed 760px tall viewport. So between them, nothing in this repository has
ever measured a full-viewport pattern against its own claim.

A page built from `hero-squeeze` - the pattern whose whole premise is one
viewport and nothing below the fold - overflowed a 1280x800 laptop by 177px on
a live site. 166 of those 177 were a site footer the platform injects at serve
time, which is in no pattern's markup and was in nobody's arithmetic. Every
gate in this repository passed it.

This is the gate that would not have. It assembles a page the way the platform
serves one - this library's own masthead-nav above, a stand-in site footer
below - renders it at real device viewport sizes, and holds each pattern to the
promise its own metadata makes:

    whole-page: yes     the DOCUMENT must not scroll. The pattern says it is
                        the page, so the footer is inside its promise.
    everything else     the SECTION's foot must be at or above the fold. The
                        page continues under it, so the footer is not.

WHAT IT COMPARES, and this is the whole of it: the furniture the section's own
`calc()` SET ASIDE, against the furniture that actually RENDERED. Both numbers
come off the page. The allowance is read as the viewport minus the RESOLVED
`min-height`, never re-derived from the token text, because a token is a claim
about the page and this gate exists to check claims about the page against the
page. The measurement is the rendered height of the header the platform serves
and of the footer it injects.

That framing is not decoration. On 2026-08-26 this gate went red on a CI runner
and green on the machine it was written on, for the same commit. The display
fixture's heading face is a `local()` chain, the runner has no Georgia, it
landed on a wider serif, `masthead-nav`'s wide menu wrapped onto a third line,
and the header rendered 173.8px where `--page-header-height` had set aside 152.
What the gate said was that the section's foot was 22px below the fold - true,
and no help at all in finding a font. It now names which number is wrong and
what the page measured instead, because the fault was never the overflow: the
overflow is only what an understated allowance looks like from the far end.

The two are the same arithmetic while the section sits on its floor, and that
is the point of the change rather than an argument against it. A section whose
CONTENT has grown past the floor overflows for a reason no token can fix, so
the old test had to stay silent there - and stayed silent about a wrong
allowance underneath it too. `hero-squeeze` is content-bound at most viewports
in this library, which means its furniture arithmetic could not be failed by
this gate at all. Now it can.

    python ci/check_fold.py                 every full-viewport pattern
    python ci/check_fold.py hero-squeeze
    python ci/check_fold.py --broken        the positive control, below
    python ci/check_fold.py --out /tmp/fold keep the assembled pages
    python ci/check_fold.py --require-browser

THE POSITIVE CONTROL. `--broken` re-renders every page with the furniture
tokens set the way the live defect had them - a header height derived from a
70px logo, and no footer allowance at all - and requires this check to FIRE. A
gate that has only ever run against code that passes has not been shown to
catch anything. Exit 0 on that run means the defect was detected.

WHICH PATTERNS. Discovered, not listed: any pattern whose CSS claims a viewport
height, minus ci/check_page.py's FULL_VIEWPORT_EXEMPT - the mid-page and
closing patterns, which have nothing above them in the viewport by the time a
reader arrives. Naming them here instead would leave the next full-viewport
opener out of this gate on the day it lands, which is how the fold rule reached
five openers out of six once already.

Exit codes: 0 clean, or skipped because no browser is available; 1 at least one
page does not fit; 2 the request itself is unusable.
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

from build_preview import fill, repeat_block                    # noqa: E402
from check_phone import browser_unavailable, token_set          # noqa: E402
from check_page import (FULL_VIEWPORT_EXEMPT, VIEWPORT_HEIGHT,  # noqa: E402
                        parse_meta, strip_css_comments)

# Width AND height, which is the difference between this gate and every other
# one here. ci/check_phone.py varies the width and holds the height at 760,
# because the defects it hunts are horizontal. Every defect this file hunts is
# vertical, so a viewport height that is not a real device's proves nothing.
#
# 1280x800 and 1440x900 are the two commonest laptops. 390x844 is a current
# iPhone, 360x740 the commonest Android. 320x568 is the floor - an SE-sized
# phone, and the one viewport in this list where a squeeze page's own content
# is taller than the space left for it.
VIEWPORTS = ((1280, 800), (1440, 900), (390, 844), (360, 740), (320, 568))

# The header the platform actually serves above a canvas page: this library's
# own, not a stand-in. Its height is the number the fold arithmetic turns on,
# so measuring against a fake one would measure the fake.
HEADER = "masthead-nav"

# The site footer is NOT in this library. The platform injects it at serve
# time, so there is nothing here to render and a stand-in is the only option.
# These two heights are what it measures on a live brand in Chromium, and the
# breakpoint is where the footer's own layout changes:
#
#     320-560px   196.8px
#     640px up    165.8px
#
# Rounded up by a fraction of a pixel, which is the direction that makes this
# gate harder to pass rather than easier. A stand-in with a stated provenance
# beats a re-implementation nobody can check, and it is the same shape as
# ci/check_page.py's stand-in header.
FOOTER_TALL, FOOTER_SHORT, FOOTER_BREAK = 197, 166, 640

# What the live defect had in it: a header allowance derived from a 70px logo
# by a rule that has since been withdrawn, and no footer allowance at all
# because nothing in the guidance mentioned one. --broken puts these back.
BROKEN = "--page-header-height: 5.75rem; --page-footer-height: 0px;"

SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name} at {width}x{height}</title>
<style>
{tokens}
:root {{ {overrides} }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: var(--font-body); background: var(--color-bg);
       color: var(--color-text); line-height: 1.6; }}
{header_css}
{css}
/* The site footer the platform injects under every canvas page. Not a
   pattern, and not in this library - see FOOTER_TALL in ci/check_fold.py for
   where its two heights come from. */
.fold-check-footer {{ height: {footer}px; display: flex; align-items: center;
  justify-content: center; background: var(--color-surface-soft);
  color: var(--color-text-soft); font-size: 0.875rem; }}
</style>
</head>
<body>
{header}
<main>
{markup}
</main>
<footer class="fold-check-footer">the site footer, {footer}px</footer>
</body>
</html>
"""


def full_viewport(name, css):
    """Does this pattern claim a whole viewport? check_page.py's question."""
    return bool(VIEWPORT_HEIGHT.search(strip_css_comments(css))) \
        and name not in FULL_VIEWPORT_EXEMPT


def filled(name):
    """One pattern's markup, with its sample content in it."""
    folder = PATTERNS / name
    markup = (folder / "pattern.html").read_text(encoding="utf-8")
    markup = re.sub(r"\s*<!--\n.*?\n-->", "", markup, count=1, flags=re.S)
    sample = folder / "preview-content.json"
    data = json.loads(sample.read_text(encoding="utf-8")) if sample.exists() else {}
    out = fill(markup, data)
    repeat = data.get("_repeat")
    if repeat:
        out = repeat_block(out, repeat["class"], int(repeat["count"]))
    return out


def page(name, width, height, tokens, overrides=""):
    """The pattern, under a real header and over a stand-in site footer."""
    footer = FOOTER_TALL if width < FOOTER_BREAK else FOOTER_SHORT
    return SHELL.format(
        name=name, width=width, height=height, tokens=tokens,
        overrides=overrides, footer=footer,
        header_css=(PATTERNS / HEADER / "pattern.css").read_text(encoding="utf-8"),
        header=filled(HEADER), markup=filled(name),
        css=(PATTERNS / name / "pattern.css").read_text(encoding="utf-8"))


# One pass in the page. Observations, not verdicts - what counts as a fault is
# decided in Python, where it can be read and argued with.
MEASURE = r"""
(selector) => {
  const doc = document.documentElement;
  const el = document.querySelector(selector);
  const head = document.querySelector('header');
  const foot = document.querySelector('.fold-check-footer');
  const px = n => Math.round(n * 10) / 10;
  return {
    viewport: doc.clientHeight,
    scroll: doc.scrollHeight,
    header: head ? px(head.getBoundingClientRect().height) : 0,
    section: el ? px(el.getBoundingClientRect().height) : null,
    foot: el ? px(el.getBoundingClientRect().bottom) : null,
    // The resolved calc(), in px. What separates "the arithmetic is wrong"
    // from "the words are too long for the box" - see verdict().
    floor: el ? getComputedStyle(el).minHeight : 'auto',
    footer: foot ? px(foot.getBoundingClientRect().height) : 0,
  };
}
"""


class Shell:
    """One browser, held open across every page. Same reason as check_phone."""

    def __init__(self):
        self._pw = self._browser = self._dir = None

    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=True)
        # A real directory, so the sample SVGs resolve. A broken image has
        # different dimensions from the real one, and this gate is entirely
        # about dimensions.
        self._dir = Path(tempfile.mkdtemp(prefix="lander-fold-"))
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

    def measure(self, html, selector, width, height):
        path = self._dir / f"fold-{width}x{height}.html"
        path.write_text(html, encoding="utf-8", newline="\n")
        tab = self._browser.new_page(viewport={"width": width, "height": height},
                                     device_scale_factor=1)
        try:
            tab.goto(path.as_uri())
            return tab.evaluate(MEASURE, selector)
        finally:
            tab.close()


def box_bound(got):
    """Is the section sitting on its own min-height, or on its content?

    Kept because the two cases read differently in the report and one of them
    is nobody's arithmetic to fix. It is no longer what decides a fault - see
    verdict() for why that had to change.

    This is the whole difference between the two things that make a page
    overflow, and only one of them is this library's arithmetic:

      box-bound      the section is exactly as tall as calc() said. Whatever
                     overflows, overflows because the sum was wrong, and the
                     sum is entirely inside this repository. That is the
                     defect this gate exists for.
      content-bound  the content is taller than the box, so the section grew
                     past its floor. hero-squeeze's README calls this out as
                     the deliberate failure mode - a short scroll rather than
                     a hidden join button - and what it depends on is the copy
                     somebody placed, which no dial can fix. Reported, never
                     failed: failing it would make this gate an opinion about
                     sample content, and a gate with a false positive in it is
                     one everybody stops reading.
    """
    floor = got.get("floor") or "auto"
    if not floor.endswith("px"):
        return False                      # `auto`, or a keyword: no floor
    try:
        return got["section"] <= float(floor[:-2]) + 1
    except ValueError:
        return False


def furniture(got, whole_page):
    """(allowed, rendered) px of page furniture, or None if there is no floor.

    ALLOWED is what the section's own arithmetic set aside, taken from the page
    rather than from the stylesheet: every full-viewport rule in this library
    is `100svh` minus its furniture tokens, `100svh` is the viewport in a page
    served like this one, so the viewport minus the RESOLVED min-height is the
    allowance with every `var()`, fallback and media query already applied. Read
    it this way and a brand that sets the token in a media query, or leaves it
    to the default, or writes it in `em`, all measure the same. Re-derive it
    from the token text instead and the gate is reading a claim, which is the
    habit that put the claim wrong in the first place.

    RENDERED is what the furniture measured. The header always. The site footer
    only for a `whole-page` pattern, whose promise is about the page and so
    covers everything on it; an opener promises about its own foot, and the
    page continues under that foot with the footer at the bottom of all of it.

    None when there is no px floor to read - `auto`, or a keyword. A section
    that claims no height has made no arithmetic claim to check.
    """
    floor = got.get("floor") or "auto"
    if not floor.endswith("px"):
        return None
    try:
        allowed = got["viewport"] - float(floor[:-2])
    except ValueError:
        return None
    return allowed, got["header"] + (got["footer"] if whole_page else 0)


def verdict(name, whole_page, got, width, height):
    """The fault this page has, as a sentence, or None.

    ONE test: did the furniture render taller than the section set aside for
    it? That is this library's arithmetic and nothing else's, it is wrong
    wherever it lands, and it is wrong whether or not anything visibly
    overflowed - a section whose content has grown past its floor can be
    sitting on a badly understated allowance and never show it, which is
    exactly the state `hero-squeeze` is in at most viewports here.

    It replaces a test on the overflow itself, which was the same arithmetic
    seen from the far end and could only be trusted while the section was
    box-bound. While it IS box-bound the two are algebraically identical -
    section == floor, so `header + section - viewport` and `rendered - allowed`
    are the same subtraction - which is why every case this file has ever been
    tested on keeps the verdict it had. What changes is the half that was
    unreachable, and the sentence, which now names the token that is wrong
    instead of the pixel count that is downstream of it.

    1px of tolerance, for the same reason check_phone allows one: a rect
    resolving to 799.6 against an 800 viewport is a rounding artefact.
    """
    both = furniture(got, whole_page)
    if both is None:
        return None
    allowed, rendered = both
    short = rendered - allowed
    if short <= 1:
        return None
    if whole_page:
        return (f"{name}: the section set aside {round(allowed)}px for this "
                f"page's furniture at {width}x{height} and the furniture "
                f"rendered {round(rendered, 1)} - header {got['header']} plus "
                f"footer {got['footer']}, {round(short)}px more than "
                f"--page-header-height and --page-footer-height allow between "
                f"them. This pattern is whole-page: yes, so the footer under it "
                f"is part of what it promised and belongs in the sum")
    return (f"{name}: the section set aside {round(allowed)}px for what sits "
            f"above it at {width}x{height} and {HEADER} rendered "
            f"{got['header']} - {round(short)}px more than "
            f"--page-header-height allows. The section claims that {round(short)}"
            f"px of viewport anyway, so the join control at its foot is below "
            f"the fold")


def sweep(shell, names, tokens, viewports, overrides=""):
    """Every named pattern at every viewport. Returns (faults, rows)."""
    faults, rows = [], []
    for name in names:
        meta = parse_meta((PATTERNS / name / "pattern.html")
                          .read_text(encoding="utf-8"))
        whole = meta.get("whole-page") == "yes"
        for width, height in viewports:
            html = page(name, width, height, tokens, overrides)
            got = shell.measure(html, f".{name}", width, height)
            rows.append((name, width, height, whole, got))
            bad = verdict(name, whole, got, width, height)
            if bad:
                faults.append(bad)
    return faults, rows


def candidates():
    """Every full-viewport pattern in the library, discovered from its CSS."""
    out = []
    for folder in sorted(p for p in PATTERNS.iterdir() if p.is_dir()):
        css_path = folder / "pattern.css"
        if css_path.is_file() and full_viewport(
                folder.name, css_path.read_text(encoding="utf-8")):
            out.append(folder.name)
    return out


def main():
    ap = argparse.ArgumentParser(
        description="Render full-viewport patterns in a page with a real "
                    "header and a site footer, and measure what came out.")
    ap.add_argument("patterns", nargs="*",
                    help="pattern names; default every full-viewport pattern")
    ap.add_argument("--tokens", default="brand",
                    help="which preview token set to render on (default brand)")
    ap.add_argument("--broken", action="store_true",
                    help="the positive control: render with the furniture "
                         "tokens as the live defect had them and require this "
                         "check to fire")
    ap.add_argument("--out", help="directory to keep the assembled pages in")
    ap.add_argument("--require-browser", action="store_true",
                    help="treat a missing browser as a failure, not a skip")
    args = ap.parse_args()

    why = browser_unavailable()
    if why:
        print(f"the fold: SKIPPED - {why}")
        print("  Nothing was measured. This is not a pass.")
        return 1 if args.require_browser else 0

    try:
        tokens = token_set(args.tokens)
    except FileNotFoundError:
        print(f"the fold: no preview token set called {args.tokens!r}")
        return 2

    names = args.patterns or candidates()
    for name in names:
        if not (PATTERNS / name / "pattern.html").exists():
            print(f"the fold: no pattern called {name!r} in patterns/")
            return 2
    if not names:
        print("the fold: no full-viewport pattern in the library to measure. "
              "That is not a pass - check ci/check_page.py's VIEWPORT_HEIGHT")
        return 2

    overrides = BROKEN if args.broken else ""
    sizes = ", ".join(f"{w}x{h}" for w, h in VIEWPORTS)
    print(f"the fold: {len(names)} pattern(s) under {HEADER} and over a "
          f"{FOOTER_SHORT}/{FOOTER_TALL}px site footer, at {sizes}, on the "
          f"{args.tokens} tokens")
    if args.broken:
        print(f"  positive control: :root {{ {BROKEN} }}\n")
    else:
        print()

    out_dir = Path(args.out) if args.out else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        for name in names:
            for width, height in VIEWPORTS:
                (out_dir / f"{name}--{width}x{height}.html").write_text(
                    page(name, width, height, tokens, overrides),
                    encoding="utf-8", newline="\n")

    with Shell() as shell:
        faults, rows = sweep(shell, names, tokens, VIEWPORTS, overrides)

    grown = 0
    for name, width, height, whole, got in rows:
        used = got["header"] + got["section"] + (got["footer"] if whole else 0)
        room = got["viewport"] - used
        how = "at its floor" if box_bound(got) else "grown past its floor"
        if not box_bound(got):
            grown += 1
        # The two numbers the verdict turns on, on every row and not only the
        # failing ones. A row that passes with 2px of allowance left is worth
        # seeing before the day it does not.
        both = furniture(got, whole)
        if both is None:
            says = "no px floor to read"
        else:
            allowed, rendered = both
            says = (f"furniture {rendered:g} of {allowed:g} allowed"
                    + (f" (header {got['header']:g} + footer {got['footer']:g})"
                       if whole else ""))
        print(f"  {name} {width}x{height}: {says}, section "
              f"{got['section']} {how}"
              + f" - {'spare' if room >= 0 else 'OVER'} {abs(round(room))}px")
    if grown:
        print()
        print(f"  {grown} row(s) with the section grown past its floor: the "
              f"content is taller than the room left for it, which is the "
              f"documented failure mode and is not this arithmetic's to fix")
    print()
    for line in faults:
        print(f"  FAIL  {line}")

    if args.broken:
        # The control is the other way up: a clean run here means the gate
        # cannot see the defect it was written for, which is the worst result
        # this file can produce and must not be reported as a pass.
        if faults:
            print(f"  control: {len(faults)} fault(s) caught with the "
                  f"furniture tokens as the defect had them. The gate fires.")
            return 0
        print("  CONTROL FAILED: every page fitted with the furniture tokens "
              "set the way the live defect had them. This gate cannot see the "
              "thing it exists for.")
        return 1

    if not faults:
        print(f"  clean: {len(names)} pattern(s) at {len(VIEWPORTS)} viewport(s) "
              f"- nothing promised a fold it does not keep")
    if out_dir:
        print(f"\n  pages written to {out_dir}")
    return 1 if faults else 0


if __name__ == "__main__":
    raise SystemExit(main())
