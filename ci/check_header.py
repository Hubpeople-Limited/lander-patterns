#!/usr/bin/env python3
"""Render the site header against menus the size real brands have.

Every render of `masthead-nav` in this repository carries the same sample
menu: a few short links and one small group. Real menus are not like that.
A brand with six pages, a group of places under one of them and a label
twenty-four characters long is ordinary, and the header had never been laid
out with one. Above `60rem` the items wrapped onto a second row, the bar grew,
`--page-header-height` stopped being true, and the join control on a
full-viewport opener slid below the fold - with every gate green, because
every gate rendered the sample menu.

So this gate renders the header with three menus - short, typical and long -
beside a ratio-only wordmark and a ratio-only square, at eight widths across
the `60rem` line, with the behaviour library on and off, on the rungs that
decide how a long menu behaves. It holds the header to:

    ONE ROW        above the line, on `overflow=more` with the library and on
                   `overflow=scroll` without it, the items sit on one row
    NO OVERLAP     the brand mark never sits on a menu item or a control
    IN VIEW        every submenu opened, and the folded item's own list, stay
                   inside the viewport
    REACHABLE      the join control is on top and in view - with the drawer
                   open below the line, and on the bar above it
    THUMB-SIZED    every control is 44px at phone widths
    NO SIDEWAYS    the document never scrolls sideways

    python ci/check_header.py                  the matrix, brand tokens
    python ci/check_header.py --tokens display
    python ci/check_header.py --broken         the positive control, below
    python ci/check_header.py --out /tmp/hdr   keep the rendered pages
    python ci/check_header.py --require-browser

THE POSITIVE CONTROL. `--broken` appends one rule that switches the fold off
- the property the overflow behaviour reads is forced to `off` - and requires
the one-row check to fire on the long menu. A gate that has only ever run
against code that passes has not been shown to catch anything. Exit 0 on that
run means the defect was detected. Appended rather than spliced, so rewording
the shipped rule cannot quietly disarm it.

Exit codes: 0 clean, or skipped because no browser is available; 1 at least one
render is at fault; 2 the request itself is unusable.
"""
import argparse
import base64
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
PATTERN = ROOT / "patterns" / "masthead-nav"
PREVIEW = ROOT / "preview"

from build_preview import fill                          # noqa: E402
from check_logo import FIXTURES as LOGOS                # noqa: E402
from check_page import apply_variants                   # noqa: E402
from check_phone import browser_unavailable             # noqa: E402
import lint                                             # noqa: E402

META = lint.parse_header(
    (PATTERN / "pattern.html").read_text(encoding="utf-8"), PATTERN / "pattern.html")

# 320 and 360 are the phone floor and mode this repo already measures at; 390
# is the commonest current phone; 768 is the tablet band; 960 is the line
# itself, where the row layout arrives with the least room it will ever have;
# 1024 is a tablet held sideways; 1280 and 1440 are laptops.
WIDTHS = (320, 360, 390, 768, 960, 1024, 1280, 1440)
HEIGHT = 900
TAP_MIN = 44
# Past the menu behaviour's hover grace, so one parent's panel has shut
# before the next is measured.
HOVER_SETTLE_MS = 300
# A control a pointer cannot reach in this long is a fault, not a wait.
POINT_TIMEOUT_MS = 3000

# The menus, as the platform emits them: a plain item is <li><a href title
# target>; a parent with children and no URL is <li class="has-submenu"><a>
# with a nested list; a parent with both arrives as two <li>s.
LONG_LABEL = "Membership and pricing"          # 22 characters, a real shape


def item(label, href="#sample"):
    return (f'<li><a href="{href}" title="{label}" target="_self">{label}</a></li>')


def group(label, children, cls="canvas-navigation-submenu"):
    inner = "".join(item(c) for c in children)
    return f'<li class="has-submenu"><a>{label}</a><ul class="{cls}">{inner}</ul></li>'


MENUS = {
    "short": '<ul class="canvas-navigation-menu">'
             + item("Home") + item("Features") + item("Pricing")
             + "</ul>",
    "typical": '<ul class="canvas-navigation-menu">'
               + item("Home") + item("How it works") + item("Pricing")
               + group("Places", ["Manchester", "Leeds", "Sheffield",
                                  "Newcastle upon Tyne", "Liverpool"])
               + item("Safety") + item("Stories")
               + "</ul>",
    "long": '<ul class="canvas-navigation-menu">'
            + item("Home") + item("How it works") + item(LONG_LABEL)
            + group("Places", ["Manchester", "Leeds", "Sheffield", "Newcastle",
                               "Liverpool", "Birmingham", "Bristol", "Cardiff",
                               "Edinburgh", "Glasgow", "Nottingham", "York"])
            + item("Safety")
            + item("Advice") + group("Advice", ["First dates", "Profiles"])
            + item("Events") + item("Stories") + item("Contact")
            + "</ul>",
}

LOGO_FIXTURES = ("wordmark-ratio-only", "square-ratio-only")

# The rungs that decide what a long menu does, crossed; every other axis at
# its default. nav=minimal has no menu to fit and is measured once, for the
# controls it keeps. dev/render_matrix.py covers the rest of the matrix.
COMBOS = [
    {"overflow": o, "submenu": s, "layout": l}
    for o in ("wrap", "more", "scroll")
    for s in ("dropdown", "mega")
    for l in ("inline", "centred")
    if not (o == "scroll" and s == "mega")
] + [
    {"overflow": "more", "submenu": "dropdown", "layout": "inline", "nav": "minimal"},
    {"overflow": "more", "submenu": "dropdown", "layout": "inline", "sticky": "compact"},
]

FILLER = "  <p>More sample copy, so the page is tall enough to scroll.</p>\n" * 30

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
.header-check-under {{ padding: 24px 16px; background: var(--color-surface-soft); }}
{css}
</style>
{script}
</head>
<body>
{markup}
<section class="header-check-under">
  <h1>The section under the header</h1>
{filler}
</section>
</body>
</html>
"""

MEASURE = r"""
() => {
  const round = n => Math.round(n * 10) / 10;
  const W = document.documentElement.clientWidth;
  const header = document.querySelector('.masthead-nav');
  const nav = document.querySelector('.masthead-nav-links');
  const list = nav ? nav.querySelector(':scope > ul, :scope > ol') : null;
  const logo = document.querySelector('.masthead-nav-logo');
  const join = document.querySelector('.masthead-nav-join');
  const toggle = document.querySelector('.masthead-nav-toggle');
  const more = document.querySelector('.hub-overflow-more');

  const shown = el => {
    if (!el) return false;
    const s = getComputedStyle(el);
    if (s.display === 'none' || s.visibility === 'hidden') return false;
    if (parseFloat(s.opacity) === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0.5 && r.height > 0.5;
  };
  const rect = el => {
    const r = el.getBoundingClientRect();
    return { left: round(r.left), right: round(r.right), top: round(r.top),
             bottom: round(r.bottom), width: round(r.width), height: round(r.height) };
  };
  const hit = el => {
    if (!el) return { present: false };
    const b = el.getBoundingClientRect();
    const x = b.left + b.width / 2, y = b.top + b.height / 2;
    const inView = b.width > 0 && b.height > 0
      && x >= 0 && y >= 0 && x < innerWidth && y < innerHeight;
    const top = inView ? document.elementFromPoint(x, y) : null;
    return { present: true, visible: shown(el), inView,
             onTop: !!top && (top === el || el.contains(top)),
             blockedBy: top && !(top === el || el.contains(top))
               ? (top.className || top.tagName) : null };
  };
  const intersects = (a, b) =>
    a.left < b.right - 1 && b.left < a.right - 1 && a.top < b.bottom - 1 && b.top < a.bottom - 1;

  // The rows the top-level items sit on, by their top edge. A button's box
  // is a few pixels taller than a link's, so items on one row do not share
  // an exact top; a new row starts where the top moves by more than half
  // an item.
  const items = list ? Array.from(list.children).filter(shown) : [];
  const tops = [];
  items.map(li => li.getBoundingClientRect())
       .sort((a, b) => a.top - b.top)
       .forEach(r => {
         const last = tops[tops.length - 1];
         if (last === undefined || r.top - last > Math.max(12, r.height / 2)) tops.push(r.top);
       });

  // The mark against everything else that can be pressed in the bar.
  const overlaps = [];
  if (logo && shown(logo)) {
    const lr = logo.getBoundingClientRect();
    for (const el of header.querySelectorAll('a[href], button, summary')) {
      if (el.closest('.masthead-nav-mark') || !shown(el)) continue;
      if (el.closest('.masthead-nav-tray') && getComputedStyle(el.closest('.masthead-nav-tray')).visibility === 'hidden') continue;
      if (intersects(lr, el.getBoundingClientRect())) {
        overlaps.push((el.getAttribute('class') || el.tagName).split(/\s+/)[0]);
      }
    }
  }

  // ci/check_phone.py's carve-out: a link that is only words is not a control.
  const textLink = el => {
    if (el.tagName !== 'A') return false;
    if (el.querySelector('img, svg, picture')) return false;
    const s = getComputedStyle(el);
    if (s.display === 'inline') return true;
    const pad = parseFloat(s.paddingTop) + parseFloat(s.paddingBottom);
    const filled = s.backgroundImage !== 'none'
      || !/^rgba\(0, 0, 0, 0\)$|^transparent$/.test(s.backgroundColor);
    return !(pad > 4 || parseFloat(s.minHeight) > 0 || filled
             || parseFloat(s.borderTopWidth) > 0 || parseFloat(s.borderBottomWidth) > 0);
  };
  const small = [];
  for (const el of header.querySelectorAll('a[href], button, summary')) {
    if (!shown(el) || textLink(el)) continue;
    const tray = el.closest('.masthead-nav-tray');
    if (tray && getComputedStyle(tray).visibility === 'hidden') continue;
    const b = el.getBoundingClientRect();
    if (Math.min(b.width, b.height) < TAP_MIN - 0.5) {
      small.push((el.getAttribute('class') || el.tagName).split(/\s+/)[0]
                 + ' ' + round(b.width) + 'x' + round(b.height));
    }
  }

  return {
    viewport: W,
    docScrollWidth: document.documentElement.scrollWidth,
    rowLayout: !toggle || getComputedStyle(toggle).display === 'none',
    navShown: !!nav && getComputedStyle(nav).display !== 'none',
    rows: tops.length,
    itemCount: items.length,
    listRect: list ? rect(list) : null,
    headerHeight: round(header.getBoundingClientRect().height),
    overlaps,
    small,
    join: hit(join),
    more: more && shown(more) ? { rect: rect(more),
                                  folded: more.querySelectorAll(':scope > ul > li').length }
                              : null,
    parents: list ? Array.from(list.children)
        .filter(li => shown(li) && li.querySelector(':scope > ul, :scope > ol'))
        .map((li, i) => ({ index: Array.from(list.children).indexOf(li),
                           label: (li.querySelector(':scope > a, :scope > button') || li)
                                    .textContent.trim().slice(0, 30) }))
      : [],
  };
}
"""

# Opens one parent's panel and measures it. Hover for a pointer, then a click
# on the control for the touch and keyboard path the behaviour adds; either
# way the panel has to end up inside the viewport.
PANEL = r"""
(index) => {
  const round = n => Math.round(n * 10) / 10;
  const list = document.querySelector('.masthead-nav-links > ul, .masthead-nav-links > ol');
  const li = list.children[index];
  const sub = li.querySelector(':scope > ul, :scope > ol');
  const s = getComputedStyle(sub);
  const r = sub.getBoundingClientRect();
  const W = document.documentElement.clientWidth;
  return { opacity: parseFloat(s.opacity), left: round(r.left), right: round(r.right),
           width: round(r.width), inView: r.left >= -1 && r.right <= W + 1,
           positioned: /absolute|fixed/.test(s.position),
           items: Array.from(sub.querySelectorAll('a')).filter(a => {
             const b = a.getBoundingClientRect(); return b.width > 0 && b.height > 0; }).length };
}
"""

# The control of one parent, for the driver to hover and press.
CONTROL = ("(index) => { const list = document.querySelector('.masthead-nav-links > ul, "
           ".masthead-nav-links > ol'); const li = list.children[index]; "
           "return li.querySelector(':scope > button, :scope > a'); }")


def token_set(which):
    path = PREVIEW / f"tokens-{which}.css"
    if not path.is_file():
        raise SystemExit(f"no sample token set called {which!r} ({path} does not exist)")
    return path.read_text(encoding="utf-8")


def markup_for(combo, menu, logo_fixture):
    html = (PATTERN / "pattern.html").read_text(encoding="utf-8")
    sample = json.loads((PATTERN / "preview-content.json").read_text(encoding="utf-8"))
    # The fixture menu goes in before the sample furniture does, or fill()
    # puts the small sample menu there and the whole point is lost.
    html = html.replace("{{menu.navigation}}", MENUS[menu])
    html = fill(html, sample)
    html = re.sub(r"<!--(?!\s*slot\s*:).*?-->", "", html, flags=re.S).strip()
    html = apply_variants("masthead-nav", META, html, combo)
    got = re.search(r'<header class="([^"]+)"', html).group(1).split()
    missing = [v for v in combo.values() if "masthead-nav--" + v not in got]
    if missing:
        raise SystemExit(
            "apply_variants did nothing for %s - the rung is declared in "
            "`variants:` but its modifier is not spelled .masthead-nav--<value>"
            % ", ".join(missing))
    svg = LOGOS[logo_fixture]["svg"].encode("utf-8")
    html = html.replace(
        'src="sample-wordmark.svg"',
        'src="data:image/svg+xml;base64,%s"' % base64.b64encode(svg).decode())
    return html


def page(combo, menu, logo_fixture, tokens, script, broken=False):
    css = (PATTERN / "pattern.css").read_text(encoding="utf-8")
    if broken:
        css += "\n.masthead-nav-links > ul { --hub-overflow: off !important; }\n"
    tag = '<script type="module" src="hub.js"></script>' if script else ""
    return SHELL.format(title="masthead-nav " + " ".join(f"{k}={v}" for k, v in combo.items()),
                        tokens=tokens, css=css, script=tag,
                        markup=markup_for(combo, menu, logo_fixture), filler=FILLER)


try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
except ImportError:                                  # pragma: no cover - env
    class PlaywrightTimeoutError(Exception):
        pass


class Shell:
    """One browser and one directory, held open across every render."""

    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        # The pages are opened from disk, and a module script is refused over
        # file: unless the browser is told otherwise - refused silently, so a
        # run without this flag measures every "library on" render with the
        # library off and reports it fine.
        self._browser = self._pw.chromium.launch(
            headless=True, args=["--allow-file-access-from-files"])
        self._dir = Path(tempfile.mkdtemp(prefix="lander-header-"))
        shutil.copy(ROOT / "lib" / "hub.js", self._dir / "hub.js")
        self.keep = None
        return self

    def __exit__(self, *exc):
        self._browser.close()
        self._pw.stop()
        shutil.rmtree(self._dir, ignore_errors=True)
        return False

    def open(self, html, width, name):
        path = self._dir / f"header-{width}.html"
        path.write_text(html, encoding="utf-8", newline="\n")
        if self.keep:
            (self.keep / f"{name}--{width}.html").write_text(html, encoding="utf-8",
                                                             newline="\n")
        tab = self._browser.new_page(viewport={"width": width, "height": HEIGHT},
                                     device_scale_factor=1,
                                     reduced_motion="reduce")
        tab.goto(path.as_uri())
        # The behaviours lay the row out on a resize observation and again
        # when the fonts settle; two frames is enough for both to have run.
        tab.evaluate("() => new Promise(r => requestAnimationFrame(() => "
                     "requestAnimationFrame(r)))")
        return tab


def measure_render(tab, combo, script):
    """(measurement, faults) for one open tab."""
    got = tab.evaluate(MEASURE.replace("TAP_MIN", str(TAP_MIN)))
    faults = []
    width = got["viewport"]
    minimal = combo.get("nav") == "minimal"

    if got["docScrollWidth"] > width + 1:
        faults.append(f"scrolls sideways: document {got['docScrollWidth']}px in a "
                      f"{width}px viewport")
    if got["overlaps"]:
        faults.append("the brand mark sits on " + ", ".join(got["overlaps"]))

    if got["rowLayout"] and not minimal:
        # Above the line. The rungs that promise one row have to keep it.
        promised = (combo["overflow"] == "scroll"
                    or (combo["overflow"] == "more" and script))
        if promised and got["rows"] > 1:
            faults.append(f"the menu sits on {got['rows']} rows on overflow="
                          f"{combo['overflow']} - {got['itemCount']} items, list "
                          f"{got['listRect']['width']}px wide")
        if got["more"]:
            r = got["more"]["rect"]
            if r["left"] < -1 or r["right"] > width + 1:
                faults.append(f"the folded item is outside the viewport "
                              f"({r['left']}..{r['right']} of {width})")
        # Every parent's panel, opened the way a pointer and a finger open it.
        for parent in got["parents"]:
            index = parent["index"]
            control = tab.evaluate_handle(CONTROL, index).as_element()
            if control is None:
                continue
            # A scrolling row holds its later items past the edge; a visitor
            # scrolls to them and so does this.
            control.scroll_into_view_if_needed()
            try:
                control.hover(timeout=POINT_TIMEOUT_MS)
            except PlaywrightTimeoutError:
                faults.append(f"the control for '{parent['label']}' cannot be pointed "
                              f"at - it is outside the viewport or under something")
                continue
            tab.wait_for_timeout(50)
            panel = tab.evaluate(PANEL, index)
            if panel["positioned"] and panel["opacity"] < 0.99 and script:
                # Hover is a mouse; the behaviour also takes a press.
                control.click(timeout=POINT_TIMEOUT_MS)
                tab.wait_for_timeout(50)
                panel = tab.evaluate(PANEL, index)
            if panel["positioned"]:
                if panel["opacity"] < 0.99:
                    faults.append(f"the panel under '{parent['label']}' does not open")
                elif not panel["inView"]:
                    faults.append(f"the panel under '{parent['label']}' leaves the "
                                  f"viewport ({panel['left']}..{panel['right']} of {width})")
                elif panel["items"] == 0:
                    faults.append(f"the panel under '{parent['label']}' has no items in it")
            if panel["positioned"] and script:
                # The press path, which a finger and a keyboard take: shut it
                # from the keyboard, then press the control and expect it open
                # - and a press on a panel the pointer already opened must not
                # shut it again.
                tab.keyboard.press("Escape")
                tab.wait_for_timeout(30)
                control.click(timeout=POINT_TIMEOUT_MS)
                tab.wait_for_timeout(50)
                pressed = tab.evaluate(PANEL, index)
                if pressed["opacity"] < 0.99:
                    faults.append(f"the panel under '{parent['label']}' does not open "
                                  f"on a press")
                tab.keyboard.press("Escape")
            tab.mouse.move(0, HEIGHT - 1)
            tab.wait_for_timeout(HOVER_SETTLE_MS)
        j = got["join"]
        if not (j["present"] and j["visible"] and j["inView"] and j["onTop"]):
            faults.append("the join control is not reachable on the bar"
                          + (f" - behind {j['blockedBy']}" if j.get("blockedBy") else ""))
    elif got["rowLayout"] and minimal:
        j = got["join"]
        if not (j["present"] and j["visible"] and j["inView"] and j["onTop"]):
            faults.append("the join control is not reachable on the menu-free bar")
        if got["navShown"]:
            faults.append("nav=minimal still renders the menu")
    else:
        # Below the line: the drawer, open, has to hand over the join control
        # and every control has to be thumb-sized.
        if minimal:
            j = got["join"]
            if not (j["present"] and j["visible"] and j["inView"] and j["onTop"]):
                faults.append("the join control is not reachable on the menu-free bar")
        else:
            tab.evaluate("() => document.querySelector('.masthead-nav-disclosure')"
                         ".setAttribute('open', '')")
            tab.wait_for_timeout(50)
            opened = tab.evaluate(MEASURE.replace("TAP_MIN", str(TAP_MIN)))
            j = opened["join"]
            if not (j["present"] and j["visible"] and j["inView"] and j["onTop"]):
                faults.append("with the drawer open the join control is not reachable"
                              + (f" - behind {j['blockedBy']}" if j.get("blockedBy") else ""))
            got["small"] = sorted(set(got["small"]) | set(opened["small"]))
        for s in got["small"]:
            faults.append(f"a control under {TAP_MIN}px: {s}")
    return got, faults


def sweep(shell, tokens, combos, menus, logos, widths, script_modes, broken=False):
    faults, count = [], 0
    for combo in combos:
        label = " ".join(f"{k}={v}" for k, v in combo.items())
        for menu in menus:
            for logo in logos:
                for script in script_modes:
                    html = page(combo, menu, logo, tokens, script, broken)
                    for width in widths:
                        name = f"{label.replace(' ', '_').replace('=', '-')}--{menu}--{logo}--{'js' if script else 'nojs'}"
                        tab = shell.open(html, width, name)
                        try:
                            _, found = measure_render(tab, combo, script)
                        finally:
                            tab.close()
                        count += 1
                        where = (f"{label} | {menu} menu | {logo} | "
                                 f"{'library' if script else 'no library'} | {width}px")
                        faults.extend(f"{where}: {f}" for f in found)
    return faults, count


def main():
    ap = argparse.ArgumentParser(
        description="Render the site header against menus the size real brands "
                    "have and check it fits. See the module docstring.")
    ap.add_argument("--tokens", default="brand",
                    help="sample token set to render against (default: brand)")
    ap.add_argument("--broken", action="store_true",
                    help="the positive control: switch the fold off and require "
                         "this check to fire")
    ap.add_argument("--widths", type=int, nargs="*", default=list(WIDTHS))
    ap.add_argument("--out", help="write the rendered pages here")
    ap.add_argument("--require-browser", action="store_true",
                    help="treat a missing browser as a failure, not a skip")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    why = browser_unavailable()
    if why:
        print(f"check_header: SKIPPED - {why}")
        return 1 if args.require_browser else 0

    tokens = token_set(args.tokens)
    with Shell() as shell:
        if args.out:
            shell.keep = Path(args.out)
            shell.keep.mkdir(parents=True, exist_ok=True)
        if args.broken:
            # The narrowest claim that must fail: the long menu, the fold rung,
            # the library on, above the line. Anything wider would let a
            # genuine fault elsewhere pass for the control firing.
            combos = [{"overflow": "more", "submenu": "dropdown", "layout": "inline"}]
            faults, count = sweep(shell, tokens, combos, ["long"],
                                  ["wordmark-ratio-only"], [1280], [True], broken=True)
            fired = [f for f in faults if "rows on overflow=more" in f]
            if fired:
                print(f"check_header --broken: the gate fires ({len(fired)} of "
                      f"{count} renders) - the control holds")
                return 0
            print("check_header --broken: the fold was switched off and nothing "
                  "fired - the gate is not measuring")
            return 1
        faults, count = sweep(shell, tokens, COMBOS, list(MENUS), LOGO_FIXTURES,
                              args.widths, [False, True])

    if faults:
        print(f"check_header ({args.tokens}): {len(faults)} fault(s) in {count} renders")
        for f in faults:
            print("  " + f)
        return 1
    print(f"check_header ({args.tokens}): clean - {count} renders, "
          f"{len(COMBOS)} rung sets x {len(MENUS)} menus x {len(LOGO_FIXTURES)} marks "
          f"x {len(args.widths)} widths, library on and off")
    return 0


if __name__ == "__main__":
    sys.exit(main())
