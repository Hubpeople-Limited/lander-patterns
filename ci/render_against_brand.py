#!/usr/bin/env python3
"""Render patterns against a real brand's stylesheet, not a sample one.

The preview build renders every pattern against four token sets written
alongside this library, so they agree with it by construction. That is why a
library which drops 203 declarations on a real brand reported clean on every
gate it had: nothing tested the contract against a stylesheet somebody else
wrote.

    python ci/render_against_brand.py <brand>/site/global.css [pattern ...]
    python ci/render_against_brand.py <brand>/site/global.css --out /tmp/render

Writes one page per pattern, each linking the brand's OWN stylesheet followed
by that pattern's CSS - the same order and the same file a brand gets when a
pattern is appended to it. Open them in a browser: what you are looking for is
a rule that is simply not there, which is what an undefined token produces and
what no amount of reading the CSS will show you.

Reads only. Nothing about any brand is stored here: the path is supplied by
whoever runs it.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
from build_preview import fill, repeat_block          # noqa: E402

PAGE = """<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name} on {brand}</title>
<link rel="stylesheet" href="brand.css">
<style>{css}</style>
<body>
<p style="font:14px system-ui;padding:.75rem 1rem;margin:0;border-bottom:1px solid #ccc">
{name} &middot; rendered on <strong>{brand}</strong>'s own stylesheet
</p>
{markup}
</body>
</html>
"""


def render(folder, brand_css_text):
    html = (folder / "pattern.html").read_text(encoding="utf-8")
    css = (folder / "pattern.css").read_text(encoding="utf-8")
    sample = json.loads((folder / "preview-content.json").read_text(encoding="utf-8"))
    markup = html.split("-->", 1)[1] if html.lstrip().startswith("<!--") else html
    repeat = sample.get("_repeat")
    if repeat:
        markup = repeat_block(markup, repeat["class"], repeat["count"])
    return css, fill(markup, sample)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("stylesheet", help="a real brand's site/global.css")
    ap.add_argument("patterns", nargs="*", help="pattern names; default all")
    ap.add_argument("--out", default=None, help="output directory")
    args = ap.parse_args(argv)

    sheet = Path(args.stylesheet)
    if not sheet.is_file():
        print(f"no stylesheet at {sheet}")
        return 2
    # The brand folder is <brand>/site/global.css, so two levels up names it.
    brand = sheet.parent.parent.name or sheet.stem
    out = Path(args.out) if args.out else ROOT / "preview" / f"on-{brand}"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    shutil.copy(sheet, out / "brand.css")
    for asset in (ROOT / "preview").glob("*.svg"):
        shutil.copy(asset, out / asset.name)

    wanted = set(args.patterns)
    folders = [p for p in sorted((ROOT / "patterns").iterdir()) if p.is_dir()
               and (not wanted or p.name in wanted)]
    if wanted - {p.name for p in folders}:
        print("unknown pattern(s): " + ", ".join(sorted(wanted - {p.name for p in folders})))
        return 2

    rows = []
    for folder in folders:
        css, markup = render(folder, sheet)
        (out / f"{folder.name}.html").write_text(
            PAGE.format(name=folder.name, brand=brand, css=css, markup=markup),
            encoding="utf-8", newline="\n")
        rows.append(f'<li><a href="{folder.name}.html">{folder.name}</a></li>')
    (out / "index.html").write_text(
        f"<!doctype html><meta charset=utf-8><title>on {brand}</title>"
        f"<h1>Patterns on {brand}'s own stylesheet</h1><ul>{''.join(rows)}</ul>",
        encoding="utf-8", newline="\n")
    print(f"{len(folders)} page(s) into {out}")
    print("this is the render the sample token sets cannot give you: open it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
