#!/usr/bin/env python3
"""A placeholder under a photo scrim has to show, and the copy over it has
to stay readable.

A pattern that lays its copy over a photograph carries a scrim, and the
scrim is heavy on purpose: nothing is known about a photograph, so the scrim
carries the contrast alone. The library's placeholder is known - mid-grey
line drawing on the pattern's tint - and under a full-strength scrim it
disappears, so a page built before its photographs arrive shows a dark band
with no sign that a picture belongs there.

Which patterns are discovered, not listed: every pattern with a
`placeholder=yes` image slot whose pattern.css sets `--<name>-scrim-floor`.

Each is rendered with its preview copy and the placeholder a build would
place, on all five sample token sets, at a laptop and a phone viewport, with
the copy hidden. Two numbers come out:

  drawing   how far the placeholder's drawing stands out from the same
            section with the tint and no drawing: over the pixels the drawing
            changes, the 90th percentile of the contrast between the two
            renders. Under THRESHOLD, the placeholder cannot be seen.
  copy      the lowest contrast between the copy's ink and the pixels under
            each line of text (1st percentile per line, lowest line). Under
            4.5:1 fails, as the contract's own pairs do.

THRESHOLD is calibrated, not chosen. Under full-strength scrims the drawing
measured 1.05 to 1.21:1 in cta-image and hero-squeeze, where it cannot be
seen, and 1.35:1 or more in hero-overlay and steps-numbered, where it can.
The bar sits between the two.

    python ci/check_placeholder_scrim.py              every discovered pattern
    python ci/check_placeholder_scrim.py cta-image    just this one
    python ci/check_placeholder_scrim.py --broken     the positive control
    python ci/check_placeholder_scrim.py --require-browser

--broken appends two sets of rules and requires each to be caught: one
gives the scrim its full strength over the old light tint, so the drawing
must fail; one takes the scrim away over a page-ground tint, so the copy
must fail. Exit 0 on that run means both were detected.

Without a browser this prints SKIPPED and exits 0, unless --require-browser.

Exit codes: 0 clean (or, with --broken, every fault detected); 1 a fault
(or, with --broken, a fault that went undetected).
"""
import argparse
import base64
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from _placeholders import file_name, parse_image_slots          # noqa: E402
from build_preview import fill, swap_in_placeholders            # noqa: E402
from check_phone import SHELL, browser_unavailable, token_set   # noqa: E402

PATTERNS = ROOT / "patterns"
PLACEHOLDERS = ROOT / "lib" / "placeholders"
TOKEN_SETS = ("brand", "soft", "sharp", "dark", "display")
VIEWPORTS = ((1280, 800), (390, 844))
THRESHOLD = 1.3
COPY_FLOOR = 4.5
BLANK = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='9'/%3E"

# Hides the copy and the controls and nothing else - the image, its tint and
# every scrim stay - so the pixels measured are what the copy sits on. Text a
# pseudo-element draws, such as a counter numeral, is copy too: its glyphs go
# transparent and any scrim it paints as a background stays.
TEXT = "h1, h2, h3, h4, p, a, button, span, small, strong, em, time, figcaption, blockquote"
HIDE_COPY = (".{n} :is(" + TEXT + ") {{ visibility: hidden !important; }}"
             " .{n} img {{ visibility: visible !important; }}"
             " .{n} *::before, .{n} *::after {{ color: transparent !important; }}")

# Runs in the page after both screenshots: per-pixel sRGB luminance, then
# the two numbers. Kept in the page because the arrays are millions long.
MEASURE = r"""
async ([withDrawing, without, rects]) => {
  const load = src => new Promise(ok => { const i = new Image(); i.onload = () => ok(i); i.src = src; });
  const pixels = async src => {
    const img = await load(src);
    const c = document.createElement('canvas');
    c.width = img.width; c.height = img.height;
    const g = c.getContext('2d');
    g.drawImage(img, 0, 0);
    return { w: img.width, data: g.getImageData(0, 0, img.width, img.height).data };
  };
  const lin = v => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
  const lum = (d, i) => 0.2126 * lin(d[i]) + 0.7152 * lin(d[i + 1]) + 0.0722 * lin(d[i + 2]);
  const ratio = (a, b) => (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
  const pct = (xs, p) => { xs.sort((a, b) => a - b); return xs[Math.min(xs.length - 1, Math.floor(xs.length * p))]; };
  const A = await pixels(withDrawing), B = await pixels(without);
  const diff = [];
  for (let i = 0; i < A.data.length; i += 4) diff.push(ratio(lum(A.data, i), lum(B.data, i)));
  const c = document.createElement('canvas').getContext('2d');
  const inkLum = ink => { c.fillStyle = ink; c.fillRect(0, 0, 1, 1); return lum(c.getImageData(0, 0, 1, 1).data, 0); };
  let copy = Infinity;
  for (const r of rects) {
    const ink = inkLum(r.ink);
    const xs = [];
    for (let y = Math.max(0, r.y); y < Math.min(r.y + r.h, A.data.length / 4 / A.w); y++)
      for (let x = Math.max(0, r.x); x < Math.min(r.x + r.w, A.w); x++)
        xs.push(ratio(ink, lum(A.data, (y * A.w + x) * 4)));
    if (xs.length) copy = Math.min(copy, pct(xs, 0.01));
  }
  // The drawing is thin lines on a large field, so a percentile over the
  // whole section measures the field. Over the pixels the drawing changed:
  const changed = diff.filter(d => d > 1.02);
  return { drawing: changed.length ? pct(changed, 0.9) : 1,
           copy: copy === Infinity ? null : copy };
}
"""

# Faults the positive control appends. Appended rather than spliced into the
# stylesheet, so rewording the shipped rules cannot quietly disarm them.
BROKEN = {
    "drawing": (".{n} img[data-hub-placeholder] {{ background: color-mix(in srgb, "
                "var(--color-primary) 18%, var(--color-surface)) !important; }}"
                " .{n}, .{n}:has(img[data-hub-placeholder]) "
                "{{ --{n}-scrim-floor: 1 !important; }}"),
    "copy": (".{n}::after {{ background: none !important; }}"
             " .{n} {{ background: transparent !important; }}"
             " .{n} img[data-hub-placeholder] {{ background: var(--color-bg) !important; }}"),
}


def discover(names=None):
    found = []
    for folder in sorted(p for p in PATTERNS.iterdir() if p.is_dir()):
        if names and folder.name not in names:
            continue
        html = (folder / "pattern.html").read_text(encoding="utf-8")
        css = (folder / "pattern.css").read_text(encoding="utf-8")
        line = re.search(r"^image-slots:\s*(.+)$", html, re.M)
        slots = parse_image_slots(line.group(1)) if line else None
        if slots and any(s["placeholder"] for s in slots) \
                and f"--{folder.name}-scrim-floor" in css:
            found.append(folder.name)
    return found


def page(name, tokens, extra_css=""):
    folder = PATTERNS / name
    markup = (folder / "pattern.html").read_text(encoding="utf-8")
    markup = re.sub(r"\s*<!--\n.*?\n-->", "", markup, count=1, flags=re.S)
    markup = swap_in_placeholders(name, markup)
    import json
    sample = json.loads((folder / "preview-content.json").read_text(encoding="utf-8"))
    css = (folder / "pattern.css").read_text(encoding="utf-8") + "\n" + extra_css
    return SHELL.format(name=name, width="scrim", tokens=tokens, css=css,
                        markup=fill(markup, sample))


def measure(browser, workdir, name, tokens_name, viewport, extra_css=""):
    html = page(name, token_set(tokens_name), extra_css)
    hidden = f"<style>{HIDE_COPY.format(n=name)}</style></head>"
    shot = workdir / f"{name}-{tokens_name}-{viewport[0]}.html"
    shot.write_text(html.replace("</head>", hidden, 1), encoding="utf-8", newline="\n")
    tab = browser.new_page(viewport={"width": viewport[0], "height": viewport[1]})
    try:
        tab.goto(shot.as_uri())
        tab.wait_for_load_state("load")
        section = tab.locator(f".{name}").first
        box = section.bounding_box()
        # Copy counts only where it sits over a placeholder, and only the part
        # of it that does: a section heading on the page ground is the page's
        # business, and one whose box grazes the image edge in a wider face
        # is not copy on the scrim. A line counts when its centre is inside
        # an image, and is measured inside that image alone.
        rects = tab.evaluate(f"""() => {{
            const s = document.querySelector('.{name}'), o = s.getBoundingClientRect();
            const pics = [...s.querySelectorAll('img[data-hub-placeholder]')]
                .map(i => i.getBoundingClientRect());
            const texts = [...s.querySelectorAll('h1, h2, h3, h4, p')]
                .filter(e => e.textContent.trim());
            const out = [];
            for (const e of texts) for (const r of e.getClientRects()) {{
                const cx = (r.left + r.right) / 2, cy = (r.top + r.bottom) / 2;
                const p = pics.find(p => cx > p.left && cx < p.right && cy > p.top && cy < p.bottom);
                if (!p) continue;
                const left = Math.max(r.left, p.left), top = Math.max(r.top, p.top);
                out.push({{x: Math.round(left - o.left), y: Math.round(top - o.top),
                          w: Math.round(Math.min(r.right, p.right) - left),
                          h: Math.round(Math.min(r.bottom, p.bottom) - top),
                          ink: getComputedStyle(e).color}});
            }}
            return out;
        }}""")
        with_drawing = tab.screenshot(clip=box, full_page=True)
        tab.evaluate(f"""() => {{
            for (const i of document.querySelectorAll('.{name} img[data-hub-placeholder]'))
                i.src = "{BLANK}";
        }}""")
        tab.wait_for_timeout(50)
        without = tab.screenshot(clip=box, full_page=True)
        to_url = lambda b: "data:image/png;base64," + base64.b64encode(b).decode()
        return tab.evaluate(MEASURE, [to_url(with_drawing), to_url(without), rects])
    finally:
        tab.close()


def run(names, broken_kind=None):
    """Returns {(name, tokens, width): (drawing, copy, faults)}."""
    from playwright.sync_api import sync_playwright
    out = {}
    workdir = Path(tempfile.mkdtemp(prefix="lander-scrim-"))
    try:
        for name in names:
            for slot in parse_image_slots(re.search(
                    r"^image-slots:\s*(.+)$",
                    (PATTERNS / name / "pattern.html").read_text(encoding="utf-8"),
                    re.M).group(1)):
                if slot["placeholder"]:
                    src = PLACEHOLDERS / file_name(slot["subjects"][0], slot["crop"])
                    shutil.copy(src, workdir / f"placeholder-{src.name}")
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                for name in names:
                    extra = BROKEN[broken_kind].format(n=name) if broken_kind else ""
                    for tokens_name in TOKEN_SETS:
                        for viewport in VIEWPORTS:
                            got = measure(browser, workdir, name, tokens_name, viewport, extra)
                            faults = []
                            if got["drawing"] < THRESHOLD:
                                faults.append("drawing")
                            if got["copy"] is not None and got["copy"] < COPY_FLOOR:
                                faults.append("copy")
                            out[(name, tokens_name, viewport[0])] = (
                                got["drawing"], got["copy"], faults)
            finally:
                browser.close()
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    return out


def report(results):
    for (name, tokens_name, width), (drawing, copy, faults) in sorted(results.items()):
        mark = "FAIL" if faults else "ok  "
        shown = f"{copy:5.2f}:1" if copy is not None else " none over it"
        print(f"  {mark} {name:<14} {tokens_name:<8} {width:>5}px  "
              f"drawing {drawing:5.2f}:1 (bar {THRESHOLD})  "
              f"copy {shown} (floor {COPY_FLOOR})"
              + (f"  - {', '.join(faults)}" if faults else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("patterns", nargs="*")
    ap.add_argument("--broken", action="store_true")
    ap.add_argument("--require-browser", action="store_true")
    args = ap.parse_args()

    why = browser_unavailable()
    if why:
        print(f"SKIPPED: {why}. A skip is not a pass.")
        return 1 if args.require_browser else 0
    names = discover(set(args.patterns) or None)
    if not names:
        print("no pattern lays a placeholder under a scrim - nothing to measure")
        return 1 if args.patterns else 0

    if args.broken:
        missed = []
        for kind in BROKEN:
            results = run(names, kind)
            caught = [k for k, v in results.items() if kind in v[2]]
            print(f"  {'ok  ' if caught else 'MISS'} control '{kind}': caught on "
                  f"{len(caught)} of {len(results)} render(s)")
            if not caught:
                missed.append(kind)
        print("positive control: every fault detected" if not missed
              else f"positive control: {', '.join(missed)} went undetected")
        return 1 if missed else 0

    results = run(names)
    report(results)
    bad = sum(1 for v in results.values() if v[2])
    print(f"{bad} render(s) failing" if bad else
          f"clean: {len(results)} render(s) across {len(names)} pattern(s) - the "
          "placeholder shows and the copy holds 4.5:1")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
