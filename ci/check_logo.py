#!/usr/bin/env python3
"""Render the brand logo the way real brands ship it, and check it is drawn.

Every image in this library's previews carries `width` and `height` attributes
and a `sample-*.svg` that carries them too, so every gate here has only ever
measured a logo whose size the browser already knew. Real brand logos are not
like that. A brand mark is almost always an SVG exported with a `viewBox` and
nothing else: it has a RATIO and no intrinsic size at all.

That is a different sizing problem, and `masthead-nav` got it wrong. Below
60rem its logo rule set `width: auto; height: auto` under a `max-width` and a
`max-height`, which is two ceilings and no floor. An image with intrinsic
dimensions settles on those and is capped; an image with only a ratio has
nothing to settle on and resolves to **0x0**. The header rendered with no brand
mark on it, on every phone and tablet, on every brand using any of this
library's six page shells - and every gate in this repository passed it,
because the sample logo has a width and a height on it.

So this gate renders the pattern against logo files of the shapes brands
actually ship - a ratio-only wordmark, a ratio-only square, and a sized
wordmark as the control - across the 60rem boundary the defect lived under,
and holds the mark to two things:

    it is DRAWN          a box of at least a few pixels each way
    it is the RIGHT SIZE the box is as tall as --logo-height resolved to

and reports, as a third fault, a mark whose box has been squashed out of its
file's own ratio - which is what happens if a height is pinned without
`object-fit` to go with it.

    python ci/check_logo.py                  every pattern that carries a logo
    python ci/check_logo.py masthead-nav
    python ci/check_logo.py --broken         the positive control, below
    python ci/check_logo.py --tokens display
    python ci/check_logo.py --out /tmp/logo  keep the rendered pages
    python ci/check_logo.py --require-browser

THE POSITIVE CONTROL. `--broken` re-renders every page with one rule appended
that puts the logo back the way the defect had it - `height: auto` under a
`max-height` - and requires this check to FIRE. A gate that has only ever run
against code that passes has not been shown to catch anything. Exit 0 on that
run means the defect was detected. The override is appended rather than spliced
into the stylesheet so that rewording the rule cannot quietly disarm it.

WHICH PATTERNS. Discovered, not listed: any pattern whose markup carries an
`<img>` on the `{{logo.src}}` furniture token. One does today. Naming it here
would leave the next pattern that carries a brand mark outside this gate on the
day it lands, which is the mistake the fold rule made once already.

Exit codes: 0 clean, or skipped because no browser is available; 1 at least one
logo is not drawn as it should be; 2 the request itself is unusable.
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

from build_preview import fill, repeat_block            # noqa: E402
from check_phone import SHELL, browser_unavailable      # noqa: E402

# The widths straddle 60rem deliberately. The live defect was invisible above
# it and total below it, so a gate that sampled one side would have reported
# a clean library either way. 320 and 360 are the phone floor and the phone
# mode this repo already measures at; 768 and 900 are the tablet band where
# the small-screen rules still apply; 1024 and 1280 are the far side.
WIDTHS = (320, 360, 768, 900, 1024, 1280)

# The shapes a brand mark actually arrives in. `ratio` is the file's own
# width-to-height, which this gate knows because it writes the file.
#
# The two ratio-only entries are the defect's own shape: a viewBox and no
# width or height attribute anywhere. `wordmark-sized` is the control - the
# same mark with its dimensions declared, which is what every other gate in
# this repository has always measured and is why none of them saw this.
FIXTURES = {
    "wordmark-ratio-only": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 104">'
               '<rect width="500" height="104" fill="#7a2e3c"/></svg>',
        "ratio": 500 / 104,
        "attrs": True,
        "why": "the ordinary brand wordmark: a viewBox and nothing else",
    },
    "wordmark-ratio-only-bare": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 104">'
               '<rect width="500" height="104" fill="#7a2e3c"/></svg>',
        "ratio": 500 / 104,
        "attrs": False,
        "why": "the same file with the img's width and height attributes "
               "dropped, which is what a hand-written page tends to do",
    },
    "square-ratio-only": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">'
               '<rect width="120" height="120" fill="#7a2e3c"/></svg>',
        "ratio": 1.0,
        "attrs": True,
        "why": "a square mark, where the width cap can never be what saves it",
    },
    "wordmark-sized": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 104" '
               'width="500" height="104">'
               '<rect width="500" height="104" fill="#7a2e3c"/></svg>',
        "ratio": 500 / 104,
        "attrs": True,
        "why": "the control: the same mark with intrinsic dimensions, the "
               "only shape this library measured before this gate",
    },
}

# A box under this many pixels in either direction is a mark nobody can see.
# The defect renders exactly 0, so the threshold is not doing fine judgement -
# it is there so that a mark rendered at half a pixel reads as absent rather
# than as present and small.
DRAWN_PX = 4.0
# --logo-height is the height the mark is asked to render at. A tenth of a
# pixel is layout; a pixel is a rule not being applied.
HEIGHT_TOLERANCE_PX = 1.0
# The box may be letterboxed around the ink, which is what object-fit is for.
# What it may not be is stretched: a box whose own ratio has left the file's
# by more than this, with object-fit filling it, is a distorted logo.
RATIO_TOLERANCE = 0.02

LOGO_IMG = re.compile(
    r"<img\b[^>]*\bsrc\s*=\s*[\"']\{\{\s*logo\.src\s*\}\}[\"'][^>]*>", re.I)
CLASS_OF = re.compile(r"\bclass\s*=\s*[\"']([^\"']+)[\"']", re.I)
SIZE_ATTRS = re.compile(r"\s+(?:width|height)\s*=\s*[\"'][^\"']*[\"']", re.I)

# --logo-height is a token, so its value is `2.75rem` or whatever the brand
# wrote, and reading the custom property gives that text rather than a length.
# A probe element carrying the same declaration the pattern carries - fallback
# included - is measured instead, so the number compared against is the number
# the browser actually resolved, on this page, at this width.
MEASURE = """
(selector) => {
  const img = document.querySelector(selector);
  if (!img) return { missing: true };
  const round = n => Math.round(n * 10) / 10;
  const probe = document.createElement('div');
  probe.style.cssText =
    'position:absolute;left:-9999px;top:0;width:1px;' +
    'height:var(--logo-height, 2.75rem);';
  (img.parentElement || document.body).appendChild(probe);
  const wanted = round(probe.getBoundingClientRect().height);
  probe.remove();
  const r = img.getBoundingClientRect();
  return {
    width: round(r.width), height: round(r.height),
    fit: getComputedStyle(img).objectFit,
    logoHeight: wanted,
  };
}
"""


def carries_a_logo(name):
    """The class on this pattern's logo image, or None if it has no logo."""
    markup = (PATTERNS / name / "pattern.html")
    if not markup.is_file():
        return None
    tag = LOGO_IMG.search(markup.read_text(encoding="utf-8"))
    if not tag:
        return None
    classes = CLASS_OF.search(tag.group(0))
    # A logo with no class of its own cannot be measured or overridden by
    # selector, and this library requires every rule to name a pattern class,
    # so there is nothing to fall back to. Say so rather than skipping.
    return classes.group(1).split()[0] if classes else ""


def discover():
    return sorted(f.name for f in PATTERNS.iterdir()
                  if f.is_dir() and carries_a_logo(f.name) is not None)


def token_set(which):
    path = PREVIEW / f"tokens-{which}.css"
    if not path.is_file():
        raise SystemExit(f"no sample token set called {which!r} "
                         f"({path} does not exist)")
    return path.read_text(encoding="utf-8")


def page(name, fixture, width, tokens, broken_class=None):
    """The pattern, with one fixture logo in it, in the bare preview shell."""
    folder = PATTERNS / name
    markup = re.sub(r"\s*<!--\n.*?\n-->", "",
                    (folder / "pattern.html").read_text(encoding="utf-8"),
                    count=1, flags=re.S)
    css = (folder / "pattern.css").read_text(encoding="utf-8")
    sample_path = folder / "preview-content.json"
    sample = (json.loads(sample_path.read_text(encoding="utf-8"))
              if sample_path.exists() else {})
    filled = fill(markup, sample)
    repeat = sample.get("_repeat")
    if repeat:
        filled = repeat_block(filled, repeat["class"], int(repeat["count"]))

    spec = FIXTURES[fixture]

    def swap(match):
        tag = match.group(0)
        if not spec["attrs"]:
            tag = SIZE_ATTRS.sub("", tag)
        return tag
    # fill() has already put the sample logo's filename in place of the token,
    # so the swap is on the resolved src rather than on {{logo.src}}.
    filled = LOGO_IMG.sub(swap, filled)
    filled = filled.replace("sample-wordmark.svg", f"{fixture}.svg")

    if broken_class:
        # The defect, reinstated: two ceilings and no floor. Appended, never
        # spliced, so that rewording the shipped rule cannot disarm the
        # control without anybody noticing.
        css += (f"\n.{broken_class} {{ height: auto; "
                f"max-height: var(--logo-height, 2.75rem); "
                f"object-fit: fill; }}\n")
    return SHELL.format(name=f"{name}--{fixture}", width=width,
                        tokens=tokens, css=css, markup=filled)


class Shell:
    """One browser and one asset directory, held open across every render."""

    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=True)
        self._dir = Path(tempfile.mkdtemp(prefix="lander-logo-"))
        for asset in PREVIEW.glob("*.svg"):
            shutil.copy(asset, self._dir / asset.name)
        for fixture, spec in FIXTURES.items():
            (self._dir / f"{fixture}.svg").write_text(spec["svg"],
                                                      encoding="utf-8")
        return self

    def __exit__(self, *exc):
        self._browser.close()
        self._pw.stop()
        shutil.rmtree(self._dir, ignore_errors=True)
        return False

    def measure(self, html, width, selector):
        path = self._dir / f"logo-{width}.html"
        path.write_text(html, encoding="utf-8", newline="\n")
        tab = self._browser.new_page(viewport={"width": width, "height": 900},
                                     device_scale_factor=1)
        try:
            tab.goto(path.as_uri())
            return tab.evaluate(MEASURE, selector)
        finally:
            tab.close()


def verdict(name, fixture, width, got):
    """Every fault for one render, as sentences."""
    where = f"{name} {fixture} at {width}px"
    if got.get("missing"):
        return [f"{where}: the logo image is not in the rendered page at all"]
    faults = []
    w, h = got["width"], got["height"]
    if w < DRAWN_PX or h < DRAWN_PX:
        return [f"{where}: the brand mark renders {w}x{h}px - it is not "
                f"drawn. An image with a ratio and no intrinsic size needs a "
                f"set height; two ceilings give it nothing to resolve against"]
    wanted = got["logoHeight"]
    if wanted and abs(h - wanted) > HEIGHT_TOLERANCE_PX:
        faults.append(
            f"{where}: the mark is {h}px tall where --logo-height resolves to "
            f"{wanted}px. The header reserves room for one and draws the other")
    ratio = FIXTURES[fixture]["ratio"]
    drawn = w / h if h else 0
    if got["fit"] == "fill" and abs(drawn - ratio) / ratio > RATIO_TOLERANCE:
        faults.append(
            f"{where}: the box is {drawn:.2f}:1 where the file is "
            f"{ratio:.2f}:1, and object-fit is `fill`, so the mark is "
            f"stretched. Pin a height and the width follows the ratio only "
            f"while object-fit says it may")
    return faults


def sweep(shell, names, tokens, widths, broken=False):
    faults, rows = [], []
    for name in names:
        logo_class = carries_a_logo(name)
        if logo_class == "":
            faults.append(f"{name}: its logo image carries no class, so no "
                          f"rule in this library can reach it and this gate "
                          f"cannot measure it")
            continue
        selector = f".{logo_class}"
        for fixture in FIXTURES:
            for width in widths:
                html = page(name, fixture, width, tokens,
                            logo_class if broken else None)
                got = shell.measure(html, width, selector)
                rows.append((name, fixture, width, got))
                faults.extend(verdict(name, fixture, width, got))
    return faults, rows


def main():
    ap = argparse.ArgumentParser(
        description="Render each pattern's brand mark as the shapes real "
                    "brands ship and check it is drawn at the size the header "
                    "reserved for it. See the module docstring.")
    ap.add_argument("names", nargs="*", help="patterns to check (default: "
                                             "every pattern carrying a logo)")
    ap.add_argument("--tokens", default="brand",
                    help="sample token set to render against (default: brand)")
    ap.add_argument("--broken", action="store_true",
                    help="the positive control: reinstate the defect and "
                         "require this check to fire")
    ap.add_argument("--out", help="write the rendered pages here")
    ap.add_argument("--require-browser", action="store_true",
                    help="treat a missing browser as a failure, not a skip")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    names = args.names or discover()
    if not names:
        print("no pattern in this library carries a {{logo.src}} image")
        return 0
    for name in names:
        if not (PATTERNS / name).is_dir():
            print(f"no pattern called {name!r}")
            return 2
        if carries_a_logo(name) is None:
            print(f"{name} carries no {{{{logo.src}}}} image, so there is "
                  f"nothing here to measure")
            return 2

    why = browser_unavailable()
    if why:
        if args.require_browser:
            print(f"FAIL logo: no browser, and --require-browser was asked "
                  f"for - {why}")
            return 1
        print(f"SKIPPED logo: {why}. A skip is not a pass.")
        return 0

    tokens = token_set(args.tokens)
    print(f"logo shapes: {len(names)} pattern(s), {len(FIXTURES)} logo "
          f"shape(s), {len(WIDTHS)} width(s), on the {args.tokens} tokens"
          + ("  [control: the defect reinstated]" if args.broken else ""))
    print()

    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        for name in names:
            logo_class = carries_a_logo(name)
            for fixture in FIXTURES:
                for width in WIDTHS:
                    (out / f"{name}--{fixture}--{width}.html").write_text(
                        page(name, fixture, width, tokens,
                             logo_class if args.broken else None),
                        encoding="utf-8", newline="\n")

    with Shell() as shell:
        faults, rows = sweep(shell, names, tokens, WIDTHS, args.broken)

    # Every row, not only the failing ones. The number worth seeing before the
    # day it fails is the one that is nearly wrong.
    for name, fixture, width, got in rows:
        if got.get("missing"):
            continue
        print(f"  {name} {fixture} {width}px: {got['width']}x{got['height']}"
              f"  --logo-height {got['logoHeight']}  object-fit {got['fit']}")
    print()
    for line in faults:
        print(f"  FAIL  {line}")

    if args.broken:
        if faults:
            print(f"  control: {len(faults)} fault(s) caught with the logo "
                  f"rule as the defect had it. The gate fires.")
            return 0
        print("  CONTROL FAILED: every brand mark drew correctly with the "
              "logo rule set the way the defect had it. This gate cannot see "
              "the thing it exists for.")
        return 1

    if not faults:
        print(f"  clean: every brand mark drawn at --logo-height, "
              f"{len(rows)} render(s)")
    if args.out:
        print(f"\n  pages written to {args.out}")
    return 1 if faults else 0


if __name__ == "__main__":
    raise SystemExit(main())
