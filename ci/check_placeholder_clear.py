#!/usr/bin/env python3
"""A placeholder's drawing sits in clear space, never under words or a control.

The library's placeholder is an SVG picture: a line drawing and its "Photo to
come" mark. The phone gate measures text against text, so a picture under
the words is invisible to it, and on a photo opener that is the point - the
words are meant to sit over a photograph. A placeholder is not a photograph.
Its figures and its mark are shapes a reader reads, and under a headline or
a button they read as clutter on the words.

So this measures the drawing itself. Each placeholder file is laid out once,
inline, at its own size, and the box of its figures and the box of its mark
are read off it. On the page, the image's object-fit and object-position map
those two boxes onto the screen, cut to the image's content box and to every
ancestor that clips. Neither may meet a line of text or a control, and a form
counts as one control: a sign-up card laid over the drawing hides part of it
behind a sheet of questions. Both must also show whole: a frame that crops
the mark to "o to come" says nothing.

Which patterns are discovered, not listed: every opener and close (`layout:`
opener= or close=) with a `placeholder=yes` image slot. Each is rendered with
its preview copy and the placeholder a build would place, on every rung
combination but motion, with the sign-up card in the join button's place
where the pattern offers one, on `brand` and `display`, at 320, 390, 768,
1024, 1280 and 1440.

    python ci/check_placeholder_clear.py                every discovered pattern
    python ci/check_placeholder_clear.py hero-overlay   just this one
    python ci/check_placeholder_clear.py --broken       the positive control
    python ci/check_placeholder_clear.py --require-browser

--broken appends one rule to every pattern laying the placeholder over the
whole section, centred, the way a photograph is laid under words, and
requires the check to fire on every pattern. Exit 0 on that run means each
was detected.

Without a browser this prints SKIPPED and exits 0, unless --require-browser.

Exit codes: 0 clean (or, with --broken, every fault detected); 1 a fault
(or, with --broken, a fault that went undetected).
"""
import argparse
import itertools
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from _placeholders import file_name, parse_image_slots          # noqa: E402
from build_preview import fill, repeat_block, swap_in_placeholders  # noqa: E402
from check_phone import SHELL, browser_unavailable, token_set   # noqa: E402

PATTERNS = ROOT / "patterns"
PLACEHOLDERS = ROOT / "lib" / "placeholders"
TOKEN_SETS = ("brand", "display")
VIEWPORTS = ((320, 640), (390, 844), (768, 1024), (1024, 768), (1280, 800), (1440, 900))
# A stroke is drawn half outside the path the layout box is read from.
STROKE_ALLOWANCE = 4

# The positive control: the drawing laid over the whole section, centred,
# its own frame no longer holding or clipping it.
BROKEN = (".{n} {{ position: relative !important; }}"
          " .{n} :has(> img[data-hub-placeholder]) {{ position: static !important;"
          " overflow: visible !important; }}"
          " .{n} img[data-hub-placeholder] {{ position: absolute !important;"
          " inset: 0 !important; width: 100% !important; height: 100% !important;"
          " max-width: none !important; padding: 0 !important; margin: 0 !important;"
          " object-fit: contain !important; object-position: 50% 50% !important;"
          " contain: none !important; }}")

# Each placeholder file at its own size: the box of everything but the mark,
# and the box of the mark, in the file's own pixels.
GEOMETRY = r"""
() => {
  const out = {};
  for (const box of document.querySelectorAll('[data-file]')) {
    const svg = box.querySelector('svg'), o = svg.getBoundingClientRect();
    const rect = els => {
      const rs = els.map(e => e.getBoundingClientRect()).filter(r => r.width || r.height);
      return [Math.min(...rs.map(r => r.left)) - o.left, Math.min(...rs.map(r => r.top)) - o.top,
              Math.max(...rs.map(r => r.right)) - o.left, Math.max(...rs.map(r => r.bottom)) - o.top];
    };
    out[box.dataset.file] = {
      w: o.width, h: o.height,
      drawing: rect([...svg.querySelectorAll('circle, path, line, rect, ellipse, polyline, polygon')]),
      label: rect([...svg.querySelectorAll('text')]),
    };
  }
  return out;
}
"""

MEASURE = r"""
async ([name, geo, stroke]) => {
  await document.fonts.ready;
  const section = document.querySelector('.' + name);
  const clipOf = el => {
    let c = {left: -Infinity, right: Infinity, top: -Infinity, bottom: Infinity};
    for (let a = el; a && a !== document.body; a = a.parentElement) {
      const s = getComputedStyle(a);
      if (s.overflowX === 'visible' && s.overflowY === 'visible') continue;
      const b = a.getBoundingClientRect();
      c = {left: Math.max(c.left, b.left), right: Math.min(c.right, b.right),
           top: Math.max(c.top, b.top), bottom: Math.min(c.bottom, b.bottom)};
    }
    return c;
  };
  const cut = (r, c) => ({left: Math.max(r.left, c.left), right: Math.min(r.right, c.right),
                          top: Math.max(r.top, c.top), bottom: Math.min(r.bottom, c.bottom)});
  const real = r => r.right - r.left > 1 && r.bottom - r.top > 1;

  // What the drawing may not meet: every line of text, cut to what shows,
  // and every control's box.
  const ink = [];
  const walk = document.createTreeWalker(section, NodeFilter.SHOW_TEXT);
  for (let n = walk.nextNode(); n; n = walk.nextNode()) {
    if (!n.textContent.trim() || !n.parentElement.checkVisibility({visibilityProperty: true, checkVisibilityCSS: true}))
      continue;
    const range = document.createRange();
    range.selectNodeContents(n);
    const c = clipOf(n.parentElement);
    for (const whole of range.getClientRects()) {
      const r = cut(whole, c);
      if (real(r)) ink.push({what: '"' + n.textContent.trim().slice(0, 28) + '"', r});
    }
  }
  for (const el of section.querySelectorAll('a, button, input, select, textarea, summary, form')) {
    if (!el.checkVisibility({visibilityProperty: true, checkVisibilityCSS: true})) continue;
    const r = cut(el.getBoundingClientRect(), clipOf(el.parentElement));
    if (r.right - r.left > 2 && r.bottom - r.top > 2)
      ink.push({what: 'the ' + el.tagName.toLowerCase() + ' .' + (el.classList[0] || ''), r});
  }

  const found = [], pics = [];
  for (const img of section.querySelectorAll('img[data-hub-placeholder]')) {
    if (!img.checkVisibility({visibilityProperty: true, checkVisibilityCSS: true, opacityProperty: true, checkOpacity: true})) continue;
    const file = img.getAttribute('src').split('/').pop().replace(/^placeholder-/, '');
    const g = geo[file];
    if (!g) { found.push('no geometry for ' + file); continue; }
    const s = getComputedStyle(img), b = img.getBoundingClientRect();
    const px = v => parseFloat(v) || 0;
    const box = {left: b.left + px(s.borderLeftWidth) + px(s.paddingLeft),
                 top: b.top + px(s.borderTopWidth) + px(s.paddingTop),
                 right: b.right - px(s.borderRightWidth) - px(s.paddingRight),
                 bottom: b.bottom - px(s.borderBottomWidth) - px(s.paddingBottom)};
    const cw = box.right - box.left, ch = box.bottom - box.top;
    if (cw <= 0 || ch <= 0) continue;
    let sx = cw / g.w, sy = ch / g.h;
    const fit = s.objectFit;
    if (fit === 'cover') sx = sy = Math.max(sx, sy);
    else if (fit === 'contain') sx = sy = Math.min(sx, sy);
    else if (fit === 'none') sx = sy = 1;
    else if (fit === 'scale-down') sx = sy = Math.min(1, sx, sy);
    const pos = s.objectPosition.split(/\s+/);
    const offset = (v, free) => v.endsWith('%') ? free * parseFloat(v) / 100 : parseFloat(v);
    const ox = offset(pos[0], cw - g.w * sx), oy = offset(pos[1] || '50%', ch - g.h * sy);
    const clip = cut(box, clipOf(img.parentElement));
    for (const part of ['drawing', 'label']) {
      const [x0, y0, x1, y1] = g[part];
      const whole = {left: box.left + ox + (x0 - stroke) * sx, top: box.top + oy + (y0 - stroke) * sy,
                     right: box.left + ox + (x1 + stroke) * sx, bottom: box.top + oy + (y1 + stroke) * sy};
      const r = cut(whole, clip);
      const what = part === 'label' ? 'the "Photo to come" mark' : 'the drawing';
      if (!real(r)) { found.push(what + ' cropped out of sight'); continue; }
      pics.push(part);
      const lost = Math.max(r.left - whole.left, whole.right - r.right,
                            r.top - whole.top, whole.bottom - r.bottom);
      if (lost > 2) found.push(what + ' cut ' + Math.round(lost) + 'px short by its frame');
      for (const t of ink) {
        const w = Math.min(r.right, t.r.right) - Math.max(r.left, t.r.left);
        const h = Math.min(r.bottom, t.r.bottom) - Math.max(r.top, t.r.top);
        if (w > 1 && h > 1)
          found.push(what + ' under ' + t.what + ' (' + Math.round(w) + 'x' + Math.round(h) + 'px)');
      }
    }
  }
  return {found: [...new Set(found)], pics: pics.length};
}
"""


def discover(names=None):
    found = []
    for folder in sorted(p for p in PATTERNS.iterdir() if p.is_dir()):
        if names and folder.name not in names:
            continue
        html = (folder / "pattern.html").read_text(encoding="utf-8")
        layout = re.search(r"^layout:\s*(.+)$", html, re.M)
        line = re.search(r"^image-slots:\s*(.+)$", html, re.M)
        slots = parse_image_slots(line.group(1)) if line else None
        if layout and re.search(r"\b(opener|close)=", layout.group(1)) \
                and slots and any(s["placeholder"] for s in slots):
            found.append(folder.name)
    return found


def renders(name):
    """(label, mods, card) for every rung combination but motion, with the
    sign-up card as well where the pattern offers it."""
    import lint
    html = (PATTERNS / name / "pattern.html").read_text(encoding="utf-8")
    meta = lint.parse_header(html, PATTERNS / name / "pattern.html")
    axes = {a: v for a, v in (lint.parse_variants(meta.get("variants", "")) or {}).items()
            if a != "motion"}
    cards = (False, True) if "A SIGN-UP OPENER" in html else (False,)
    for values in itertools.product(*(axes[a] for a in sorted(axes))):
        mods = dict(zip(sorted(axes), values))
        for card in cards:
            label = " ".join([name] + [f"{a}={v}" for a, v in mods.items()]
                             + (["with the card"] if card else []))
            yield label, mods, card


def page(name, tokens, mods, card, extra_css=""):
    import lint
    from check_page import apply_variants
    folder = PATTERNS / name
    source = (folder / "pattern.html").read_text(encoding="utf-8")
    markup = re.sub(r"\s*<!--\n.*?\n-->", "", source, count=1, flags=re.S)
    markup = swap_in_placeholders(name, markup)
    sample = json.loads((folder / "preview-content.json").read_text(encoding="utf-8"))
    markup = fill(markup, sample)
    if sample.get("_repeat"):
        markup = repeat_block(markup, sample["_repeat"]["class"], int(sample["_repeat"]["count"]))
    css = (folder / "pattern.css").read_text(encoding="utf-8")
    if card:
        card_dir = PATTERNS / "signup-card"
        form = re.sub(r"\s*<!--\n.*?\n-->", "",
                      (card_dir / "pattern.html").read_text(encoding="utf-8"),
                      count=1, flags=re.S)
        form = fill(form, json.loads((card_dir / "preview-content.json").read_text(encoding="utf-8")))
        markup, swapped = re.subn(rf'<a class="{re.escape(name)}-btn"[^>]*>.*?</a>',
                                  lambda m: form, markup, count=1, flags=re.S)
        if swapped != 1:
            raise SystemExit(f"{name} offers the sign-up card but has no join button for it")
        if "in place of both anchors" in source:
            markup = re.sub(rf'\s*<a class="{re.escape(name)}-ghost"[^>]*>.*?</a>', "",
                            markup, count=1, flags=re.S)
        css += "\n" + (card_dir / "pattern.css").read_text(encoding="utf-8")
    html = SHELL.format(name=name, width="clear", tokens=token_set(tokens),
                        css=css + "\n" + extra_css, markup=markup)
    if mods:
        meta = lint.parse_header(source, folder / "pattern.html")
        html = apply_variants(name, meta, html, mods)
    return html


def geometry(browser, workdir):
    files = sorted(PLACEHOLDERS.glob("*-*.svg"))
    body = "".join(f'<div data-file="{f.name}">{f.read_text(encoding="utf-8")}</div>'
                   for f in files)
    path = workdir / "geometry.html"
    path.write_text(f"<!DOCTYPE html><html><body style='margin:0'>{body}</body></html>",
                    encoding="utf-8", newline="\n")
    tab = browser.new_page()
    try:
        tab.goto(path.as_uri())
        tab.wait_for_load_state("load")
        return tab.evaluate(GEOMETRY)
    finally:
        tab.close()


def run(names, extra_css_for=lambda name: ""):
    """Returns {(label, tokens, width): (placeholder parts seen, faults)}."""
    from playwright.sync_api import sync_playwright
    out = {}
    workdir = Path(tempfile.mkdtemp(prefix="lander-clear-"))
    try:
        for name in names:
            line = re.search(r"^image-slots:\s*(.+)$",
                             (PATTERNS / name / "pattern.html").read_text(encoding="utf-8"), re.M)
            for slot in parse_image_slots(line.group(1)):
                if slot["placeholder"]:
                    src = PLACEHOLDERS / file_name(slot["subjects"][0], slot["crop"])
                    shutil.copy(src, workdir / f"placeholder-{src.name}")
        for asset in (ROOT / "preview").glob("*.svg"):
            shutil.copy(asset, workdir / asset.name)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                geo = geometry(browser, workdir)
                for name in names:
                    for label, mods, card in renders(name):
                        for tokens in TOKEN_SETS:
                            html = page(name, tokens, mods, card, extra_css_for(name))
                            path = workdir / f"{name}.html"
                            path.write_text(html, encoding="utf-8", newline="\n")
                            for viewport in VIEWPORTS:
                                tab = browser.new_page(
                                    viewport={"width": viewport[0], "height": viewport[1]},
                                    device_scale_factor=1)
                                try:
                                    tab.goto(path.as_uri())
                                    tab.wait_for_load_state("load")
                                    got = tab.evaluate(MEASURE, [name, geo, STROKE_ALLOWANCE])
                                finally:
                                    tab.close()
                                out[(name, label, tokens, viewport[0])] = (got["pics"], got["found"])
            finally:
                browser.close()
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    return out


def report(results, quiet=False):
    for (name, label, tokens, width), (pics, found) in sorted(results.items()):
        if quiet and not found:
            continue
        mark = "FAIL" if found else "ok  "
        print(f"  {mark} {label} on {tokens} at {width}px"
              + (f" - {'; '.join(found[:3])}" if found else
                 f" - drawing and mark clear" if pics else " - no placeholder in view"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("patterns", nargs="*")
    ap.add_argument("--broken", action="store_true")
    ap.add_argument("--require-browser", action="store_true")
    ap.add_argument("--quiet", action="store_true", help="print failing renders only")
    args = ap.parse_args()

    why = browser_unavailable()
    if why:
        print(f"SKIPPED: {why}. A skip is not a pass.")
        return 1 if args.require_browser else 0
    names = discover(set(args.patterns) or None)
    if not names:
        print("no opener or close carries a placeholder - nothing to measure")
        return 1 if args.patterns else 0

    if args.broken:
        results = run(names, lambda name: BROKEN.format(n=name))
        missed = []
        for name in names:
            mine = [v for k, v in results.items() if k[0] == name]
            caught = sum(1 for v in mine if v[1])
            print(f"  {'ok  ' if caught else 'MISS'} control on {name}: caught on "
                  f"{caught} of {len(mine)} render(s)")
            if not caught:
                missed.append(name)
        print("positive control: every pattern's fault detected" if not missed
              else f"positive control: undetected on {', '.join(missed)}")
        return 1 if missed else 0

    results = run(names)
    report(results, quiet=args.quiet)
    bad = sum(1 for v in results.values() if v[1])
    print(f"{bad} render(s) failing" if bad else
          f"clean: {len(results)} render(s) across {len(names)} pattern(s) - every "
          "placeholder's drawing and mark sit clear of the words and controls")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
