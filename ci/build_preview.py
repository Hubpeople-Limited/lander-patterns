#!/usr/bin/env python3
"""Assemble static preview pages: every pattern x every sample token set,
and every composition shell rendered as a whole page.

Output goes to preview/site/ (gitignored; published by CI). This is repo
tooling only - the inline <style> it writes exists nowhere but the preview.

The two halves have different jobs and are built differently on purpose.

A **pattern** preview exists to make a defect visible. It renders on all five
token sets, including the two that are deliberately hostile, and it uses the
flat grey sample images, because a photograph in an image slot hides the very
layout fault the render was built to show.

A **shell** preview exists to show what a page built from this library looks
like. It renders on the four token sets a real brand could plausibly ship, and
it uses the placeholder set the library already gives partners
(`lib/placeholders/`), because that is what a page genuinely looks like before
the brand's photography arrives.
"""
import json
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "preview" / "site"
# Named rather than globbed, so the preview index can say what each one is
# for and the order is the order a reviewer should read them in. `display` is
# last because it is the one to look at when something looks wrong on the
# other four and you cannot see why.
TOKEN_SETS = {"soft": "tokens-soft.css", "sharp": "tokens-sharp.css",
              "dark": "tokens-dark.css", "brand": "tokens-brand.css",
              "display": "tokens-display.css"}

# Shells render on these four. `display` is left out deliberately: it is a
# hostile type fixture built to break patterns, and a wall of pages meant to
# show what this library can do is not where anyone should meet it. Every
# pattern inside a shell is still rendered on `display` in its own preview,
# so nothing stops being checked.
SHELL_TOKEN_SETS = ("soft", "sharp", "dark", "brand")

# The shipped placeholder set, copied in beside the shell renders. The three
# shapes are the ones the photography patterns ask for; lib/placeholders/
# README.md is the contract.
SHELL_IMAGES = {"wide.svg": "placeholder-wide.svg",
                "landscape.svg": "placeholder-landscape.svg",
                "portrait.svg": "placeholder-portrait.svg"}

# Sample values carry the flat CI images. On a shell they are swapped for the
# placeholder of the same shape - see this module's docstring for why the two
# halves do not share an image set.
SHELL_IMAGE_SWAP = {"sample-wide.svg": "placeholder-wide.svg",
                    "sample-portrait.svg": "placeholder-portrait.svg"}

# compose.py writes one of these above every section it places, and it is the
# only thing on a shell page that says which pattern a run of markup came
# from. Changing its format there breaks the fill here, loudly.
SECTION_BANNER = re.compile(
    r"<!--\s*=+\s*\n\s*section \d+ of \d+ : ([\w-]+) v", re.M)

# Display stand-ins so furniture tokens render readably in previews. These
# substitutions exist only here; pattern files always keep the real tokens.
#
# The menu one is markup rather than a word, because for a header pattern the
# generated list IS the thing being styled and a preview that cannot show it
# cannot show a fault in it. It carries what the platform actually emits: plain
# items, a parent with children and no URL of its own, and the PAIR of <li>
# entries a parent with both children and a URL comes through as.
SAMPLE_MENU = (
    '<ul class="canvas-navigation-menu">'
    '<li><a href="#sample" title="Sample" target="_self">Sample one</a></li>'
    '<li><a href="#sample" title="Sample" target="_self">Sample two</a></li>'
    '<li class="has-submenu"><a>Sample group</a>'
    '<ul class="canvas-navigation-submenu">'
    '<li><a href="#sample" title="Sample" target="_self">Sample child</a></li>'
    '<li><a href="#sample" title="Sample" target="_self">Sample child two</a></li>'
    '</ul></li>'
    '<li><a href="#sample" title="Sample" target="_self">Sample paired</a></li>'
    '<li class="has-submenu"><a>Sample paired</a>'
    '<ul class="canvas-navigation-submenu">'
    '<li><a href="#sample" title="Sample" target="_self">Sample child three</a></li>'
    '</ul></li>'
    '</ul>'
)

# The footer menu, for the same reason as the header one: `{{menu.footer}}`
# sits in body position inside colophon's nav, so with no stand-in it renders
# as the visible text "[platform: menu.footer]" - which reads as a broken page
# rather than as a token, and reads that way on a public preview. colophon's
# CSS deliberately targets elements under .colophon-menu rather than any
# generated class, because the platform owns this markup, so a plain list is
# the honest stand-in.
SAMPLE_FOOTER_MENU = (
    '<ul class="canvas-navigation-menu">'
    '<li><a href="#sample" title="Sample" target="_self">Sample link</a></li>'
    '<li><a href="#sample" title="Sample" target="_self">Sample link two</a></li>'
    '<li><a href="#sample" title="Sample" target="_self">Sample link three</a></li>'
    '</ul>'
)

FURNITURE_DISPLAY = {
    "{{join.url}}": "#",
    "{{login.url}}": "#",
    "{{menu.footer}}": SAMPLE_FOOTER_MENU,
    "{{footerLinks.privacyPolicyUrl}}": "#",
    "{{footerLinks.termsAndConditionsUrl}}": "#",
    "{{footerLinks.cookiesUrl}}": "#",
    "{{footerLinks.antiSlaveryPolicyUrl}}": "#",
    "{{join.text}}": "Join sample",
    "{{login.text}}": "Log in sample",
    "{{logo.src}}": "sample-wordmark.svg",
    "{{logo.alt}}": "Sample brand wordmark",
    "{{menu.navigation}}": SAMPLE_MENU,
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
<!-- lib/hub.js is copied in beside these pages and referenced, never inlined.
     Inlining it put a literal </script> from its own header comment into the
     document: the HTML tokenizer does not read JavaScript comments, so that
     string ended the element and the rest of the file rendered as body text.
     Referencing it is also how a real page gets it. -->
<script type="module" src="hub.js"></script>
</body>
</html>
"""


# A shell renders as a whole page and carries no preview note, unlike a
# pattern render. The note is a band of content, and several openers reserve
# the viewport minus the page furniture - putting a band above one pushes the
# hero down by exactly the height of the thing that is not on a real page, so
# the demo would show an overflow no partner will ever see. The <title> says
# it is a sample instead, and the index says it around them.
SHELL_PAGE = """<!DOCTYPE html>
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
{css}
</style>
</head>
<body>
{markup}
<script type="module" src="hub.js"></script>
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


def strip_comments(text):
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def shell_sections(body):
    """Split a shell body into (pattern name, markup) pairs.

    A shell concatenates several patterns and their slot names collide - two
    sections both carrying `eyebrow` and `section-title` is the norm here, not
    the exception. Filling the whole document from one dictionary would put the
    opener's sample copy into the steps section and nothing would say it had.
    The banner compose.py writes above each section names the pattern the
    markup came from, so each section is filled from that pattern's own sample.
    """
    marks = [(m.start(), m.group(1)) for m in SECTION_BANNER.finditer(body)]
    if not marks:
        raise SystemExit(
            "shell: no section banners found - has compose.py's banner changed?")
    bounds = [m[0] for m in marks] + [len(body)]
    return [(name, body[bounds[i]:bounds[i + 1]])
            for i, (_, name) in enumerate(marks)]


def build_shell(folder):
    """Fill one composition shell and return its body markup, ready to render."""
    page = (folder / "page.html").read_text(encoding="utf-8")
    inside = re.search(r"<body>(.*)</body>", page, re.S)
    if not inside:
        raise SystemExit(f"{folder.name}: no <body> in page.html")

    pieces, patterns = [], []
    for name, markup in shell_sections(inside.group(1)):
        sample_file = ROOT / "patterns" / name / "preview-content.json"
        if not sample_file.exists():
            raise SystemExit(f"{folder.name}: {name} has no preview-content.json")
        sample = json.loads(sample_file.read_text(encoding="utf-8"))
        filled = fill(markup, sample)
        repeat = sample.get("_repeat")
        if repeat:
            filled = repeat_block(filled, repeat["class"], int(repeat["count"]))
        pieces.append(filled)
        patterns.append(name)

    # After the fill, never before: a slot marker IS a comment, and stripping
    # first would delete the thing being filled. The shell's own instruction
    # banner talks about `slot: name` in prose, so the leftover scan below
    # would also read that as an unfilled slot if it ran on the raw document.
    body = strip_comments("\n".join(pieces))
    for old, new in SHELL_IMAGE_SWAP.items():
        body = body.replace(old, new)

    leftovers = re.findall(r"slot:[\w-]+|<!--\s*slot", body)
    if leftovers:
        raise SystemExit(f"{folder.name}: unfilled slots in shell: {sorted(set(leftovers))}")

    # Two patterns can carry the same sample id and a page with a repeated id
    # is invalid, which nothing else here would notice. It has not happened
    # yet; this is what says so when it does.
    ids = re.findall(r'\bid="([^"]+)"', body)
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise SystemExit(f"{folder.name}: duplicate id(s) in shell: {dupes}")

    return body, patterns


# The wall's thumbnails are the shell pages themselves, live, shrunk. Not
# screenshots: an image set would need a browser in the build, somewhere to
# put the files, and a regeneration every time a pattern moves, and it would
# be wrong between those runs. An iframe at 400% of its frame scaled to a
# quarter is exactly the frame's width, at any frame width, with no script -
# which matters, because the script gate at the end of main() refuses any
# script element on a generated page that is not an empty src reference.
INDEX_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lander patterns - previews</title>
<style>
:root {{
  --ink: #1b1f23; --soft-ink: #5b646c; --bg: #ffffff; --panel: #f5f4f1;
  --line: #dcdad4; --link: #1f5f6b;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --ink: #e9e7e2; --soft-ink: #a3a9ae; --bg: #14171a; --panel: #1e2226;
    --line: #333a40; --link: #7fc4d1;
  }}
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0 auto; padding: 3rem 1.5rem 6rem; max-width: 76rem;
  background: var(--bg); color: var(--ink); line-height: 1.6;
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }}
h1 {{ font-size: clamp(1.8rem, 1.3rem + 2vw, 2.6rem); line-height: 1.15;
  letter-spacing: -0.02em; margin: 0 0 .5rem; }}
h2 {{ font-size: 1.35rem; letter-spacing: -0.01em; margin: 3.5rem 0 .35rem;
  padding-top: 2rem; border-top: 1px solid var(--line); }}
h2:first-of-type {{ border-top: 0; padding-top: 0; }}
p {{ max-width: 46rem; color: var(--soft-ink); margin: 0 0 1rem; }}
p.lede {{ color: var(--ink); font-size: 1.05rem; }}
a {{ color: var(--link); }}
code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: .9em; background: var(--panel); padding: .1em .35em;
  border-radius: .25rem; }}
.tag {{ display: inline-block; font-size: .78rem; letter-spacing: .04em;
  text-transform: uppercase; color: var(--soft-ink); border: 1px solid var(--line);
  border-radius: 999px; padding: .1rem .6rem; vertical-align: .12em; }}
.wall {{ display: grid; gap: 1.75rem; margin: 2rem 0 0; padding: 0; list-style: none;
  grid-template-columns: repeat(auto-fill, minmax(19rem, 1fr)); }}
.tile {{ display: block; text-decoration: none; color: inherit; }}
.frame {{ display: block; position: relative; aspect-ratio: 4 / 3;
  overflow: hidden; background: var(--panel); border: 1px solid var(--line);
  border-radius: .5rem; }}
.frame iframe {{ position: absolute; inset: 0; width: 400%; height: 400%;
  border: 0; transform: scale(.25); transform-origin: 0 0;
  pointer-events: none; }}
.tile:hover .frame, .tile:focus-visible .frame {{ border-color: var(--link); }}
.tile b {{ display: block; margin: .7rem 0 .15rem; font-size: 1rem; }}
.tile span {{ display: block; font-size: .85rem; color: var(--soft-ink); }}
.sets {{ margin: .3rem 0 0; font-size: .85rem; }}
ul.patterns {{ list-style: none; padding: 0; margin: 1.5rem 0 0; }}
ul.patterns li {{ padding: .55rem 0; border-bottom: 1px solid var(--line);
  display: flex; flex-wrap: wrap; gap: .35rem 1rem; align-items: baseline; }}
ul.patterns b {{ min-width: 12rem; font-weight: 600; }}
ul.patterns .sets {{ margin: 0; }}
</style>
</head>
<body>
<h1>Lander patterns</h1>
<p class="lede">Sample renders of the pattern library at <code>{tag}</code>. Every
page here is built from the library and filled with sample copy and placeholder
images. None of it is a real brand.</p>

<h2>Pages <span class="tag">{shell_count} shells</span></h2>
<p>Whole pages, pre-assembled from the patterns below and generated by
<code>ci/compose.py</code> from <code>ci/page-recipes.json</code>. Each is shown on
four sample token sets, which is the same page with a different brand's colours,
typefaces and corners. The photography is the placeholder set from
<code>lib/placeholders/</code>, which is what a page looks like before a brand's
own images arrive.</p>
<ul class="wall">
{wall}
</ul>

<h2>Patterns <span class="tag">{pattern_count}</span></h2>
<p>Each pattern on its own, rendered on every sample token set. Two of the five
are not style options. <strong>dark</strong> is a deliberately hostile brand whose
<code>--color-heading</code> sits at the 3:1 large-text bar, which is all the
contract promises of that token. <strong>display</strong> is a deliberately hostile
brand whose heading face carries a digit 42% wider than Georgia's and a line box
57% taller, Georgia being the face most of this library was designed against.
Anything that looks wrong on either is a defect in the pattern, not in the
preview.</p>
<ul class="patterns">
{patterns}
</ul>
</body>
</html>
"""


def release_tag():
    """The tag these pages will be published as, not the one already released.

    `LATEST` is the wrong answer here and said so on the live site: this build
    runs in the validate job, and the release job writes the new LATEST and cuts
    the tag afterwards - so on a push to main the file still holds the previous
    release, and the index published from that run claimed a version one behind
    the library it was rendering. The tag is `v` plus the run number, in the
    release job and here, from the same variable.

    Off CI there is no run number and no release, so the local build says what
    is on disk. That is honest: a local preview IS the working tree.
    """
    run = os.environ.get("GITHUB_RUN_NUMBER")
    if run and os.environ.get("GITHUB_REF") == "refs/heads/main":
        return f"v{run}"
    if run:
        # A pull-request run publishes nothing and cuts no tag, so naming the
        # run number would invent a release that will never exist.
        return (ROOT / "LATEST").read_text(encoding="utf-8").strip() + " plus this branch"
    return (ROOT / "LATEST").read_text(encoding="utf-8").strip() + " (working tree)"


def build_index(shells, cards, tag):
    default_set = SHELL_TOKEN_SETS[0]
    tiles = []
    for shell in shells:
        name = shell["name"]
        sets = " / ".join(
            f'<a href="shell-{name}--{s}.html">{s}</a>' for s in SHELL_TOKEN_SETS)
        tiles.append(
            f'<li><a class="tile" href="shell-{name}--{default_set}.html">'
            f'<span class="frame"><iframe src="shell-{name}--{default_set}.html" '
            f'loading="lazy" tabindex="-1" aria-hidden="true" '
            f'title="{name} preview"></iframe></span>'
            f'<b>{name}</b><span>{shell["page"]} &middot; '
            f'{" &rarr; ".join(shell["patterns"])}</span></a>'
            f'<p class="sets">{sets}</p></li>')
    return INDEX_PAGE.format(
        tag=tag, shell_count=len(shells), pattern_count=len(cards),
        wall="\n".join(tiles), patterns="\n".join(cards))


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for asset in (ROOT / "preview").glob("*.svg"):
        shutil.copy(asset, OUT / asset.name)
    for source, name in SHELL_IMAGES.items():
        shutil.copy(ROOT / "lib" / "placeholders" / source, OUT / name)
    shutil.copy(ROOT / "lib" / "hub.js", OUT / "hub.js")
    tokens = {k: (ROOT / "preview" / v).read_text(encoding="utf-8")
              for k, v in TOKEN_SETS.items()}
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
                                set_name=set_name, markup=filled)
            (OUT / f"{folder.name}--{set_name}.html").write_text(
                page, encoding="utf-8", newline="\n")
        cards.append(
            f'<li><b>{folder.name}</b><span class="sets">'
            + ' / '.join(f'<a href="{folder.name}--{s}.html">{s}</a>'
                         for s in tokens)
            + '</span></li>'
        )

    shells = []
    composition_dir = ROOT / "compositions"
    for folder in sorted(p for p in composition_dir.iterdir() if p.is_dir()):
        body, patterns = build_shell(folder)
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        # The manifest is what a consumer pins against and the banners are what
        # this build read. If they ever disagree, one of them is lying about
        # what is on the page and there is no way to tell which from the render.
        named = [p["name"] for p in manifest["patterns"]]
        if named != patterns:
            raise SystemExit(
                f"{folder.name}: manifest says {named}, the page banners say {patterns}")
        css = (folder / "page.css").read_text(encoding="utf-8")
        for set_name in SHELL_TOKEN_SETS:
            page = SHELL_PAGE.format(
                title=f"{folder.name} on {set_name} - sample page",
                tokens=tokens[set_name], css=css, markup=body)
            (OUT / f"shell-{folder.name}--{set_name}.html").write_text(
                page, encoding="utf-8", newline="\n")
        shells.append({"name": folder.name, "page": manifest["page"],
                       "patterns": patterns})
    (OUT / "index.html").write_text(
        build_index(shells, cards, release_tag()),
        encoding="utf-8", newline="\n")
    # Every script element on a generated page must be empty and carry a src.
    # Inlining a script body once put a literal closing-script string from
    # hub.js's own header comment into the document; the HTML tokenizer does
    # not read JavaScript comments, so it ended the element there and the rest
    # of the file rendered as visible body text on every preview. Nothing
    # caught it because the preview site had never been published.
    bad = []
    for page in sorted(OUT.glob("*.html")):
        text = page.read_text(encoding="utf-8")
        for m in re.finditer(r"<script\b([^>]*)>(.*?)</script\s*>", text, re.S | re.I):
            if m.group(2).strip() or "src=" not in m.group(1):
                bad.append(f"{page.name}: a script element is not an empty src reference")
    if bad:
        raise SystemExit("preview: " + "; ".join(sorted(set(bad))[:3]))

    print(f"built previews for {len(cards)} pattern(s) and {len(shells)} shell(s) "
          f"into {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
