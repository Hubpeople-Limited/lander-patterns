#!/usr/bin/env python3
"""Assemble static preview pages: every pattern x every sample token set.

Output goes to preview/site/ (gitignored; published by CI). This is repo
tooling only - the inline <style> it writes exists nowhere but the preview.
"""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "preview" / "site"
TOKEN_SETS = {"soft": "tokens-soft.css", "sharp": "tokens-sharp.css",
              "dark": "tokens-dark.css", "brand": "tokens-brand.css"}

# Display stand-ins so furniture tokens render readably in previews. These
# substitutions exist only here; pattern files always keep the real tokens.
FURNITURE_DISPLAY = {
    "{{join.url}}": "#",
    "{{login.url}}": "#",
    "{{join.text}}": "Join sample",
    "{{login.text}}": "Log in sample",
}

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
.preview-note {{ padding: 8px 16px; font-size: 0.8rem;
                 color: var(--color-text-soft);
                 border-bottom: 1px solid var(--color-rule); }}
{css}
</style>
</head>
<body>
<p class="preview-note">Preview render - {name} on the {set_name} token set. Sample content, not a real page.</p>
{markup}
<script type="module">
/* Preview-only embed of lib/hub.js, standing in for the platform's injected
   behaviour library. Pattern files themselves never carry a script. */
{hub_js}
</script>
</body>
</html>
"""


def repeat_block(markup, cls, count):
    """Duplicate the element carrying `cls` until there are `count` of them.

    A pattern ships one of whatever it says to duplicate, which is right for a
    file someone pastes from and wrong for a preview: a grid that only breaks
    at four items has never been rendered. Refuses rather than returning the
    markup unchanged, because a repeat that silently did nothing would put the
    exact failure it exists to catch back out of sight.
    """
    start = markup.find(f'class="{cls}"')
    if start == -1:
        raise SystemExit(f"_repeat: no element carries class {cls!r}")
    open_lt = markup.rfind("<", 0, start)
    tag = re.match(r"<([a-zA-Z][\w-]*)", markup[open_lt:]).group(1)
    # Balanced scan: a nested element of the same tag must not end the block.
    depth, i = 0, open_lt
    pattern = re.compile(rf"<(/?){tag}\b", re.I)
    while True:
        m = pattern.search(markup, i)
        if not m:
            raise SystemExit(f"_repeat: unbalanced <{tag}> around {cls!r}")
        depth += -1 if m.group(1) else 1
        i = m.end()
        if depth == 0:
            end = markup.index(">", i) + 1
            break
    block = markup[open_lt:end]
    return markup[:end] + (block * (count - 1)) + markup[end:]


def fill(markup, sample):
    # Longest keys first, so 'hero-image' can never eat 'hero-image-alt'.
    for key in sorted(sample, key=len, reverse=True):
        if key.startswith("_"):
            continue
        value = str(sample[key])
        markup = re.sub(rf"<!--\s*slot\s*:\s*{re.escape(key)}\s*-->", value, markup)
        markup = markup.replace(f"slot:{key}", value)
    for token, display in FURNITURE_DISPLAY.items():
        markup = markup.replace(token, display)
    # Any furniture token left renders as a visible label rather than raw braces.
    markup = re.sub(r"\{\{\s*([^}]+?)\s*\}\}", r"[platform: \1]", markup)
    return markup


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for asset in (ROOT / "preview").glob("*.svg"):
        shutil.copy(asset, OUT / asset.name)
    tokens = {k: (ROOT / "preview" / v).read_text(encoding="utf-8")
              for k, v in TOKEN_SETS.items()}
    hub_js = (ROOT / "lib" / "hub.js").read_text(encoding="utf-8")
    cards = []
    for folder in sorted(p for p in (ROOT / "patterns").iterdir() if p.is_dir()):
        markup = (folder / "pattern.html").read_text(encoding="utf-8")
        markup = re.sub(r"\s*<!--\n.*?\n-->", "", markup, count=1, flags=re.S)
        css = (folder / "pattern.css").read_text(encoding="utf-8")
        sample = json.loads((folder / "preview-content.json").read_text(encoding="utf-8"))
        filled = fill(markup, sample)
        repeat = sample.get("_repeat")
        if repeat:
            filled = repeat_block(filled, repeat["class"], int(repeat["count"]))
        leftovers = re.findall(r"slot:[\w-]+|<!--\s*slot", filled)
        if leftovers:
            raise SystemExit(f"{folder.name}: unfilled slots in preview: {leftovers}")
        for set_name, token_css in tokens.items():
            page = SHELL.format(title=f"{folder.name} ({set_name})",
                                tokens=token_css, css=css, name=folder.name,
                                set_name=set_name, markup=filled, hub_js=hub_js)
            (OUT / f"{folder.name}--{set_name}.html").write_text(
                page, encoding="utf-8", newline="\n")
        cards.append(
            f'<li><strong>{folder.name}</strong> - '
            + ' / '.join(f'<a href="{folder.name}--{s}.html">{s}</a>'
                         for s in tokens)
            + '</li>'
        )
    index = ("<!DOCTYPE html>\n<html lang=\"en\"><head><meta charset=\"UTF-8\">"
             "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
             "<title>Pattern previews</title></head><body>"
             "<h1>Pattern previews</h1><p>Each pattern rendered on every "
             "sample token set. <strong>dark</strong> is not a style option: "
             "it is a deliberately hostile brand whose --color-heading sits "
             "at the 3:1 large-text bar, which is all the contract promises "
             "of that token. Anything that looks wrong there is a defect in "
             "the pattern, not in the preview.</p><ul>" + "".join(cards) + "</ul></body></html>\n")
    (OUT / "index.html").write_text(index, encoding="utf-8", newline="\n")
    print(f"built previews for {len(cards)} pattern(s) into {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
