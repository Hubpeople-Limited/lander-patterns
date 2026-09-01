#!/usr/bin/env python3
"""Render every pattern at phone widths and measure what came out.

Every other gate in this repo reasons about a file: the metadata header, the
CSS text, the token census, a contrast ratio computed from two hex values.
`ci/check_page.py` widened that to a page, but it still reads source - it
knows `min-height: 100svh` is there, not what 100svh turned out to be.

Nothing had ever laid a pattern out and looked at the result, and the defects
that reached live sites are all of that kind: a header logo painting over the
first menu link, a wordmark pushing a menu button onto a second row, an
opener putting its join control below the fold. Each passed every gate. Each
was found by opening a browser.

Most of the traffic is phones, so that is the width this measures.

    python ci/check_phone.py                     every pattern, 320 and 360
    python ci/check_phone.py hero-split faq-details
    python ci/check_phone.py --width 320
    python ci/check_phone.py --out /tmp/phone    keep the rendered pages
    python ci/check_phone.py --advisory          report, never fail the build

Exit codes: 0 clean, or skipped because no browser is available; 1 at least
one pattern has a fault; 2 the request itself is unusable.

WHAT IT DOES NOT CHECK, on purpose, is in CONTRIBUTING.md next to what it
does. The short version: a rule that cannot be made reliable is worse than no
rule, because the first false positive teaches everyone to stop reading the
output - and this repo has already learnt that lesson once.
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

from build_preview import fill, repeat_block  # noqa: E402

# 320 is the floor: the narrowest viewport still in real use, and the width
# every "mobile-first" claim is implicitly making. Anything that overflows
# does it here first.
#
# 360 is the mode. It is the single most common width in the traffic these
# pages serve, so a fault at 360 is a fault most visitors would meet, and one
# that is clean at 320 but broken at 360 is a real thing - a grid whose
# breakpoint lands between the two.
#
# 390 and 414 were tried and found nothing that 360 did not, while costing a
# third more runtime. Add a width when a defect turns up that needs it, not
# before.
WIDTHS = (320, 360)

# 44 CSS pixels in the smaller dimension. It is the figure Apple's guidance
# and WCAG's AAA target-size rule both land on, and it is what a thumb
# actually needs. WCAG 2.2's AA floor is 24, which is low enough to pass
# controls nobody can reliably hit.
TAP_MIN = 44

# Below this, body text on a phone is not being read, it is being squinted
# at. Deliberately well under the 16px norm: the job is to catch a mistake,
# not to have an opinion about small print.
TEXT_MIN = 12

# iOS zooms the whole page when a form field under 16px takes focus, which
# throws the layout out and is not recoverable by pinching back. A hard,
# objective number with no taste in it.
FIELD_MIN = 16

# A pattern whose whole job is a horizontal rail. Its track is MEANT to be
# wider than the viewport - that is the affordance - so the document-overflow
# rule cannot apply to it. Named here rather than inferred, so that adding a
# pattern to this list is a decision somebody made in a diff.
#
# Empty today: every rail in the library carries its own overflow-x, which is
# the right way to do it and means the general rule already leaves it alone.
# The list exists so the next rail that does not has somewhere to be argued
# about.
OVERFLOW_EXEMPT = set()

# What the library is known to do today, and why it is not failing the build
# over it. Each entry is (pattern, a phrase from the fault, the reason).
#
# This is a baseline, not an amnesty. A fault that matches one of these is
# reported as KNOWN and does not fail; anything else is new and does fail. So
# the gate protects against regression from the day it lands, without
# demanding four design decisions be taken in the same hour it was written -
# and every one of them stays visible in the output rather than being
# quietly excluded.
#
# Delete an entry when the pattern is fixed. If the fault has gone and the
# entry has not, the run says so: a stale baseline is how a gate goes quiet.
ACCEPTED = [
    ("listing-rows", "listing-rows-link",
     "min-block-size: 1.5rem, chosen deliberately - the CSS says so in a "
     "comment. 24px is WCAG 2.2 AA; 44px is the AAA figure this gate uses"),
    ("trust-row", "trust-row-membership-status",
     "font-size: 0.6875rem on a chip label, and it does not carry "
     "--type-scale, so a brand that dials type up does not rescue it"),
]

SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name} at {width}px</title>
<style>
{tokens}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: var(--font-body); background: var(--color-bg);
       color: var(--color-text); line-height: 1.6; }}
{css}
</style>
</head>
<body>
{markup}
</body>
</html>
"""

# The measurement. One pass in the page, returning observations rather than
# verdicts - what is a fault is decided in Python, where it can be read.
MEASURE = r"""
() => {
  const W = document.documentElement.clientWidth;
  const TAP = %TAP%, TEXT = %TEXT%, FIELD = %FIELD%;
  const out = { width: W, docScroll: document.documentElement.scrollWidth,
                overflow: [], taps: [], small: [], fields: [] };

  const style = el => getComputedStyle(el);

  const shown = el => {
    const s = style(el);
    if (s.display === 'none' || s.visibility === 'hidden') return false;
    if (parseFloat(s.opacity) === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0.5 && r.height > 0.5;
  };

  // Anything inside a scroller or a clip is contained by design. A carousel
  // track IS wider than the screen; a cover-cropped image IS bigger than its
  // frame. Neither reaches the document scroll width, and neither is a fault.
  const contained = el => {
    for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) {
      const o = style(p);
      if (/hidden|auto|scroll|clip/.test(o.overflowX)) return true;
      if (/hidden|auto|scroll|clip/.test(o.overflow)) return true;
    }
    return false;
  };

  const describe = el => {
    const cls = (el.getAttribute('class') || '').trim().split(/\s+/)
                  .filter(Boolean).slice(0, 2).join('.');
    const text = (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 40);
    return el.tagName.toLowerCase() + (cls ? '.' + cls : '')
           + (text ? ' "' + text + '"' : '');
  };

  const all = [...document.body.querySelectorAll('*')];

  // ---- horizontal overflow -------------------------------------------
  // Only named when the DOCUMENT itself overflows. An element sticking out
  // of a box that clips it is not something a visitor can see or scroll to,
  // and reporting it is how this check would start crying wolf.
  if (out.docScroll > W + 1) {
    const over = all.filter(el => {
      if (!shown(el) || contained(el)) return false;
      const r = el.getBoundingClientRect();
      return r.right > W + 1 || r.left < -1;
    });
    // Deepest offenders only: naming the <h1> that holds the long word is
    // actionable, naming its four ancestors as well is noise.
    const deepest = over.filter(el => !over.some(o => o !== el && el.contains(o)));
    out.overflow = deepest.slice(0, 4).map(el => {
      const r = el.getBoundingClientRect();
      return { what: describe(el), right: Math.round(r.right),
               left: Math.round(r.left) };
    });
    // A long unbreakable word bursts its box without moving it: the <div> is
    // still 320 wide, so no rect is out of bounds and the loop above names
    // nothing while the document plainly scrolls. Fall back to the box the
    // text is bursting OUT of. Only ever used to name a culprit on a document
    // that has already failed, so it cannot add a false positive of its own.
    if (!out.overflow.length) {
      const burst = all.filter(el => shown(el) && !contained(el)
        && style(el).overflowX === 'visible'
        && el.scrollWidth > el.clientWidth + 1 && el.clientWidth > 0);
      out.overflow = burst
        .filter(el => !burst.some(o => o !== el && el.contains(o)))
        .slice(0, 4)
        .map(el => ({ what: describe(el), right: el.scrollWidth, left: 0 }));
    }
  }

  // ---- tap targets -----------------------------------------------------
  const labelled = el => {
    const labels = [];
    if (el.id) document.querySelectorAll('label[for="' + CSS.escape(el.id) + '"]')
                       .forEach(l => labels.push(l));
    const wrap = el.closest('label');
    if (wrap) labels.push(wrap);
    return labels.some(l => {
      const r = l.getBoundingClientRect();
      return Math.min(r.width, r.height) >= TAP - 0.5;
    });
  };

  // A link that is TEXT is not a control, and holding it to 44px means
  // double-spacing prose. WCAG carves the same exception out for the same
  // reason. `display: inline` is the obvious form of it, but it is not
  // enough on its own: a link in a grid or flex parent is blockified, so a
  // row title and a caption's source link both compute as `block` while
  // still being nothing but words. The test that survives both is whether
  // the author gave it a BOX - padding, a min-height, a border, a fill.
  // Something with a box was drawn as a control and should be hittable as
  // one; something without is a run of text.
  //
  // Only `<a>`. A `<button>` or a `<summary>` is a control whatever it is
  // wearing. An `<a>` wrapping an image is one too - a logo is tapped, not
  // read - so the carve-out is for text content only.
  const textLink = el => {
    if (el.tagName !== 'A') return false;
    if (el.querySelector('img, svg, picture, video')) return false;
    const s = style(el);
    if (s.display === 'inline') return true;
    const pad = parseFloat(s.paddingTop) + parseFloat(s.paddingBottom);
    const filled = s.backgroundImage !== 'none'
      || !/^rgba\(0, 0, 0, 0\)$|^transparent$/.test(s.backgroundColor);
    return !(pad > 4 || parseFloat(s.minHeight) > 0 || filled
             || parseFloat(s.borderTopWidth) > 0
             || parseFloat(s.borderBottomWidth) > 0);
  };

  const controls = [...document.body.querySelectorAll(
    'a[href], button, summary, input:not([type="hidden"]), select, textarea')];
  for (const el of controls) {
    if (!shown(el)) continue;
    if (textLink(el)) continue;
    // A 16px checkbox with a 48px label is a 48px target, because the label
    // activates it.
    if (labelled(el)) continue;
    const r = el.getBoundingClientRect();
    const min = Math.min(r.width, r.height);
    if (min < TAP - 0.5) {
      out.taps.push({ what: describe(el), w: Math.round(r.width),
                      h: Math.round(r.height) });
    }
  }

  // ---- text that has become unreadable ---------------------------------
  const hasOwnWords = el => [...el.childNodes].some(
    n => n.nodeType === 3 && n.textContent.trim().length > 1);
  for (const el of all) {
    if (!hasOwnWords(el) || !shown(el)) continue;
    if (/^(SUP|SUB)$/.test(el.tagName)) continue;   // small by definition
    const size = parseFloat(style(el).fontSize);
    if (size < TEXT - 0.01) {
      out.small.push({ what: describe(el), size: Math.round(size * 10) / 10 });
    }
  }

  // ---- form fields iOS will zoom into ----------------------------------
  for (const el of document.body.querySelectorAll('input:not([type="hidden"]), select, textarea')) {
    if (!shown(el)) continue;
    if (/^(checkbox|radio|submit|button|range|color|file)$/.test(el.type || '')) continue;
    const size = parseFloat(style(el).fontSize);
    if (size < FIELD - 0.01) {
      out.fields.push({ what: describe(el), size: Math.round(size * 10) / 10 });
    }
  }

  return out;
}
""".replace("%TAP%", str(TAP_MIN)).replace("%TEXT%", str(TEXT_MIN)) \
   .replace("%FIELD%", str(FIELD_MIN))


# ------------------------------------------------------------ availability

def browser_unavailable():
    """Why a browser cannot be driven here, or None if one can.

    Returns a sentence rather than a boolean, because the whole point of the
    skip path is that whoever hits it is told what to install. A gate that
    goes quiet without saying why is the false assurance this repo's test
    suite exists to prevent.
    """
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        return ("the playwright package is not installed "
                "(pip install playwright && playwright install chromium)")
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as p:
            path = Path(p.chromium.executable_path)
    except Exception as exc:                      # pragma: no cover - env
        return f"playwright could not start ({exc.__class__.__name__})"
    if not path.exists():
        return (f"no chromium at {path} "
                f"(run: playwright install chromium)")
    return None


# ------------------------------------------------------------- the render

def pattern_page(name, width, tokens):
    """The pattern, filled with its sample content, in a bare page.

    The same shell `ci/build_preview.py` writes, minus two things that would
    corrupt the measurement: the 0.8rem preview note, which is text under the
    legibility floor and is not the pattern's, and hub.js. A pattern's markup
    is required to work with no script on the page, so with no script on the
    page is what gets measured.
    """
    folder = PATTERNS / name
    markup = (folder / "pattern.html").read_text(encoding="utf-8")
    markup = re.sub(r"\s*<!--\n.*?\n-->", "", markup, count=1, flags=re.S)
    css = (folder / "pattern.css").read_text(encoding="utf-8")
    sample_path = folder / "preview-content.json"
    sample = json.loads(sample_path.read_text(encoding="utf-8")) if sample_path.exists() else {}
    filled = fill(markup, sample)
    repeat = sample.get("_repeat")
    if repeat:
        filled = repeat_block(filled, repeat["class"], int(repeat["count"]))
    return SHELL.format(name=name, width=width, tokens=tokens, css=css,
                        markup=filled)


class Phone:
    """One browser, held open across every pattern.

    Launching Chromium costs about six tenths of a second and measuring a
    page costs about a hundredth. Launching per pattern would therefore be
    fifty times the cost of the thing being measured, which is how a gate
    ends up too slow to run and then not run.
    """

    def __init__(self, widths=WIDTHS):
        self.widths = widths
        self._pw = None
        self._browser = None
        self._dir = None

    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=True)
        # A real directory, so the sample SVGs resolve as they would on a
        # page. set_content() has no base URL and every image would 404 -
        # a broken image has different dimensions from the real one, so the
        # overflow numbers would be measuring the wrong document.
        self._dir = Path(tempfile.mkdtemp(prefix="lander-phone-"))
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

    def measure(self, html, width):
        page = self._dir / f"m-{width}.html"
        page.write_text(html, encoding="utf-8", newline="\n")
        tab = self._browser.new_page(viewport={"width": width, "height": 760},
                                     device_scale_factor=1)
        try:
            tab.goto(page.as_uri())
            return tab.evaluate(MEASURE)
        finally:
            tab.close()

    def faults(self, name, html, exempt_overflow=False):
        """Every fault for one document, as sentences, folded by width.

        Two foldings, and both matter for the same reason - the run whose
        output most needs to be readable is the first one that fails.

        A row pattern ships seven identical rows, so one undersized link is
        seven identical sentences: they fold into one with a count. And a
        fault usually appears at every width, so it is reported once naming
        the widths rather than once per width.
        """
        seen = {}
        for width in self.widths:
            got = self.measure(html, width)
            tally = {}
            for line in self._verdict(name, got, exempt_overflow):
                tally[line] = tally.get(line, 0) + 1
            for line, count in tally.items():
                seen.setdefault(line, {})[width] = count
        out = []
        for line, widths in seen.items():
            where = ", ".join(
                f"{w}px" + (f" (x{n})" if n > 1 else "")
                for w, n in sorted(widths.items()))
            out.append(f"{line} [at {where}]")
        return out

    @staticmethod
    def _verdict(name, got, exempt_overflow):
        bad = []
        w = got["width"]

        def say(text):
            """Element descriptions carry the pattern's own sample text, and
            a Windows console is cp1252. One arrow in a sample string is
            enough to end the run in a UnicodeEncodeError from print(), which
            reads as the gate crashing rather than as a pattern being fine."""
            return text.encode("ascii", "replace").decode("ascii")

        if not exempt_overflow and got["docScroll"] > w + 1:
            culprits = ", ".join(
                f"{say(c['what'])} reaches {c['right']}px"
                for c in got["overflow"])
            bad.append(
                f"{name}: the page scrolls sideways - {got['docScroll']}px of "
                f"content in a {w}px viewport"
                + (f" ({culprits})" if culprits else ""))
        for t in got["taps"]:
            bad.append(f"{name}: tap target {say(t['what'])} is "
                       f"{t['w']}x{t['h']}px, under {TAP_MIN}px")
        for s in got["small"]:
            bad.append(f"{name}: text {say(s['what'])} renders at {s['size']}px, "
                       f"under {TEXT_MIN}px")
        for f in got["fields"]:
            bad.append(f"{name}: form field {say(f['what'])} is {f['size']}px - "
                       f"iOS zooms the page when a field under {FIELD_MIN}px "
                       f"takes focus")
        return bad


# ---------------------------------------------------------------- the sweep

# The token set every measurement in ACCEPTED was taken on. It matters
# because those entries carry PIXEL SIZES, and a pixel size is a size in a
# particular typeface: masthead-nav's login link is 40px tall on a brand
# whose heading face is Georgia and clears 44px on preview/tokens-display.css,
# whose line box is 57% taller. So a run on any other set cannot say an entry
# matched nothing - the fault is not gone, it is a different size - and
# reporting it as stale sends somebody to delete a live baseline entry.
BASELINE_TOKENS = "brand"


def token_set(which=BASELINE_TOKENS):
    return (PREVIEW / f"tokens-{which}.css").read_text(encoding="utf-8")


def accepted_for(name, line):
    """The baseline entry this fault matches, or None if it is new."""
    for pattern, needle, why in ACCEPTED:
        if pattern == name and needle in line:
            return why
    return None


def sweep(widths=WIDTHS, tokens_name=BASELINE_TOKENS, names=None):
    """Every pattern, measured. Returns (new, known, stale).

    `new` fails a build, `known` is the baseline above, and `stale` names
    baseline entries that matched nothing - which means either the pattern
    was fixed and the entry should go, or the fault moved and the entry is
    now hiding a live defect. Either way it needs a person, so it is
    reported rather than ignored.
    """
    tokens = token_set(tokens_name)
    names = names or sorted(f.name for f in PATTERNS.iterdir() if f.is_dir())
    new, known, matched = [], [], set()
    with Phone(widths) as phone:
        for name in names:
            html = pattern_page(name, widths[0], tokens)
            for line in phone.faults(name, html, name in OVERFLOW_EXEMPT):
                why = accepted_for(name, line)
                if why:
                    known.append((line, why))
                    matched.add((name, why))
                else:
                    new.append(line)
    # Only a run over the whole library ON THE BASELINE TOKEN SET can say an
    # entry matched nothing. A run over three named patterns would call every
    # other entry stale, and a run on another sample brand would call stale
    # every entry whose fault the other brand's type metrics happen to lift
    # over the threshold - which is a live baseline entry being deleted for
    # the wrong reason. See BASELINE_TOKENS.
    full = (names == sorted(f.name for f in PATTERNS.iterdir() if f.is_dir())
            and tokens_name == BASELINE_TOKENS)
    stale = ([f"{p}: {w}" for p, n, w in ACCEPTED if (p, w) not in matched]
             if full else [])
    return new, known, stale


def main():
    ap = argparse.ArgumentParser(
        description="Render patterns at phone widths and measure the result.")
    ap.add_argument("patterns", nargs="*",
                    help="pattern names; default every pattern in the library")
    ap.add_argument("--width", type=int, action="append",
                    help="a viewport width; repeatable. Default 320 and 360")
    ap.add_argument("--tokens", default="brand",
                    help="which preview token set to render on (default brand)")
    ap.add_argument("--out", help="directory to keep the rendered pages in")
    ap.add_argument("--advisory", action="store_true",
                    help="report faults but exit 0")
    ap.add_argument("--strict", action="store_true",
                    help="also fail on the accepted baseline, not just new faults")
    ap.add_argument("--require-browser", action="store_true",
                    help="treat a missing browser as a failure, not a skip")
    args = ap.parse_args()

    why = browser_unavailable()
    if why:
        print(f"phone widths: SKIPPED - {why}")
        print("  Nothing was measured. This is not a pass.")
        # A skip is the right answer for a contributor who cannot install a
        # browser, and the wrong one for CI, where a silent skip is a green
        # build that measured nothing. Which of the two this is cannot be
        # inferred here, so it is passed in.
        return 1 if args.require_browser else 0

    widths = tuple(args.width) if args.width else WIDTHS
    names = args.patterns or sorted(
        f.name for f in PATTERNS.iterdir() if f.is_dir())
    for name in names:
        if not (PATTERNS / name / "pattern.html").exists():
            print(f"phone widths: no pattern called {name!r} in patterns/")
            return 2

    try:
        tokens = token_set(args.tokens)
    except FileNotFoundError:
        print(f"phone widths: no preview token set called {args.tokens!r}")
        return 2

    out_dir = Path(args.out) if args.out else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    print(f"phone widths: {len(names)} pattern(s) at "
          f"{', '.join(str(w) for w in widths)}px on the {args.tokens} tokens\n")

    if out_dir:
        for name in names:
            for width in widths:
                (out_dir / f"{name}--{width}.html").write_text(
                    pattern_page(name, width, tokens),
                    encoding="utf-8", newline="\n")

    new, known, stale = sweep(widths, args.tokens, names)

    for line in new:
        print(f"  FAIL  {line}")
    for line, why in known:
        print(f"  known {line}")
        print(f"        accepted: {why}")
    for line in stale:
        print(f"  STALE baseline entry matched nothing - {line}")
    if args.tokens != BASELINE_TOKENS:
        print(f"  note: the accepted baseline was measured on the "
              f"{BASELINE_TOKENS} tokens, so stale detection is off on this "
              f"run. A pixel size is a size in a particular typeface")

    if not new and not known:
        print(f"  clean: {len(names)} pattern(s), nothing overflows, no target "
              f"under {TAP_MIN}px, no text under {TEXT_MIN}px")
    elif not new:
        print(f"\n  {len(known)} known fault(s), 0 new, across "
              f"{len(names)} pattern(s)")
    else:
        print(f"\n  {len(new)} new fault(s) and {len(known)} known, across "
              f"{len(names)} pattern(s)")

    if out_dir:
        print(f"\n  pages written to {out_dir} - open one at a phone width")

    if args.strict and known:
        return 1
    if args.advisory:
        if new:
            print("  advisory run: not failing the build")
        return 0
    return 1 if (new or stale) else 0


if __name__ == "__main__":
    raise SystemExit(main())
