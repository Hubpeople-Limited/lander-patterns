#!/usr/bin/env python3
"""Render masthead-nav across every combination of its axes and look at it.

Five axes multiply out to seventy-two headers, and each has a shut state, an
open one and a scrolled one at every width. Nobody reasons about that many
combinations; this renders all of them, measures the things that decide whether
the header works, and writes a PNG of each so the rest can be judged by eye.

    python dev/render_matrix.py                       everything
    python dev/render_matrix.py --only menu=drawer    one rung of one axis
    python dev/render_matrix.py --widths 320          one width
    python dev/render_matrix.py --no-shots            measure only

Exit codes: 0 every combination clean, 1 at least one fault, 2 no browser.

The measurements are taken in the browser rather than read off source:

  reachable   with the drawer open, the point at the centre of the join
              control is hit-tested. Whatever elementFromPoint returns has to
              be the join control or something inside it. A control behind a
              scrim fails this and looks perfectly fine in a screenshot.
  clear       the header's foot against the top of the section under it. A
              header that paints over the page below it is a header whose
              own box does not account for what it draws.
  targets     44px on every control, at 320 only. ci/check_phone.py measures
              this properly, but only on the pattern as shipped - which is
              one of the seventy-two, with its drawer shut. Every rung of
              every axis is unmeasured there and measured here.
  pinned      scrolled 600px: a sticky bar has to still be at the top of the
              viewport with its controls reachable, and one that is not sticky
              has to have gone. The scrolled state asserts the page moved
              before it believes either - a page that did not scroll reports
              that every bar pins.

Two things about how it drives the browser, both of which cost a wrong
answer before they were written down:

  Open the drawer by ATTRIBUTE, never by the `open` IDL property. Setting the
  property defers the style recalc past a short wait, so a measurement taken
  straight after it reports a drawer that is still shut.

  Render under REDUCED MOTION. The panel slides for --transition-fast, and a
  measurement taken while it is still sliding reports it off the side of the
  screen. Waiting longer than the transition is a race, and a race in a check
  is a check that is sometimes wrong in the direction of passing. The
  pattern's own reduced-motion block sets `transition: none` on these rules,
  so this measures the end state by the pattern's own code path.
"""
import argparse
import base64
import itertools
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ci"))

from build_preview import fill  # noqa: E402
from check_phone import ACCEPTED  # noqa: E402
from check_page import apply_variants  # noqa: E402
import lint  # noqa: E402

# The library's own baseline, imported rather than restated. A fault this
# repository has already looked at and written a reason for is `known` here for
# the same reason it is known there - and deleting the entry there starts the
# reporting again here, which is what keeps the two from drifting.
KNOWN = {phrase for pattern, phrase, _why in ACCEPTED if pattern == "masthead-nav"}

PATTERN = ROOT / "patterns" / "masthead-nav"
PREVIEW = ROOT / "preview"
META = lint.parse_header(
    (PATTERN / "pattern.html").read_text(encoding="utf-8"), PATTERN / "pattern.html")

AXES = {
    "ground": ["plain", "soft", "brand"],
    "layout": ["inline", "centred"],
    "menu": ["drawer", "panel", "row"],
    "sticky": ["static", "pinned"],
    "menu-align": ["menu-start", "menu-centre", "menu-end"],
    "menu-side": ["side-start", "side-end"],
}

# The axes that can move a box. Screenshots are taken only where these differ,
# because a picture of the same layout on a different ground is a picture
# nobody needs to look at - and at seven axes the full cross-product is 3888
# renders. Every combination is still MEASURED; only the photography is
# sampled, so no rule is checked less thoroughly than before.
POSITIONAL = ("menu", "menu-align", "menu-side", "layout", "sticky")

WIDTHS = (320, 768, 1280)
HEIGHT = 720

# How far down the `scrolled` state scrolls. Anything past the header's own
# height does the job; 600 is comfortably past the tallest of them.
SCROLL_TO = 600

# Enough copy under the header that the page actually scrolls at 720 tall. The
# first version of this shell carried six paragraphs, which is not enough - the
# scrolled state then measured a page sitting at the top and reported that a
# header pins when nothing had moved.
FILLER = "  <p>More sample copy, so the page is tall enough to scroll.</p>\n" * 40

SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
{tokens}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: var(--font-body); background: var(--color-bg);
       color: var(--color-text); line-height: 1.6; }}
.matrix-under {{ padding: 24px 16px; background: var(--color-surface-soft); }}
.matrix-under h1 {{ margin: 0 0 12px; font-size: 1.5rem; }}
.matrix-under p {{ margin: 0 0 12px; }}
{css}
</style>
</head>
<body>
{markup}
<section class="matrix-under">
  <h1>The section under the header</h1>
  <p>Sample body copy, here so the header has something to run into.</p>
{filler}
</section>
</body>
</html>
"""

MEASURE = r"""
() => {
  const round = n => Math.round(n * 10) / 10;
  const join = document.querySelector('.masthead-nav-join');
  const login = document.querySelector('.masthead-nav-login');
  const header = document.querySelector('.masthead-nav');
  const under = document.querySelector('.matrix-under');
  const disclosure = document.querySelector('.masthead-nav-disclosure');

  const hit = el => {
    if (!el) return {present: false};
    const b = el.getBoundingClientRect();
    const x = b.left + b.width / 2, y = b.top + b.height / 2;
    const inView = b.width > 0 && b.height > 0
      && x >= 0 && y >= 0 && x < innerWidth && y < innerHeight;
    const top = inView ? document.elementFromPoint(x, y) : null;
    return {
      present: true,
      w: round(b.width), h: round(b.height),
      x: round(b.left), y: round(b.top),
      visible: el.checkVisibility({checkOpacity: true, checkVisibilityCSS: true}),
      inView: inView,
      onTop: !!top && (top === el || el.contains(top)),
      blockedBy: top && !(top === el || el.contains(top))
        ? (top.className || top.tagName) : null
    };
  };

  // The same carve-outs ci/check_phone.py makes, so a report here means the
  // same thing a report there does: a link that is only words is not a
  // control, and an <a> around an image always is.
  const textLink = el => {
    if (el.tagName !== 'A') return false;
    if (el.querySelector('img, svg, picture, video')) return false;
    const s = getComputedStyle(el);
    if (s.display === 'inline') return true;
    const pad = parseFloat(s.paddingTop) + parseFloat(s.paddingBottom);
    const filled = s.backgroundImage !== 'none'
      || !/^rgba\(0, 0, 0, 0\)$|^transparent$/.test(s.backgroundColor);
    return !(pad > 4 || parseFloat(s.minHeight) > 0 || filled
             || parseFloat(s.borderTopWidth) > 0
             || parseFloat(s.borderBottomWidth) > 0);
  };
  const small = [];
  for (const el of header.querySelectorAll('a[href], button, summary')) {
    const s = getComputedStyle(el);
    if (s.display === 'none' || s.visibility === 'hidden') continue;
    if (parseFloat(s.opacity) === 0) continue;
    const b = el.getBoundingClientRect();
    if (b.width < 0.5 || b.height < 0.5) continue;
    if (textLink(el)) continue;
    if (Math.min(b.width, b.height) < 43.5) {
      small.push(((el.getAttribute('class') || el.tagName).split(/\s+/)[0])
                 + ' ' + round(b.width) + 'x' + round(b.height));
    }
  }

  const hb = header.getBoundingClientRect();
  const ub = under.getBoundingClientRect();
  return {
    small: small,
    join: hit(join),
    login: hit(login),
    joinInsideDisclosure: !!(join && disclosure && disclosure.contains(join)),
    loginInsideDisclosure: !!(login && disclosure && disclosure.contains(login)),
    headerBottom: round(hb.bottom),
    underTop: round(ub.top),
    headerHeight: round(hb.height),
    headerTop: round(hb.top),
    toggleOnScreen: (() => {
      const s = document.querySelector('.masthead-nav-toggle');
      if (!s || getComputedStyle(s).display === 'none') return true;
      const b = s.getBoundingClientRect();
      if (b.bottom <= 0 || b.top >= innerHeight) return false;
      const el = document.elementFromPoint(b.left + b.width / 2,
                                           b.top + b.height / 2);
      return !!el && (el === s || s.contains(el));
    })(),
    scrollY: Math.round(scrollY),
    scrollable: document.documentElement.scrollHeight > innerHeight,
    docScrollWidth: document.documentElement.scrollWidth,
    viewport: innerWidth
  };
}
"""


def markup_for(combo):
    html = (PATTERN / "pattern.html").read_text(encoding="utf-8")
    sample = json.loads((PATTERN / "preview-content.json").read_text(encoding="utf-8"))
    html = fill(html, sample)
    # Both comments, not just the metadata header: the placement notes carry
    # the axis names and would sit in every screenshot.
    html = re.sub(r"<!--(?!\s*slot\s*:).*?-->", "", html, flags=re.S).strip()
    # The library's own applier, not a class map of our own. ci/compose.py,
    # ci/check_page.py and the two browser tools on the help site all reach a
    # rung this way, so rendering it any other way would render something
    # nobody can actually ask for - and would be blind to a rung that silently
    # does nothing, which is the one fault a bespoke map cannot have.
    html = apply_variants("masthead-nav", META, html, combo)
    got = re.search(r'<header class="([^"]+)"', html).group(1).split()
    missing = [v for v in combo.values() if "masthead-nav--" + v not in got]
    if missing:
        raise SystemExit(
            "apply_variants did nothing for %s - the rung is declared in "
            "`variants:` but its modifier is not spelled "
            ".masthead-nav--<value>, so asking for it returns the default:\n  %s"
            % (", ".join(missing), " ".join(got)))
    # A data URI, not a file: URL. set_content serves the page from about:blank
    # and the browser refuses a file: image to it, so the mark rendered as
    # broken-image alt text - narrower and shorter than the wordmark, in a
    # header whose whole small-screen layout is a width cap on that element.
    svg = (PREVIEW / "sample-wordmark.svg").read_bytes()
    html = html.replace(
        'src="sample-wordmark.svg"',
        'src="data:image/svg+xml;base64,%s"' % base64.b64encode(svg).decode())
    return html


def shot_worthy(combo):
    """One photograph per distinct positional arrangement, on one ground.

    Ground is the only axis sampled out, because it is the only one that
    cannot move a box. `sticky` was sampled out once and should not have been:
    it compacts the bar's padding, so it changes shape and has to be seen.
    Every combination is still MEASURED whatever this returns.
    """
    return combo.get("ground", "plain") == "plain"


def label(combo):
    return "-".join(combo[a] for a in AXES if a in combo)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "dev" / "matrix"))
    ap.add_argument("--widths", type=int, nargs="*", default=list(WIDTHS))
    ap.add_argument("--only", nargs="*", default=[],
                    help="axis=value, repeatable, to narrow the matrix")
    ap.add_argument("--tokens", default="brand")
    ap.add_argument("--no-shots", action="store_true")
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("no browser: pip install playwright && playwright install chromium")
        return 2

    axes = {a: list(v) for a, v in AXES.items()}
    for clause in args.only:
        axis, _, value = clause.partition("=")
        if axis not in axes or value not in axes[axis]:
            print("unknown filter %r" % clause)
            return 2
        axes[axis] = [value]

    tokens = (PREVIEW / ("tokens-%s.css" % args.tokens)).read_text(encoding="utf-8")
    css = (PATTERN / "pattern.css").read_text(encoding="utf-8")
    out = Path(args.out)
    if not args.no_shots:
        out.mkdir(parents=True, exist_ok=True)

    combos = [dict(zip(axes, values)) for values in itertools.product(*axes.values())]
    faults, rendered, known = [], 0, 0

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for combo in combos:
            name = label(combo)
            html = markup_for(combo)
            for width in args.widths:
                page = browser.new_page(viewport={"width": width, "height": HEIGHT},
                                        reduced_motion="reduce")
                page.set_content(SHELL.format(
                    title=name, tokens=tokens, css=css, markup=html,
                    filler=FILLER))
                for state in ("shut", "open", "scrolled"):
                    page.evaluate("window.scrollTo(0, %d)"
                                  % (SCROLL_TO if state == "scrolled" else 0))
                    page.eval_on_selector(
                        ".masthead-nav-disclosure",
                        "el => el.%s" % ("removeAttribute('open')" if state == "shut"
                                         else "setAttribute('open','')"))
                    page.wait_for_timeout(30)
                    got = page.evaluate(MEASURE)
                    rendered += 1
                    if not args.no_shots and shot_worthy(combo):
                        page.screenshot(
                            path=str(out / ("%s--%d-%s.png" % (name, width, state))))

                    where = "%s @%d %s" % (name, width, state)
                    if not got["joinInsideDisclosure"]:
                        faults.append(where + ": join is not inside the disclosure")

                    # A scrolled state that did not scroll is a state that
                    # reports every header pins and every control is reachable,
                    # because nothing moved. Assert the page moved first.
                    if state == "scrolled":
                        if not got["scrollable"] or got["scrollY"] != SCROLL_TO:
                            faults.append(
                                "%s: the page did not scroll (scrollY %s, scrollable %s)"
                                % (where, got["scrollY"], got["scrollable"]))
                        pinned = abs(got["headerTop"]) < 0.5
                        # An open drawer pins the bar whatever the sticky rung,
                        # because the button that shuts the drawer lives in the
                        # bar and the drawer is fixed to the viewport. Below
                        # 60rem with the drawer open, pinned is the right
                        # answer on both rungs and NOT pinning is the fault.
                        held_by_drawer = (combo.get("menu") == "drawer"
                                          and width < 960)
                        want = combo.get("sticky") == "pinned" or held_by_drawer
                        if want and not pinned:
                            faults.append(
                                "%s: bar did not pin, header top %s%s"
                                % (where, got["headerTop"],
                                   " - an open drawer must keep its own close "
                                   "control on screen" if held_by_drawer else ""))
                        if not want and pinned:
                            faults.append(where + ": bar stayed pinned with "
                                          "nothing asking it to")
                        # The close control is half of "reachable while open".
                        if want and not got["toggleOnScreen"]:
                            faults.append(where + ": the close control is off "
                                          "screen while the drawer is open")

                    # The rule that matters. A control the reader cannot touch
                    # is the fault this work exists to remove, so it is judged
                    # by hit test rather than by visibility. Scrolled, only a
                    # pinned bar owes this: a bar that scrolled away has taken
                    # its controls with it, which is what sticky=no means.
                    if state == "open" or (state == "scrolled"
                                           and combo.get("sticky") == "pinned"):
                        for control in ("join", "login"):
                            c = got[control]
                            if not c["visible"] or not c["inView"]:
                                faults.append(
                                    "%s: %s not on screen (visible=%s inView=%s)"
                                    % (where, control, c["visible"], c["inView"]))
                            elif not c["onTop"]:
                                faults.append("%s: %s is behind %s"
                                              % (where, control, c["blockedBy"]))
                    # A pinned bar over the page IS the point of sticky, so the
                    # clearance rule is asked at rest, where it means something.
                    if state != "scrolled" and got["headerBottom"] - got["underTop"] > 0.5:
                        faults.append(
                            "%s: header foot %s is below the section top %s"
                            % (where, got["headerBottom"], got["underTop"]))
                    if got["docScrollWidth"] > got["viewport"] + 1:
                        faults.append(
                            "%s: scrolls sideways (%s > %s)"
                            % (where, got["docScrollWidth"], got["viewport"]))
                    new = [s for s in got["small"]
                           if not any(k in s for k in KNOWN)]
                    known += len(got["small"]) - len(new)
                    if width == 320 and new:
                        faults.append("%s: under 44px - %s"
                                      % (where, ", ".join(new)))
                page.close()
        browser.close()

    print("%d renders across %d combinations%s"
          % (rendered, len(combos),
             "" if args.no_shots else ", PNGs in %s" % out))
    if known:
        print("%d target(s) under 44px matched ci/check_phone.py's accepted "
              "baseline and are not reported" % known)
    if faults:
        print("\n%d fault(s):" % len(faults))
        for f in faults:
            print("  " + f)
        return 1
    print("clean: every combination reachable, clear and inside the viewport.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
