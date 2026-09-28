#!/usr/bin/env python3
"""Run the section behaviours for real, and hold each to its registry row.

Every behaviour in `lib/hub.js` is a promise in `lib/REGISTRY.md`, and until
this gate nothing ran the section behaviours at all: the phone gate renders
with no script on purpose, and the header gate runs the bundle for the header
alone. A behaviour that mangles a figure, marks the wrong link or builds no
control passes every other check, because every other check reads the page as
authored.

So this gate puts each pattern that declares one of the section behaviours in
a page with the bundle, launched with file access allowed so the module
script actually runs, proves the bundle ran by reading its version off the
page, and holds each behaviour to what its row says:

    counter    a figure ends on the authored text, byte for byte, with its
               prefix, separators, decimals and suffix; it moved on the way
               there; under reduced motion it never moves; with no bundle the
               authored figure is the page
    scrollspy  the link whose heading the reader passed last carries
               aria-current and the state class, exactly one at a time, and
               none above the first heading
    carousel   two controls are built inside the block and none ship in the
               authored render; next moves the slide and previous moves it
               back, wrapping on a radio carousel and disabling at the ends
               of a scroller; the controls are thumb-sized at a phone width,
               and they hold their place while the carousel is operated -
               a control that moves as the rail does is one the reader has
               to chase, and it passes every other check on this list
    signup     a phone opens on one question; Next with nothing chosen stays
               and says why; a tapped answer moves on by itself; members
               show once "looking for" is answered and never after a failed
               search; the hand-off goes to the join link with the answers
               summed, spaces as %20, never "+", interests as a %3B list and
               no password, and it carries what every join link carries -
               the page's own parameters and its pn; under reduced motion it
               still moves on

    python ci/check_behaviours.py                  every pattern declaring one
    python ci/check_behaviours.py stats-band
    python ci/check_behaviours.py --broken         the positive control, below
    python ci/check_behaviours.py --out /tmp/beh   keep the rendered pages
    python ci/check_behaviours.py --require-browser

THE POSITIVE CONTROL. `--broken` writes a COPY of the bundle with one named
line of each behaviour turned wrong - the counter's last write, the
scrollspy's aria-current, the carousel's move - and requires every one of the
three checks to fire. The file in lib/ is never touched. A substitution that
no longer matches is itself a failure, so the control cannot go quietly stale
when a behaviour is reworded.

WHICH PATTERNS. Discovered from the `behaviours:` header of every pattern:
anything declaring `counter`, `scrollspy` or `carousel`. A new pattern taking
one of them is measured the day it lands.

Exit codes: 0 clean, or skipped because no browser is available; 1 at least
one behaviour does not do what its row says; 2 the request itself is unusable.
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
BUNDLE = ROOT / "lib" / "hub.js"

from build_preview import fill, repeat_block            # noqa: E402
from check_phone import browser_unavailable             # noqa: E402
import lint                                             # noqa: E402

BEHAVIOURS = ("counter", "scrollspy", "carousel", "signup")
WIDTH, HEIGHT = 1280, 800
PHONE = 360
TAP_MIN = 44
# How far a control a behaviour builds may travel while its carousel is
# operated. Not zero: a scrollbar appearing or a snap settling can shift a row
# by a pixel or two, and a gate that fails on that teaches people to ignore it.
CONTROL_DRIFT_MAX = 4
# Past the counter's default duration, with room for a slow runner.
COUNTER_SETTLE_MS = 2600
# The figures a real brand writes: a grouped integer with a suffix, a
# decimal, a percentage, and a big grouped number. Each one has to come
# back exactly.
FIGURES = ("12,500+", "4.8", "98%", "1,000,000")
FILLER = "<p>Filler copy so the page scrolls, used only to render this check.</p>\n" * 12

# One line per behaviour, turned wrong by the control. Each must still be
# present in the bundle, or the control has gone stale and says so.
CONTROL_SUBSTITUTIONS = {
    "counter": ("target.textContent = item.authored;",
                'target.textContent = "0";'),
    "scrollspy": ('current.a.setAttribute("aria-current", "true");',
                  'current.a.setAttribute("data-hub-broken", "true");'),
    "carousel": ("group[index].checked = true;",
                 "group[index].checked = group[index].checked;"),
    "carousel-scroller": ("scroller.scrollBy({ left: step * stepSize(), behavior });",
                          "void step;"),
    "signup": (".reduce((sum, r) => sum + Number(r.value), 0)",
               ".reduce((sum, r) => Number(r.value), 0)"),
    "signup-attribution": ("new URLSearchParams(location.search).forEach((v, k) => first(k, v));",
                           "void first;"),
}

# The signup check hands off to this link and never follows it; the GUID in it
# is what the member strip searches with, and the search is answered here.
SIGNUP_JOIN = "https://example.invalid/s/register/00000000-0000-4000-8000-000000000000"
SIGNUP_MEMBERS = [{"MemberName": f"Sample {i}", "MemberImage": f"sample-portrait.svg?m={i}",
                   "MemberAge": 28 + i, "Interests": ""} for i in range(6)]

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
.behaviour-check-section {{ min-height: 900px; padding: 24px 16px; }}
{css}
</style>
<script type="module" src="{bundle}"></script>
</head>
<body>
{before}
{markup}
{after}
</body>
</html>
"""


def bundle_version():
    m = re.search(r'version:\s*"([\d.]+)"', BUNDLE.read_text(encoding="utf-8"))
    return m.group(1) if m else None


def pattern_meta(name):
    path = PATTERNS / name / "pattern.html"
    return lint.parse_header(path.read_text(encoding="utf-8"), path)


def declared(name):
    return {b.strip() for b in pattern_meta(name).get("behaviours", "").split(",") if b.strip()}


def discover():
    out = {}
    for folder in sorted(p for p in PATTERNS.iterdir() if p.is_dir()):
        have = declared(folder.name) & set(BEHAVIOURS)
        if have:
            out[folder.name] = have
    return out


def filled_markup(name):
    folder = PATTERNS / name
    markup = re.sub(r"\s*<!--\n.*?\n-->", "",
                    (folder / "pattern.html").read_text(encoding="utf-8"),
                    count=1, flags=re.S)
    sample_path = folder / "preview-content.json"
    sample = (json.loads(sample_path.read_text(encoding="utf-8"))
              if sample_path.exists() else {})
    filled = fill(markup, sample)
    repeat = sample.get("_repeat")
    if repeat:
        filled = repeat_block(filled, repeat["class"], int(repeat["count"]))
    css = (folder / "pattern.css").read_text(encoding="utf-8")
    return filled, css


def page_for(name, behaviour, tokens, bundle_file, width):
    """The pattern in a page shaped so the behaviour has something to do."""
    filled, css = filled_markup(name)
    before = after = ""
    if behaviour == "counter":
        # Real figures in the dt slots, one of each shape, cycling.
        i = [0]

        def swap(m):
            text = FIGURES[i[0] % len(FIGURES)]
            i[0] += 1
            return m.group(1) + text + m.group(3)
        filled = re.sub(r"(<dt\b[^>]*>)(.*?)(</dt>)", swap, filled, flags=re.S)
        before = '<section class="behaviour-check-section"><h1>Above</h1>' + FILLER + "</section>"
    elif behaviour == "scrollspy":
        # Four entries pointing at four headings spaced down the page.
        item = re.search(r"<li class=\"article-toc-item\">.*?</li>", filled, re.S).group(0)
        entries = "".join(
            re.sub(r'href="[^"]*"', f'href="#hub-s{k}"', item).replace(
                re.search(r"<a[^>]*>(.*?)</a>", item, re.S).group(1), f"Section {k}")
            for k in range(1, 5))
        filled = filled.replace(item, entries)
        after = "".join(
            f'<section class="behaviour-check-section"><h2 id="hub-s{k}">Section {k}</h2>'
            + FILLER + "</section>" for k in range(1, 5))
    elif behaviour == "carousel":
        after = '<section class="behaviour-check-section">' + FILLER + "</section>"
    elif behaviour == "signup":
        # The preview fill writes "#" for the join link; the check needs a
        # real-shaped one, because the member search reads its GUID from it.
        filled = re.sub(r'(<form class="signup-steps-card"[^>]*action=")[^"]*"',
                        lambda m: m.group(1) + SIGNUP_JOIN + '"', filled, count=1)
        after = '<section class="behaviour-check-section">' + FILLER + "</section>"
    return SHELL.format(title=f"{name} {behaviour}", tokens=tokens, css=css,
                        bundle=bundle_file, before=before, markup=filled, after=after)


# ---------------------------------------------------------------- measures

VERSION_JS = "() => (window.HubBehaviours && window.HubBehaviours.version) || null"

COUNTER_JS = """
() => Array.from(document.querySelectorAll('[data-hub-module~="counter"] dt'))
        .map(dt => dt.textContent)
"""

SCROLLSPY_JS = """
() => Array.from(document.querySelectorAll('[data-hub-module~="scrollspy"] a[href^="#"]'))
        .map(a => ({ href: a.getAttribute('href'),
                     current: a.getAttribute('aria-current'),
                     marked: a.classList.contains('hub-scrollspy-current') }))
"""

CAROUSEL_JS = """
() => {
  const block = document.querySelector('[data-hub-module~="carousel"]');
  const prev = block && block.querySelector('.hub-carousel-prev');
  const next = block && block.querySelector('.hub-carousel-next');
  const radios = block ? Array.from(block.querySelectorAll('input[type="radio"]')) : [];
  const scroller = block && (/^(auto|scroll)$/.test(getComputedStyle(block).overflowX)
    ? block : Array.from(block.querySelectorAll('ul, ol'))
        .find(l => /^(auto|scroll)$/.test(getComputedStyle(l).overflowX)));
  const box = el => { if (!el) return null; const r = el.getBoundingClientRect();
                      return [Math.round(r.width), Math.round(r.height)]; };
  return {
    controls: !!(prev && next), prevBox: box(prev), nextBox: box(next),
    prevDisabled: prev ? prev.getAttribute('aria-disabled') : null,
    nextDisabled: next ? next.getAttribute('aria-disabled') : null,
    checked: radios.findIndex(r => r.checked), radios: radios.length,
    scrollLeft: scroller ? Math.round(scroller.scrollLeft) : null,
    scrollMax: scroller ? Math.round(scroller.scrollWidth - scroller.clientWidth) : null,
  };
}
"""


class Shell:
    def __init__(self, broken):
        self.broken = broken

    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            headless=True, args=["--allow-file-access-from-files"])
        self._dir = Path(tempfile.mkdtemp(prefix="lander-behaviours-"))
        for asset in PREVIEW.glob("*.svg"):
            shutil.copy(asset, self._dir / asset.name)
        source = BUNDLE.read_text(encoding="utf-8")
        if self.broken:
            for key, (old, new) in CONTROL_SUBSTITUTIONS.items():
                if old not in source:
                    raise SystemExit(f"control: the {key} substitution no longer matches "
                                     f"lib/hub.js - re-pick the line {old!r}")
                source = source.replace(old, new, 1)
        (self._dir / "hub.js").write_text(source, encoding="utf-8", newline="\n")
        return self

    def __exit__(self, *exc):
        self._browser.close()
        self._pw.stop()
        shutil.rmtree(self._dir, ignore_errors=True)
        return False

    def open(self, html, stem, width=WIDTH, reduced=False, before=None, query=""):
        path = self._dir / f"{stem}.html"
        path.write_text(html, encoding="utf-8", newline="\n")
        tab = self._browser.new_page(
            viewport={"width": width, "height": HEIGHT}, device_scale_factor=1,
            reduced_motion="reduce" if reduced else "no-preference")
        if before:
            before(tab)
        tab.goto(path.as_uri() + query)
        return tab


def check_counter(shell, name, tokens):
    faults = []
    where = f"{name} counter"
    html = page_for(name, "counter", tokens, "hub.js", WIDTH)
    tab = shell.open(html, f"{name}-counter")
    try:
        version = tab.evaluate(VERSION_JS)
        if version != bundle_version():
            return [f"{where}: the bundle did not run (version {version!r} on the page)"]
        # Bring the figures on screen and read them at once, before the
        # count has finished.
        tab.evaluate("() => document.querySelector('[data-hub-module~=\"counter\"]').scrollIntoView()")
        tab.wait_for_timeout(120)
        early = tab.evaluate(COUNTER_JS)
        tab.wait_for_timeout(COUNTER_SETTLE_MS)
        final = tab.evaluate(COUNTER_JS)
    finally:
        tab.close()
    expected = [FIGURES[i % len(FIGURES)] for i in range(len(final))]
    if not final:
        return [f"{where}: no figure found under the counter hook"]
    for i, (got, want) in enumerate(zip(final, expected)):
        if got != want:
            faults.append(f"{where}: figure {i + 1} ends as {got!r} where the page "
                          f"authored {want!r} - the last write is the authored text")
    if early == expected:
        faults.append(f"{where}: no figure had moved 120ms after arriving - the count "
                      f"never ran")
    # Reduced motion: never moves.
    tab = shell.open(html, f"{name}-counter-reduced", reduced=True)
    try:
        tab.evaluate("() => document.querySelector('[data-hub-module~=\"counter\"]').scrollIntoView()")
        tab.wait_for_timeout(150)
        still = tab.evaluate(COUNTER_JS)
    finally:
        tab.close()
    if still != expected:
        faults.append(f"{where}: under reduced motion the figures read {still!r} - "
                      f"the authored figure is the only one allowed")
    return faults


def check_scrollspy(shell, name, tokens):
    where = f"{name} scrollspy"
    html = page_for(name, "scrollspy", tokens, "hub.js", WIDTH)
    tab = shell.open(html, f"{name}-scrollspy")
    try:
        version = tab.evaluate(VERSION_JS)
        if version != bundle_version():
            return [f"{where}: the bundle did not run (version {version!r} on the page)"]
        top = tab.evaluate(SCROLLSPY_JS)
        tab.evaluate("() => { const h = document.getElementById('hub-s3'); "
                     "window.scrollTo(0, h.offsetTop - 40); }")
        tab.wait_for_timeout(150)
        mid = tab.evaluate(SCROLLSPY_JS)
    finally:
        tab.close()
    faults = []
    if not top or len(top) < 4:
        return [f"{where}: fewer than four contents links were built ({len(top)})"]
    if any(l["current"] or l["marked"] for l in top):
        faults.append(f"{where}: a link is current at the top of the page, above "
                      f"the first heading")
    current = [l["href"] for l in mid if l["current"] == "true" and l["marked"]]
    if current != ["#hub-s3"]:
        faults.append(f"{where}: with the third heading passed, the current link(s) "
                      f"read {current} - one link, #hub-s3, should carry aria-current "
                      f"and the state class")
    return faults


def press(tab, which):
    """A DOM click, not a pointer click: the driver refuses to click a control
    carrying aria-disabled, and a disabled control ignoring a press is one of
    the things this gate has to be able to see."""
    tab.evaluate("w => document.querySelector('[data-hub-module~=\"carousel\"] .hub-carousel-' + w).click()", which)


def check_carousel(shell, name, tokens):
    where = f"{name} carousel"
    faults = []
    html = page_for(name, "carousel", tokens, "hub.js", WIDTH)
    tab = shell.open(html, f"{name}-carousel")
    try:
        version = tab.evaluate(VERSION_JS)
        if version != bundle_version():
            return [f"{where}: the bundle did not run (version {version!r} on the page)"]
        tab.wait_for_timeout(100)
        first = tab.evaluate(CAROUSEL_JS)
        if not first["controls"]:
            return [f"{where}: no previous and next controls were built inside the block"]
        press(tab, "next")
        tab.wait_for_timeout(600)
        after_next = tab.evaluate(CAROUSEL_JS)
        press(tab, "prev")
        tab.wait_for_timeout(600)
        after_prev = tab.evaluate(CAROUSEL_JS)
        if first["radios"]:
            press(tab, "prev")
            tab.wait_for_timeout(100)
            wrapped = tab.evaluate(CAROUSEL_JS)
        else:
            wrapped = None
            # Walk to the end and expect the next control to disable.
            for _ in range(12):
                press(tab, "next")
                tab.wait_for_timeout(350)
            end = tab.evaluate(CAROUSEL_JS)
    finally:
        tab.close()
    if first["radios"]:
        if after_next["checked"] != 1:
            faults.append(f"{where}: next left slide {after_next['checked'] + 1} checked "
                          f"where slide 2 should be")
        if after_prev["checked"] != 0:
            faults.append(f"{where}: previous left slide {after_prev['checked'] + 1} "
                          f"checked where slide 1 should be")
        if wrapped["checked"] != first["radios"] - 1:
            faults.append(f"{where}: previous from the first slide left slide "
                          f"{wrapped['checked'] + 1} checked; it should wrap to the last")
    else:
        if not (after_next["scrollLeft"] or 0) > 0:
            faults.append(f"{where}: next did not move the scroller "
                          f"(scrollLeft {after_next['scrollLeft']})")
        if (after_prev["scrollLeft"] or 0) > 1:
            faults.append(f"{where}: previous did not bring the scroller back "
                          f"(scrollLeft {after_prev['scrollLeft']})")
        if first["prevDisabled"] != "true":
            faults.append(f"{where}: the previous control is not disabled at the start")
        if end["nextDisabled"] != "true":
            faults.append(f"{where}: the next control is not disabled at the end "
                          f"(scrollLeft {end['scrollLeft']} of {end['scrollMax']})")
    # No bundle: nothing built.
    plain = html.replace('<script type="module" src="hub.js"></script>', "")
    tab = shell.open(plain, f"{name}-carousel-plain")
    try:
        tab.wait_for_timeout(100)
        bare = tab.evaluate(CAROUSEL_JS)
    finally:
        tab.close()
    if bare["controls"]:
        faults.append(f"{where}: controls are present with no bundle on the page - "
                      f"the authored render carries none")
    # Phone: thumb-sized controls.
    tab = shell.open(html, f"{name}-carousel-phone", width=PHONE)
    try:
        tab.wait_for_timeout(100)
        phone = tab.evaluate(CAROUSEL_JS)
    finally:
        tab.close()
    for label, box in (("previous", phone["prevBox"]), ("next", phone["nextBox"])):
        if not box or min(box) < TAP_MIN:
            faults.append(f"{where}: the {label} control is {box} at {PHONE}px, under "
                          f"the {TAP_MIN}px thumb target")
    # Phone: the controls hold their place while the carousel is operated. A
    # control that moves as the rail does is one the reader has to chase, and a
    # thumb already travelling towards it lands on a photograph instead. This is
    # the half a working control can still fail: the two above prove it is built,
    # big enough and moves the slide, all of which stay true of a button that
    # will not stay still. Phone width because that is where a control is aimed
    # at rather than clicked, and where the scrollport is narrowest.
    tab = shell.open(html, f"{name}-carousel-stability", width=PHONE)
    try:
        tab.wait_for_timeout(100)
        travel = tab.evaluate(CAROUSEL_STABILITY_JS)
    finally:
        tab.close()
    if travel.get("controls"):
        for label in ("previous", "next"):
            moved = travel["moved"][label]
            if moved > CONTROL_DRIFT_MAX:
                faults.append(
                    f"{where}: the {label} control moves {moved}px across the "
                    f"carousel's range at {PHONE}px, over the {CONTROL_DRIFT_MAX}px "
                    f"a control may travel - it sits at {travel['seen'][label]}")
            if not travel["visible"][label]:
                faults.append(f"{where}: the {label} control leaves the viewport "
                              f"while the carousel is operated")
    # Every placement the registry offers, on this pattern's own markup. A
    # placement is an option a page can set, so each one is a way this pattern
    # can ship: "none" has to build nothing at all, and anything else has to
    # record what it resolved to and still hold its controls still.
    for asked in ("none", "edges"):
        marked = html.replace('data-hub-module="carousel"',
                              f'data-hub-module="carousel" '
                              f'data-hub-carousel-controls="{asked}"', 1)
        tab = shell.open(marked, f"{name}-carousel-controls-{asked}", width=PHONE)
        try:
            tab.wait_for_timeout(100)
            placed = tab.evaluate(CAROUSEL_PLACEMENT_JS)
        finally:
            tab.close()
        used = placed.get("used")
        if asked == "none":
            if placed["controls"]:
                faults.append(f"{where}: controls are built with "
                              f'data-hub-carousel-controls="none"')
            if used != "none":
                faults.append(f'{where}: asked for "none" and recorded "{used}"')
            continue
        if used not in ("edges", "under"):
            faults.append(f'{where}: asked for "edges" and recorded "{used}" - '
                          f"the placement in force is not one the registry offers")
        if not placed["controls"]:
            faults.append(f'{where}: no controls built for "{asked}", which '
                          f"resolved to \"{used}\"")
        elif placed["nameKept"] is not True:
            faults.append(f"{where}: a control in the {used} placement lost its "
                          f"label as its accessible name")
    return faults


CAROUSEL_STABILITY_JS = """
async () => {
  const block = document.querySelector('[data-hub-module~="carousel"]');
  const prev = block && block.querySelector('.hub-carousel-prev');
  const next = block && block.querySelector('.hub-carousel-next');
  if (!prev || !next) return { controls: false };
  const scroller = /^(auto|scroll)$/.test(getComputedStyle(block).overflowX)
    ? block : Array.from(block.querySelectorAll('ul, ol'))
        .find(l => /^(auto|scroll)$/.test(getComputedStyle(l).overflowX));
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const seen = { previous: [], next: [] };
  const vis = { previous: true, next: true };
  const sample = () => {
    for (const [label, el] of [['previous', prev], ['next', next]]) {
      const r = el.getBoundingClientRect();
      seen[label].push(Math.round(r.left));
      if (r.right < 1 || r.left > window.innerWidth - 1) vis[label] = false;
    }
  };
  sample();
  if (scroller) {
    // A scroller moves continuously, so walk its whole range rather than
    // trusting the ends: a control can sit still at both and travel between.
    const max = scroller.scrollWidth - scroller.clientWidth;
    for (const frac of [0.25, 0.5, 0.75, 1]) {
      scroller.scrollLeft = Math.round(max * frac);
      await wait(160);
      sample();
    }
  } else {
    // A radio carousel moves in steps; one full lap covers every state.
    const radios = Array.from(block.querySelectorAll('input[type="radio"]'));
    for (let i = 0; i < Math.max(radios.length, 1); i++) {
      next.click();
      await wait(160);
      sample();
    }
  }
  const spread = xs => Math.max(...xs) - Math.min(...xs);
  return {
    controls: true,
    moved: { previous: spread(seen.previous), next: spread(seen.next) },
    visible: vis,
    seen,
  };
}
"""


CAROUSEL_PLACEMENT_JS = """
() => {
  const block = document.querySelector('[data-hub-module~="carousel"]');
  const prev = block && block.querySelector('.hub-carousel-prev');
  const next = block && block.querySelector('.hub-carousel-next');
  const asked = block ? block.getAttribute('data-hub-carousel-prev-label') : null;
  return {
    used: block ? block.getAttribute('data-hub-carousel-controls-used') : null,
    controls: !!(prev && next),
    // The words stay the control's accessible name in every placement, even
    // where the look replaces them with an arrow.
    nameKept: prev && next
      ? (prev.textContent.trim() === (asked || 'Previous') || prev.textContent.trim().length > 0)
        && next.textContent.trim().length > 0
      : null,
  };
}
"""


SIGNUP_PARTS_JS = """
() => Array.from(document.querySelectorAll('[data-hub-signup-part]'))
        .filter(p => p.offsetParent !== null).map(p => p.getAttribute('data-hub-signup-part'))
"""


def signup_stub(members):
    """Answer the member search, and keep the hand-off instead of following it."""
    def before(tab):
        def answer(route):
            if members is None:
                route.fulfill(status=502, body="")
            else:
                route.fulfill(status=200, content_type="application/json",
                              headers={"Access-Control-Allow-Origin": "*"},
                              body=json.dumps(members))
        tab.route("**/api/hs/quicksearch**", answer)
        tab.route("https://example.invalid/**", lambda r: r.abort())
        tab.add_init_script("addEventListener('hub:signup:handoff', "
                            "e => { window.__signupHandoff = e.detail.url })")
        # The platform's record of the page, as its footer script sets it.
        tab.add_init_script("window.templateInfo = {template_name: 'Canvas Studio', "
                            "page_guid: 'abc123def456', template_lang: 'en', "
                            "template_brand_lang: 'en', is_prod: true}")
    return before


def tap(tab, selector):
    """A real press at the middle of the thing, as a finger makes one - once it
    has stopped moving. A step change scrolls the card up smoothly and the
    member strip can arrive above it, and a press measured mid-move lands on
    whatever slid under it."""
    target = tab.locator(selector).first
    box = target.bounding_box()
    for _ in range(40):
        tab.wait_for_timeout(50)
        again = target.bounding_box()
        if again == box:
            break
        box = again
    tab.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)


def check_signup(shell, name, tokens):
    where = f"{name} signup"
    faults = []
    html = page_for(name, "signup", tokens, "hub.js", PHONE)
    face = 'input[name="{0}"][value="{1}"] + .signup-steps-opt-face'
    tab = shell.open(html, f"{name}-signup", width=PHONE, before=signup_stub(SIGNUP_MEMBERS),
                     query="?utm_source=s&utm_medium=m&cmp=abc&gclid=g&cmp=second")
    try:
        tab.wait_for_timeout(300)
        version = tab.evaluate(VERSION_JS)
        if version != bundle_version():
            return [f"{where}: the bundle did not run (version {version!r} on the page)"]
        parts = tab.evaluate(SIGNUP_PARTS_JS)
        if parts != ["iam"]:
            faults.append(f"{where}: a phone opens on {parts!r} - one question, 'iam', is the step")
        tap(tab, ".signup-steps-next")
        tab.wait_for_timeout(150)
        if tab.evaluate(SIGNUP_PARTS_JS) != ["iam"] or not tab.locator(
                '[data-hub-signup-part="iam"] .signup-steps-error').is_visible():
            faults.append(f"{where}: Next with nothing chosen must stay put and say why")
        tap(tab, face.format("mt", 2))
        tab.wait_for_timeout(900)
        if tab.evaluate(SIGNUP_PARTS_JS) != ["seeking"]:
            faults.append(f"{where}: a tapped single answer did not move on by itself")
        tap(tab, face.format("lf", 1))
        tap(tab, face.format("lf", 2))
        tab.wait_for_timeout(600)
        if tab.locator(".signup-steps-members img").count() != 4:
            faults.append(f"{where}: four members should show once 'looking for' is answered")
        tap(tab, ".signup-steps-next")
        tab.wait_for_timeout(500)
        for field, value in (("dd", "14"), ("dm", "8"), ("dy", "1992")):
            tab.fill(f'input[name="{field}"]', value)
        tap(tab, ".signup-steps-next")
        tab.wait_for_timeout(500)
        for chips in ("intent", "enjoy"):
            if tab.evaluate(SIGNUP_PARTS_JS) == [chips]:
                tap(tab, f'[data-hub-signup-part="{chips}"] .signup-steps-chip')
                tap(tab, ".signup-steps-next")
                tab.wait_for_timeout(500)
        if tab.evaluate(SIGNUP_PARTS_JS) != ["email"]:
            return faults + [f"{where}: the steps never reached the last one "
                             f"(stopped on {tab.evaluate(SIGNUP_PARTS_JS)!r})"]
        tab.locator('[data-hub-signup-part="email"] input').first.fill("Sam Lee")
        tab.fill('input[name="em"]', "sam@example.com")
        tab.check('[data-hub-signup-part="email"] input[type="checkbox"]')
        tap(tab, ".signup-steps-submit")
        tab.wait_for_timeout(400)
        url = tab.evaluate("() => window.__signupHandoff || null")
    finally:
        tab.close()
    if not url:
        return faults + [f"{where}: the last step handed nothing off"]
    query = url.split("?", 1)[-1]
    fields = dict(pair.split("=", 1) for pair in query.split("&") if "=" in pair)
    if not url.startswith(SIGNUP_JOIN + "?"):
        faults.append(f"{where}: handed off to {url.split('?')[0]!r}, not the join link")
    if fields.get("lf") != "3":
        faults.append(f"{where}: 'looking for' men and women sent as lf={fields.get('lf')!r} - "
                      f"the answers are summed, 3")
    if "+" in query:
        faults.append(f"{where}: the hand-off carries '+', which the join flow does not read as a space")
    if fields.get("firstname") != "Sam%20Lee":
        faults.append(f"{where}: a first name with a space sent as {fields.get('firstname')!r}")
    if "%3B" not in fields.get("interests", ""):
        faults.append(f"{where}: two interests sent as {fields.get('interests')!r} - "
                      f"a list separated by %3B")
    if "p" in fields:
        faults.append(f"{where}: a password was sent")
    # What every join link on the platform carries: the page's own parameters,
    # the first of each, and its pn attribution, ~ and / written plain.
    carried = {k: fields.get(k) for k in ("utm_source", "utm_medium", "cmp", "gclid")}
    if carried != {"utm_source": "s", "utm_medium": "m", "cmp": "abc", "gclid": "g"}:
        faults.append(f"{where}: the page's own parameters arrived as {carried!r} - each is passed "
                      f"on as it came, the first of each")
    if not fields.get("pn", "").startswith("ai~canvas-studio~abc123def456~/") or "%2F" in fields.get("pn", ""):
        faults.append(f"{where}: pn sent as {fields.get('pn')!r} - ai~<template>~<page>~<path>, "
                      f"as the platform writes it on every join link")
    # A brand with one possible answer to each: the questions are hidden
    # values, nobody is asked them, and each value is sent once.
    single = re.sub(r'<fieldset class="signup-steps-step" data-hub-signup-part="(iam|seeking)">.*?</fieldset>',
                    lambda m: f'<input type="hidden" name="{"mt" if m.group(1) == "iam" else "lf"}" value="1">',
                    html, flags=re.S)
    tab = shell.open(single, f"{name}-signup-single", width=PHONE, before=signup_stub(SIGNUP_MEMBERS))
    try:
        tab.wait_for_timeout(300)
        opening = tab.evaluate(SIGNUP_PARTS_JS)
        for field, value in (("dd", "14"), ("dm", "8"), ("dy", "1992")):
            tab.fill(f'input[name="{field}"]', value)
        tap(tab, ".signup-steps-next")
        tab.wait_for_timeout(500)
        for chips in ("intent", "enjoy"):
            if tab.evaluate(SIGNUP_PARTS_JS) == [chips]:
                tap(tab, f'[data-hub-signup-part="{chips}"] .signup-steps-chip')
                tap(tab, ".signup-steps-next")
                tab.wait_for_timeout(500)
        tab.locator('[data-hub-signup-part="email"] input').first.fill("Sam")
        tab.fill('input[name="em"]', "sam@example.com")
        tab.check('[data-hub-signup-part="email"] input[type="checkbox"]')
        tap(tab, ".signup-steps-submit")
        tab.wait_for_timeout(400)
        single_url = tab.evaluate("() => window.__signupHandoff || ''")
    finally:
        tab.close()
    if opening != ["dob"]:
        faults.append(f"{where}: with both questions fixed the card opens on {opening!r}, not the date of birth")
    sent = single_url.split("?", 1)[-1].split("&")
    if sent.count("mt=1") != 1 or sent.count("lf=1") != 1:
        faults.append(f"{where}: fixed answers must be sent once each - got "
                      f"{[x for x in sent if x.startswith(('mt=', 'lf='))]!r}")
    # A failed search leaves nothing behind.
    tab = shell.open(html, f"{name}-signup-failed", width=PHONE, before=signup_stub(None))
    try:
        tab.wait_for_timeout(300)
        tap(tab, face.format("mt", 2))
        tab.wait_for_timeout(900)
        tap(tab, face.format("lf", 1))
        tab.wait_for_timeout(600)
        if tab.locator(".signup-steps-members").is_visible():
            faults.append(f"{where}: a failed member search left the strip showing")
    finally:
        tab.close()
    # Reduced motion still moves on, without waiting on a tick nobody sees drawn.
    tab = shell.open(html, f"{name}-signup-reduced", width=PHONE, reduced=True,
                     before=signup_stub([]))
    try:
        tab.wait_for_timeout(300)
        tap(tab, face.format("mt", 2))
        tab.wait_for_timeout(250)
        if tab.evaluate(SIGNUP_PARTS_JS) != ["seeking"]:
            faults.append(f"{where}: under reduced motion a tapped answer did not move on")
    finally:
        tab.close()
    return faults


CHECKS = {"counter": check_counter, "scrollspy": check_scrollspy, "carousel": check_carousel,
          "signup": check_signup}


def main():
    ap = argparse.ArgumentParser(description="Run the section behaviours for real "
                                             "and hold each to its registry row.")
    ap.add_argument("names", nargs="*", help="patterns to check (default: every "
                                             "pattern declaring one of the behaviours)")
    ap.add_argument("--tokens", default="brand")
    ap.add_argument("--broken", action="store_true",
                    help="the positive control: a copy of the bundle with one line "
                         "of each behaviour turned wrong; every check must fire")
    ap.add_argument("--out", help="write the rendered pages here")
    ap.add_argument("--require-browser", action="store_true")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    found = discover()
    names = args.names or sorted(found)
    for name in names:
        if name not in found:
            print(f"{name!r} declares none of {', '.join(BEHAVIOURS)}")
            return 2
    why = browser_unavailable()
    if why:
        if args.require_browser:
            print(f"FAIL behaviours: no browser, and --require-browser was asked for - {why}")
            return 1
        print(f"SKIPPED behaviours: {why}. A skip is not a pass.")
        return 0
    tokens = (PREVIEW / f"tokens-{args.tokens}.css").read_text(encoding="utf-8")
    print(f"behaviours: {len(names)} pattern(s) on the {args.tokens} tokens, bundle "
          f"{bundle_version()}" + ("  [control: one line of each turned wrong]" if args.broken else ""))
    print()
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        for name in names:
            for behaviour in sorted(found[name]):
                (out / f"{name}--{behaviour}.html").write_text(
                    page_for(name, behaviour, tokens, "hub.js", WIDTH),
                    encoding="utf-8", newline="\n")

    fired = {b: 0 for b in BEHAVIOURS}
    faults = []
    with Shell(args.broken) as shell:
        for name in names:
            for behaviour in sorted(found[name]):
                got = CHECKS[behaviour](shell, name, tokens)
                fired[behaviour] += len(got)
                faults.extend(got)
                print(f"  {name} {behaviour}: {'FAIL ' + str(len(got)) if got else 'ok'}")
    print()
    for line in faults:
        print(f"  FAIL  {line}")

    exercised = {b for n in names for b in found[n]}
    if args.broken:
        silent = [b for b in BEHAVIOURS if b in exercised and not fired[b]]
        if silent:
            print(f"  CONTROL FAILED: {', '.join(silent)} passed with a line turned "
                  f"wrong. This gate cannot see the thing it exists for.")
            return 1
        print(f"  control: {len(faults)} fault(s) caught across "
              f"{', '.join(sorted(exercised))}. The gate fires.")
        return 0
    if not faults:
        print(f"  clean: {', '.join(sorted(exercised))} do what the registry says, "
              f"on {len(names)} pattern(s)")
    if args.out:
        print(f"\n  pages written to {args.out}")
    return 1 if faults else 0


if __name__ == "__main__":
    raise SystemExit(main())
