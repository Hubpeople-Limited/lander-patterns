#!/usr/bin/env python3
"""Render the brand logo the way real brands ship it, and check it is drawn
- and, on the brand-colour ground, that it can be seen.

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
    it is the RIGHT SIZE the box is as tall as the pattern's own height
                         declaration for it resolved to - `--logo-height`
                         in the header, a multiple of it in a footer

and reports, as a third fault, a mark whose box has been squashed out of its
file's own ratio - which is what happens if a height is pinned without
`object-fit` to go with it.

THE SECOND MEASURE: CAN IT BE SEEN. A header on the brand-colour ground puts
the bar on `--color-primary`, and the logo file is the one the platform
serves - usually dark ink on nothing. On a saturated brand colour that mark is
there, the right size, and invisible. A pattern that offers a brand ground and
a `mark` axis is answering exactly this: the first rung is the file as it is,
and every rung after it is the pattern's answer for a mark that does not read
as it is - a plate in the page colour behind it, a white silhouette of it. So
for such a pattern this gate also renders the brand ground across every rung
of the mark axis, with a dark-ink mark and a light-ink mark, and reads the
result out of the browser: the mark's own painted pixels, drawn through
whatever filter the rung applies, against the colour of the nearest thing
painting a background behind it. WCAG's 3:1 for graphics is the bar, and:

    EVERY INK HAS AN ANSWER   for each ink, at least one rung reaches 3:1
    THE ANSWERS WORK          for the dark ink, every rung after the first
                              reaches 3:1 on its own - those rungs exist for
                              that mark, and one that leaves it under the bar
                              is a rung nobody should be offered

The as-it-is rung's ratio is printed for both inks whether or not it passes,
because that number is what tells a brand which rung to take.

    python ci/check_logo.py                  every pattern that carries a logo
    python ci/check_logo.py masthead-nav
    python ci/check_logo.py --broken         the positive control, below
    python ci/check_logo.py --tokens display
    python ci/check_logo.py --out /tmp/logo  keep the rendered pages
    python ci/check_logo.py --require-browser

THE POSITIVE CONTROL. `--broken` re-renders every page with rules appended
that put both defects back - `height: auto` under a `max-height` for the size,
and the plate's fill and the silhouette's filter removed for the contrast -
and requires BOTH checks to FIRE. A gate that has only ever run against code
that passes has not been shown to catch anything. Exit 0 on that run means
both defects were detected. The overrides are appended rather than spliced
into the stylesheet so that rewording the rules cannot quietly disarm them.

WHICH PATTERNS. Discovered, not listed: any pattern whose markup carries an
`<img>` on the `{{logo.src}}` furniture token is held to the size; any of
those that also declares a `brand` ground and a `mark` axis is held to the
contrast. Naming them here would leave the next pattern that carries a brand
mark outside this gate on the day it lands, which is the mistake the fold rule
made once already. A pattern whose `mark` axis has a `none` rung is rendered
on its first other rung for the size measure, since `none` draws nothing to
measure.

Exit codes: 0 clean, or skipped because no browser is available; 1 at least one
logo is not drawn as it should be, or cannot be seen; 2 the request itself is
unusable.
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
from check_page import apply_variants                   # noqa: E402
from check_phone import SHELL, browser_unavailable      # noqa: E402
import lint                                             # noqa: E402

# The widths straddle 60rem deliberately. The live defect was invisible above
# it and total below it, so a gate that sampled one side would have reported
# a clean library either way. 320 and 360 are the phone floor and the phone
# mode this repo already measures at; 768 and 900 are the tablet band where
# the small-screen rules still apply; 1024 and 1280 are the far side.
WIDTHS = (320, 360, 768, 900, 1024, 1280)
# Contrast does not change with width; the mark rules sit outside every media
# query. One phone width and one laptop width prove that.
CONTRAST_WIDTHS = (360, 1280)
# WCAG 1.4.11: a graphical object needs 3:1 against what it sits on.
CONTRAST_MIN = 3.0

# Two inks, and the gate knows each because it writes the file. The dark one
# is the ordinary brand mark - a logo exported as dark ink on nothing. The
# light one is the brand that ships a white or cream mark for exactly this
# ground, and it exists so the as-it-is rung is measured passing as well as
# failing: a gate that only ever sees the dark ink cannot tell a working rung
# from one that fails everything.
INKS = {
    "dark": "#7a2e3c",
    "light": "#f6f3ee",
}

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
               '<rect width="500" height="104" fill="%s"/></svg>' % INKS["dark"],
        "ratio": 500 / 104,
        "attrs": True,
        "why": "the ordinary brand wordmark: a viewBox and nothing else",
    },
    "wordmark-ratio-only-bare": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 104">'
               '<rect width="500" height="104" fill="%s"/></svg>' % INKS["dark"],
        "ratio": 500 / 104,
        "attrs": False,
        "why": "the same file with the img's width and height attributes "
               "dropped, which is what a hand-written page tends to do",
    },
    "square-ratio-only": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">'
               '<rect width="120" height="120" fill="%s"/></svg>' % INKS["dark"],
        "ratio": 1.0,
        "attrs": True,
        "why": "a square mark, where the width cap can never be what saves it",
    },
    "wordmark-sized": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 104" '
               'width="500" height="104">'
               '<rect width="500" height="104" fill="%s"/></svg>' % INKS["dark"],
        "ratio": 500 / 104,
        "attrs": True,
        "why": "the control: the same mark with intrinsic dimensions, the "
               "only shape this library measured before this gate",
    },
}


def ink_fixture(ink):
    """A ratio-only wordmark painted in one of the two inks, for contrast."""
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 104">'
            '<rect width="500" height="104" fill="%s"/></svg>' % INKS[ink])


# A box under this many pixels in either direction is a mark nobody can see.
# The defect renders exactly 0, so the threshold is not doing fine judgement -
# it is there so that a mark rendered at half a pixel reads as absent rather
# than as present and small.
DRAWN_PX = 4.0
# The pattern's height declaration is the height the mark is asked to render
# at. A tenth of a pixel is layout; a pixel is a rule not being applied.
HEIGHT_TOLERANCE_PX = 1.0
# The box may be letterboxed around the ink, which is what object-fit is for.
# What it may not be is stretched: a box whose own ratio has left the file's
# by more than this, with object-fit filling it, is a distorted logo.
RATIO_TOLERANCE = 0.02

LOGO_IMG = re.compile(
    r"<img\b[^>]*\bsrc\s*=\s*[\"']\{\{\s*logo\.src\s*\}\}[\"'][^>]*>", re.I)
CLASS_OF = re.compile(r"\bclass\s*=\s*[\"']([^\"']+)[\"']", re.I)
SIZE_ATTRS = re.compile(r"\s+(?:width|height)\s*=\s*[\"'][^\"']*[\"']", re.I)
DEFAULT_HEIGHT = "var(--logo-height, 2.75rem)"

# The height token is `2.75rem` or whatever the brand wrote, and reading the
# custom property gives that text rather than a length. A probe element
# carrying the same declaration the pattern carries - fallback, multiplier
# and all - is measured instead, so the number compared against is the number
# the browser actually resolved, on this page, at this width.
MEASURE = """
([selector, heightDeclaration]) => {
  const img = document.querySelector(selector);
  if (!img) return { missing: true };
  const round = n => Math.round(n * 10) / 10;
  const probe = document.createElement('div');
  probe.style.cssText =
    'position:absolute;left:-9999px;top:0;width:1px;' +
    'height:' + heightDeclaration + ';';
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

# The contrast measure. The ink is read from the painted pixels of the image
# drawn through its own computed filter, so a silhouette rung is measured as
# the silhouette and not as the file. The ground is the nearest ancestor that
# paints a background, resolved to sRGB through a canvas so an `oklch()` token
# and a `color-mix()` both come back as numbers. Nothing here is read off the
# stylesheet: a plate rule that has stopped applying reads as no plate.
CONTRAST = """
(selector) => {
  const img = document.querySelector(selector);
  if (!img) return { missing: true };
  const scratch = document.createElement('canvas');
  scratch.width = scratch.height = 1;
  const sctx = scratch.getContext('2d', { willReadFrequently: true });
  const toRGBA = css => {
    sctx.clearRect(0, 0, 1, 1);
    sctx.fillStyle = '#000';
    sctx.fillStyle = css;
    sctx.fillRect(0, 0, 1, 1);
    return Array.from(sctx.getImageData(0, 0, 1, 1).data);
  };
  let el = img.parentElement, ground = null, groundOn = null;
  while (el) {
    const bg = toRGBA(getComputedStyle(el).backgroundColor);
    if (bg[3] > 0) {
      ground = bg.slice(0, 3);
      groundOn = el.className ? String(el.className).split(' ')[0] : el.tagName;
      break;
    }
    el = el.parentElement;
  }
  if (!ground) return { noGround: true };
  const box = img.getBoundingClientRect();
  if (box.width < 1 || box.height < 1) return { notDrawn: true, ground, groundOn };
  const c = document.createElement('canvas');
  c.width = Math.max(1, Math.round(Math.min(box.width, 400)));
  c.height = Math.max(1, Math.round(c.width * box.height / box.width));
  const ctx = c.getContext('2d', { willReadFrequently: true });
  const filter = getComputedStyle(img).filter;
  if (filter && filter !== 'none') ctx.filter = filter;
  ctx.drawImage(img, 0, 0, c.width, c.height);
  let data;
  try { data = ctx.getImageData(0, 0, c.width, c.height).data; }
  catch (e) { return { tainted: String(e) }; }
  let r = 0, g = 0, b = 0, n = 0;
  for (let i = 0; i < data.length; i += 4) {
    if (data[i + 3] > 128) { r += data[i]; g += data[i + 1]; b += data[i + 2]; n++; }
  }
  if (!n) return { noInk: true, ground, groundOn };
  return {
    ink: [r / n, g / n, b / n], ground, groundOn,
    opacity: parseFloat(getComputedStyle(img).opacity), filter, painted: n,
  };
}
"""


def relative_luminance(rgb):
    def channel(v):
        v = v / 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(ink, ground):
    a, b = relative_luminance(ink), relative_luminance(ground)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


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


def pattern_meta(name):
    path = PATTERNS / name / "pattern.html"
    return lint.parse_header(path.read_text(encoding="utf-8"), path)


def axes_of(name):
    meta = pattern_meta(name)
    return lint.parse_variants(meta.get("variants", "")) or {}


def size_rung(name):
    """The rungs the size measure renders on: the markup as it ships, unless
    the mark axis has a `none` rung, which draws nothing to measure."""
    axes = axes_of(name)
    marks = list(axes.get("mark", ()))
    if "none" in marks:
        showing = [m for m in marks if m != "none"]
        return {"mark": showing[0]} if showing else {}
    return {}


def measures_contrast(name):
    """True where the pattern offers the brand ground and a mark axis: the
    two things that together make the contrast question answerable."""
    axes = axes_of(name)
    return "brand" in axes.get("ground", ()) and bool(axes.get("mark"))


def height_declaration(css, logo_class):
    """The pattern's own `height:` for its logo class, or the library default.

    Taken from the rule whose selector is exactly the logo class, so a
    compound selector that adjusts it in one state (a shrunk sticky bar, say)
    is not mistaken for the resting size."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    found = DEFAULT_HEIGHT
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        selectors = [s.strip() for s in match.group(1).split(",")]
        if f".{logo_class}" not in selectors:
            continue
        heights = re.findall(r"(?<![-\w])height\s*:\s*([^;]+)", match.group(2))
        if heights:
            found = heights[-1].strip()
    return found


def page(name, logo_file, attrs, width, tokens, mods=None, broken_class=None):
    """The pattern, with one fixture logo in it, in the bare preview shell."""
    folder = PATTERNS / name
    markup = re.sub(r"\s*<!--\n.*?\n-->", "",
                    (folder / "pattern.html").read_text(encoding="utf-8"),
                    count=1, flags=re.S)
    if mods:
        markup = apply_variants(name, pattern_meta(name), markup, mods)
    css = (folder / "pattern.css").read_text(encoding="utf-8")
    sample_path = folder / "preview-content.json"
    sample = (json.loads(sample_path.read_text(encoding="utf-8"))
              if sample_path.exists() else {})
    filled = fill(markup, sample)
    repeat = sample.get("_repeat")
    if repeat:
        filled = repeat_block(filled, repeat["class"], int(repeat["count"]))

    def swap(match):
        tag = match.group(0)
        if not attrs:
            tag = SIZE_ATTRS.sub("", tag)
        return tag
    # fill() has already put the sample logo's filename in place of the token,
    # so the swap is on the resolved src rather than on {{logo.src}}.
    filled = LOGO_IMG.sub(swap, filled)
    filled = filled.replace("sample-wordmark.svg", logo_file)

    if broken_class:
        # Both defects, reinstated. The size: two ceilings and no floor. The
        # contrast: every rung after the first stripped of whatever it paints
        # or filters, so the mark meets the brand ground as the file is.
        # Appended, never spliced, so that rewording the shipped rules cannot
        # disarm the control without anybody noticing.
        css += (f"\n.{broken_class} {{ height: auto; "
                f"max-height: var(--logo-height, 2.75rem); "
                f"object-fit: fill; }}\n")
        for rung in list(axes_of(name).get("mark", ()))[1:]:
            css += (f".{name}--{rung} * {{ background: transparent !important; "
                    f"filter: none !important; }}\n")
    return SHELL.format(name=f"{name}--{Path(logo_file).stem}", width=width,
                        tokens=tokens, css=css, markup=filled)


class Shell:
    """One browser and one asset directory, held open across every render.

    File access is allowed so that a logo loaded from the asset directory can
    be drawn to a canvas and read back; without it the canvas is tainted and
    the contrast measure cannot read a single pixel."""

    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            headless=True, args=["--allow-file-access-from-files"])
        self._dir = Path(tempfile.mkdtemp(prefix="lander-logo-"))
        for asset in PREVIEW.glob("*.svg"):
            shutil.copy(asset, self._dir / asset.name)
        for fixture, spec in FIXTURES.items():
            (self._dir / f"{fixture}.svg").write_text(spec["svg"],
                                                      encoding="utf-8")
        for ink in INKS:
            (self._dir / f"ink-{ink}.svg").write_text(ink_fixture(ink),
                                                      encoding="utf-8")
        return self

    def __exit__(self, *exc):
        self._browser.close()
        self._pw.stop()
        shutil.rmtree(self._dir, ignore_errors=True)
        return False

    def _open(self, html, width, stem):
        path = self._dir / f"{stem}-{width}.html"
        path.write_text(html, encoding="utf-8", newline="\n")
        tab = self._browser.new_page(viewport={"width": width, "height": 900},
                                     device_scale_factor=1)
        tab.goto(path.as_uri())
        return tab

    def measure(self, html, width, selector, height):
        tab = self._open(html, width, "logo")
        try:
            return tab.evaluate(MEASURE, [selector, height])
        finally:
            tab.close()

    def contrast(self, html, width, selector):
        tab = self._open(html, width, "contrast")
        try:
            tab.wait_for_function(
                "s => { const i = document.querySelector(s); "
                "return i && i.complete; }", arg=selector, timeout=5000)
            return tab.evaluate(CONTRAST, selector)
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
            f"{where}: the mark is {h}px tall where its height declaration "
            f"resolves to {wanted}px. The pattern reserves room for one and "
            f"draws the other")
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
    """The size measure: every fixture shape at every width."""
    faults, rows = [], []
    for name in names:
        logo_class = carries_a_logo(name)
        if logo_class == "":
            faults.append(f"{name}: its logo image carries no class, so no "
                          f"rule in this library can reach it and this gate "
                          f"cannot measure it")
            continue
        selector = f".{logo_class}"
        height = height_declaration(
            (PATTERNS / name / "pattern.css").read_text(encoding="utf-8"),
            logo_class)
        mods = size_rung(name)
        for fixture, spec in FIXTURES.items():
            for width in widths:
                html = page(name, f"{fixture}.svg", spec["attrs"], width,
                            tokens, mods, logo_class if broken else None)
                got = shell.measure(html, width, selector, height)
                rows.append((name, fixture, width, got))
                faults.extend(verdict(name, fixture, width, got))
    return faults, rows


def contrast_verdict(name, rungs, ratios):
    """Faults for one pattern's brand ground, from {(ink, rung): min ratio}."""
    faults = []
    as_is, answers = rungs[0], rungs[1:]
    for ink in INKS:
        reached = {r: ratios.get((ink, r)) for r in rungs}
        if any(v is None for v in reached.values()):
            continue                      # a render fault, reported already
        if not any(v >= CONTRAST_MIN for v in reached.values()):
            faults.append(
                f"{name} on the brand ground, {ink} mark: no rung of the mark "
                f"axis reaches {CONTRAST_MIN:.0f}:1 - "
                + ", ".join(f"{r} {v:.2f}:1" for r, v in reached.items())
                + ". A brand with this mark on this ground has no way to be "
                  "seen")
        if ink == "dark":
            for rung in answers:
                if reached[rung] < CONTRAST_MIN:
                    faults.append(
                        f"{name} on the brand ground, {ink} mark, {rung}: "
                        f"{reached[rung]:.2f}:1 where this rung exists to "
                        f"lift a {ink} mark off the brand colour; {as_is} "
                        f"reads {reached[as_is]:.2f}:1 on the same render")
    return faults


def contrast_sweep(shell, names, tokens, widths, broken=False):
    """The contrast measure: the brand ground across the mark axis, two inks."""
    faults, rows = [], []
    for name in names:
        if not measures_contrast(name):
            continue
        logo_class = carries_a_logo(name)
        if not logo_class:
            continue
        selector = f".{logo_class}"
        rungs = list(axes_of(name)["mark"])
        ratios = {}
        for ink in INKS:
            for rung in rungs:
                mods = {"ground": "brand", "mark": rung}
                for width in widths:
                    html = page(name, f"ink-{ink}.svg", True, width, tokens,
                                mods, logo_class if broken else None)
                    got = shell.contrast(html, width, selector)
                    where = f"{name} brand ground, {ink} mark, {rung} at {width}px"
                    if got.get("missing"):
                        faults.append(f"{where}: the logo image is not in "
                                      f"the rendered page at all")
                        continue
                    if got.get("tainted"):
                        faults.append(f"{where}: the canvas could not be read "
                                      f"({got['tainted']}), so the ink cannot "
                                      f"be measured - this gate needs the "
                                      f"browser launched with file access")
                        continue
                    if got.get("noGround"):
                        faults.append(f"{where}: nothing behind the mark "
                                      f"paints a background, so there is no "
                                      f"ground to measure against")
                        continue
                    if got.get("notDrawn") or got.get("noInk"):
                        faults.append(f"{where}: the mark paints no pixels, "
                                      f"so there is no ink to measure")
                        continue
                    ink_rgb = got["ink"]
                    alpha = got.get("opacity", 1.0)
                    if alpha < 1:
                        ink_rgb = [i * alpha + g * (1 - alpha)
                                   for i, g in zip(ink_rgb, got["ground"])]
                    ratio = contrast_ratio(ink_rgb, got["ground"])
                    rows.append((name, ink, rung, width, ratio, got["groundOn"],
                                 got["filter"]))
                    key = (ink, rung)
                    ratios[key] = min(ratios.get(key, ratio), ratio)
        faults.extend(contrast_verdict(name, rungs, ratios))
    return faults, rows


def main():
    ap = argparse.ArgumentParser(
        description="Render each pattern's brand mark as the shapes real "
                    "brands ship, check it is drawn at the size the pattern "
                    "reserved for it, and on the brand ground check it can "
                    "be seen. See the module docstring.")
    ap.add_argument("names", nargs="*", help="patterns to check (default: "
                                             "every pattern carrying a logo)")
    ap.add_argument("--tokens", default="brand",
                    help="sample token set to render against (default: brand)")
    ap.add_argument("--broken", action="store_true",
                    help="the positive control: reinstate both defects and "
                         "require this check to fire on each")
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
    with_contrast = [n for n in names if measures_contrast(n)]
    print(f"logo shapes: {len(names)} pattern(s), {len(FIXTURES)} logo "
          f"shape(s), {len(WIDTHS)} width(s), on the {args.tokens} tokens; "
          f"contrast on the brand ground for {len(with_contrast)} of them, "
          f"{len(INKS)} ink(s), {len(CONTRAST_WIDTHS)} width(s)"
          + ("  [control: both defects reinstated]" if args.broken else ""))
    print()

    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        for name in names:
            logo_class = carries_a_logo(name)
            broken = logo_class if args.broken else None
            for fixture, spec in FIXTURES.items():
                for width in WIDTHS:
                    (out / f"{name}--{fixture}--{width}.html").write_text(
                        page(name, f"{fixture}.svg", spec["attrs"], width,
                             tokens, size_rung(name), broken),
                        encoding="utf-8", newline="\n")
            if name in with_contrast:
                for ink in INKS:
                    for rung in axes_of(name)["mark"]:
                        for width in CONTRAST_WIDTHS:
                            (out / f"{name}--brand-{ink}-{rung}--{width}.html"
                             ).write_text(
                                page(name, f"ink-{ink}.svg", True, width,
                                     tokens, {"ground": "brand", "mark": rung},
                                     broken),
                                encoding="utf-8", newline="\n")

    with Shell() as shell:
        faults, rows = sweep(shell, names, tokens, WIDTHS, args.broken)
        seen_faults, seen_rows = contrast_sweep(shell, names, tokens,
                                               CONTRAST_WIDTHS, args.broken)

    # Every row, not only the failing ones. The number worth seeing before the
    # day it fails is the one that is nearly wrong.
    for name, fixture, width, got in rows:
        if got.get("missing"):
            continue
        print(f"  {name} {fixture} {width}px: {got['width']}x{got['height']}"
              f"  wanted {got['logoHeight']}  object-fit {got['fit']}")
    if seen_rows:
        print()
        for name, ink, rung, width, ratio, ground_on, filt in seen_rows:
            print(f"  {name} brand ground, {ink} mark, {rung} {width}px: "
                  f"{ratio:.2f}:1 on {ground_on}"
                  + (f"  filter {filt}" if filt and filt != "none" else ""))
    print()
    for line in faults + seen_faults:
        print(f"  FAIL  {line}")

    if args.broken:
        size_fired = bool(faults)
        seen_fired = bool(seen_faults) or not with_contrast
        if size_fired:
            print(f"  control: {len(faults)} size fault(s) caught with the "
                  f"logo rule as the defect had it. The size check fires.")
        else:
            print("  CONTROL FAILED: every brand mark drew correctly with the "
                  "logo rule set the way the defect had it. This gate cannot "
                  "see the thing it exists for.")
        if not with_contrast:
            print("  control: no pattern offers the brand ground with a mark "
                  "axis, so there is no contrast control to run")
        elif seen_faults:
            print(f"  control: {len(seen_faults)} contrast fault(s) caught "
                  f"with the plate and the silhouette disarmed. The contrast "
                  f"check fires.")
        else:
            print("  CONTROL FAILED: every mark read on the brand ground with "
                  "the plate and the silhouette disarmed. The contrast check "
                  "cannot see the thing it exists for.")
        return 0 if (size_fired and seen_fired) else 1

    if not faults and not seen_faults:
        print(f"  clean: every brand mark drawn at its declared height, "
              f"{len(rows)} render(s)"
              + (f"; every mark answered on the brand ground, "
                 f"{len(seen_rows)} render(s)" if seen_rows else ""))
    if args.out:
        print(f"\n  pages written to {args.out}")
    return 1 if (faults or seen_faults) else 0


if __name__ == "__main__":
    raise SystemExit(main())
