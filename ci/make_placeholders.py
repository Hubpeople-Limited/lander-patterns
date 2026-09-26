#!/usr/bin/env python3
"""Write the placeholder set in lib/placeholders/ from one drawing per subject.

Usage:
  python ci/make_placeholders.py          write every <subject>-<crop>.svg
  python ci/make_placeholders.py --check  fail if a file differs from what
                                          this script would write (CI runs this)

The files are uploaded to the CDN once and their hashes recorded in
placeholders.json, so an edit here means a new upload. lint.py says so when
the hashes stop matching.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _placeholders import CROPS, SUBJECTS, file_name  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "lib" / "placeholders"
# An SVG literal, not pattern CSS: the drawing is grey on a transparent
# ground, and the brand's colour comes from the tint the pattern paints
# behind it.
INK = "#808080"

PERSON = ('<circle cx="50" cy="34" r="13"/>'
          '<path d="M24 82c0-15 12-27 26-27s26 12 26 27"/>')


def _at(dx, scale):
    return (f'<g transform="translate({dx} 0) translate(50 50) scale({scale}) '
            f'translate(-50 -50)">{PERSON}</g>')


# Each drawing sits in a 100x100 box. Pictograms, never a likeness: the
# placeholder must read as "a picture goes here", not as somebody.
DRAWINGS = {
    "person": PERSON,
    "couple": _at(-15, 0.86) + _at(15, 0.86),
    "group": _at(-26, 0.72) + _at(26, 0.72) + _at(0, 0.86),
    "place": '<path d="M8 80 34 48l18 20 12-14 28 26z"/><circle cx="72" cy="30" r="8"/>',
    "object": '<rect x="22" y="32" width="56" height="42" rx="6"/><circle cx="50" cy="53" r="11"/>',
}


def _num(value):
    return f"{round(value, 2):g}"


def svg(subject, crop):
    w, h = CROPS[crop]
    short = min(w, h)
    box = short * 0.42
    pad = round(short * 0.04)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}">\n'
        f'  <title>Photo to come</title>\n'
        f'  <g fill="none" stroke="{INK}" stroke-width="3.2" '
        f'stroke-linecap="round" stroke-linejoin="round" '
        f'transform="translate({_num((w - box) / 2)} {_num((h - box) / 2)}) '
        f'scale({_num(box / 100)})">{DRAWINGS[subject]}</g>\n'
        f'  <text x="{w // 2}" y="{_num((h - box) / 2 - pad)}" text-anchor="middle" '
        f'font-family="system-ui, sans-serif" font-size="{round(short * 0.045)}" '
        f'font-weight="600" fill="{INK}">Photo to come</text>\n'
        f'</svg>\n')


def expected():
    return {file_name(s, c): svg(s, c) for s in SUBJECTS for c in CROPS}


def write(out):
    out.mkdir(parents=True, exist_ok=True)
    for name, text in expected().items():
        (out / name).write_bytes(text.encode("utf-8"))


def stale(out):
    bad = []
    for name, text in expected().items():
        path = out / name
        if not path.is_file() or path.read_bytes().replace(b"\r\n", b"\n") != text.encode("utf-8"):
            bad.append(name)
    return sorted(bad)


def main(argv):
    if "--check" in argv:
        bad = stale(OUT)
        for name in bad:
            print(f"lib/placeholders/{name}: differs from ci/make_placeholders.py - run it and upload again")
        if not bad:
            print(f"clean: {len(expected())} placeholders match what this script writes.")
        return 1 if bad else 0
    write(OUT)
    print(f"wrote {len(expected())} placeholders to lib/placeholders/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
