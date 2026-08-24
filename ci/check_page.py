#!/usr/bin/env python3
"""Check patterns as neighbours on one page, rather than one at a time.

Every other gate in this repo measures a pattern **in isolation** - its tokens,
its contrast, its markup, its render against a token set. That is the right
shape for most defects and it is blind to a whole family of others, because a
pattern has no page: it cannot know what sits above it, what follows it, or
what the reader has already been shown by the time they arrive.

The defect that made the case for this file shipped through every gate the
library had. `hero-overlay` set `min-height: 100svh`, which is correct for a
pattern and wrong for a page: measured from below a site header, it put the
join control exactly one header-height below the fold. Nothing caught it. It
took a screenshot of a browser.

    python ci/check_page.py homepage hero-overlay stats-band cta-band
    python ci/check_page.py homepage hero-stated:ground=deep listing-rows:ground=soft
    python ci/check_page.py homepage hero-overlay stats-band --brand ../brand/site/global.css --out /tmp/page

A recipe is a page type followed by the patterns in the order they appear.
A pattern may carry its chosen variant after a colon - `hero-stated:ground=deep`
- which is the same modifier the page would actually be built with, and some
checks can say nothing useful without it.

With `--brand` the assembled page links that stylesheet ahead of the pattern
CSS, in the order a real brand gets, so the output is worth opening in a
browser as well as reading. Reads only; nothing is written unless `--out` is
given.

Exit codes: 0 all checks passed, 1 at least one failed, 2 the recipe itself is
unusable (an unknown pattern, an empty page).
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
PATTERNS = ROOT / "patterns"

from build_preview import fill, repeat_block          # noqa: E402


# ---------------------------------------------------------------- the recipe

def parse_meta(text):
    """The pattern's own metadata header. A local copy on purpose.

    lint.py has one of these, but its version records a failure against the
    linter's global state when a header is missing, which is right for the
    linter and wrong here: this script must be able to report a bad pattern as
    a recipe problem rather than half-failing somebody else's run.
    """
    m = re.match(r"\s*<!--\n(.*?)\n-->", text, re.S)
    if not m:
        return {}
    meta = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta


def parse_recipe(items):
    """`name` or `name:key=value,key=value` into (name, {key: value})."""
    out = []
    for item in items:
        name, _, mods = item.partition(":")
        chosen = {}
        for pair in filter(None, (p.strip() for p in mods.split(","))):
            key, _, value = pair.partition("=")
            if not value:
                return None, f"{item}: a modifier needs key=value, got {pair!r}"
            chosen[key.strip()] = value.strip()
        out.append((name.strip(), chosen))
    return out, None


def load(name):
    folder = PATTERNS / name
    if not folder.is_dir():
        return None, f"no pattern called {name!r} in patterns/"
    html = (folder / "pattern.html").read_text(encoding="utf-8")
    css = (folder / "pattern.css").read_text(encoding="utf-8")
    meta = parse_meta(html)
    if not meta.get("name"):
        return None, f"{name}: no usable metadata header"
    sample_path = folder / "preview-content.json"
    sample = json.loads(sample_path.read_text(encoding="utf-8")) if sample_path.exists() else {}
    return {"name": name, "html": html, "css": css, "meta": meta, "sample": sample}, None


def listed(meta, key):
    """The comma list under `key`, with the library's "nothing here" spellings
    dropped. `requires: none` and `motion: none` are how a pattern says it has
    no requirement, so treating `none` as the name of one produces a page
    report demanding the brand supply some none."""
    values = [v.strip() for v in meta.get(key, "").split(",") if v.strip()]
    return [v for v in values if v.lower() != "none"]


# ---------------------------------------------------------------- the checks
#
# Each check takes the loaded page and returns a list of failures. A failure is
# a sentence saying what is wrong with THIS page - never a rule restated, and
# never a complaint about a pattern on its own, which is the other gates' job.

def check_known_page_type(page, page_type):
    bad = []
    for item in page:
        types = listed(item["meta"], "page-types")
        if types and page_type not in types:
            bad.append(
                f"{item['name']} is not for a {page_type}: its page-types are "
                f"{', '.join(types)}"
            )
    return bad


def check_one_per_page(page):
    seen = {}
    bad = []
    for item in page:
        if item["meta"].get("one-per-page", "").split("#")[0].strip() != "yes":
            continue
        if item["name"] in seen:
            bad.append(
                f"{item['name']} is marked one-per-page and appears "
                f"{sum(1 for i in page if i['name'] == item['name'])} times"
            )
        seen[item["name"]] = True
    return sorted(set(bad))


def check_avoid_with(page):
    names = [item["name"] for item in page]
    # The field is mutual, so a collision is found from both ends. Report it
    # once, by the pair, or a page with two openers reads as four faults.
    pairs = {}
    for item in page:
        for other in listed(item["meta"], "avoid-with"):
            if other in names and other != item["name"]:
                pairs.setdefault(tuple(sorted((item["name"], other))), set()).add(item["name"])
    return [
        f"{a} and {b} are on the same page, and "
        f"{' and '.join(sorted(who))}'s avoid-with names the other"
        for (a, b), who in sorted(pairs.items())
    ]


VIEWPORT_MIN_HEIGHT = re.compile(
    r"min-height\s*:\s*([^;}]*\b100(?:svh|vh|dvh)\b[^;}]*)", re.I)


def check_opener_reserves_room(page):
    """The fold bug, as a rule a machine can hold you to.

    A pattern that claims a whole viewport is right to do so - and wrong to
    measure it from the top of the document, because a real page has a site
    header above the opener and the pattern cannot see it. What falls off the
    bottom is whatever the pattern put last, which on every opener here is the
    join control.

    Only the first pattern is judged. `cta-curtain` and `pinned-cards` claim a
    full viewport too and are correct with a plain 100svh: they sit mid-page
    and at the end, where nothing is above them by the time a reader arrives.
    """
    if not page:
        return []
    first = page[0]
    bad = []
    for value in VIEWPORT_MIN_HEIGHT.findall(first["css"]):
        if f"--{first['name']}-above" in value:
            continue
        bad.append(
            f"{first['name']} opens the page with min-height: {value.strip()} "
            f"and subtracts nothing for what sits above it. On a page with a "
            f"site header the foot of this section - the join control - lands "
            f"one header-height below the fold. It needs "
            f"calc(100svh - var(--{first['name']}-above, 4.5rem))"
        )
    return bad


HEADING = re.compile(r"<h([1-6])\b", re.I)


def check_headings(page):
    """One h1, and no level skipped as the reader moves down the page.

    Every pattern is a valid fragment on its own - a section starting at h2 is
    correct in isolation. Whether the page has exactly one h1, and whether the
    join between two patterns skips a level, is only answerable once they are
    neighbours, which is the whole point of this file.
    """
    levels = []
    for item in page:
        for lvl in HEADING.findall(strip_comments(item["html"])):
            levels.append((int(lvl), item["name"]))

    bad = []
    ones = [name for lvl, name in levels if lvl == 1]
    if len(ones) == 0:
        bad.append("the page has no h1 - nothing states what it is about")
    elif len(ones) > 1:
        bad.append(f"the page has {len(ones)} h1s, in {', '.join(ones)} - a page has one")

    previous = None
    for lvl, name in levels:
        if previous is not None and lvl > previous + 1:
            bad.append(
                f"heading level jumps h{previous} to h{lvl} at {name} - "
                f"a reader using headings to move loses the level in between"
            )
        previous = lvl
    return bad


def check_ground_run(page, chosen):
    """Two full-bleed sections landing on the same ground read as one section.

    This is the "it all runs together" complaint in a form a machine can see,
    and it is only visible between neighbours. Where a ground was not chosen in
    the recipe nothing is claimed: a pattern's default is a property of the
    pattern, and guessing it here would produce confident nonsense.
    """
    bad = []
    unknown = []
    previous = None
    for item, mods in zip(page, chosen):
        varies = listed(item["meta"], "variants") or listed(item["meta"], "varies")
        ground = mods.get("ground")
        if ground is None:
            if any(v.startswith("ground") for v in varies):
                unknown.append(item["name"])
            previous = None
            continue
        if previous and previous[1] == ground:
            bad.append(
                f"{previous[0]} and {item['name']} are next to each other and "
                f"both on the {ground} ground - with nothing between them they "
                f"read as one long section"
            )
        previous = (item["name"], ground)
    return bad, unknown


def check_behaviours(page):
    """Not a failure. What the page needs carrying, said once, out loud."""
    brings = {}
    for item in page:
        for b in listed(item["meta"], "behaviours"):
            brings.setdefault(b, []).append(item["name"])
    return brings


def check_requires(page):
    """Also not a failure - a recipe cannot know what material a brand has."""
    needs = {}
    for item in page:
        for r in listed(item["meta"], "requires"):
            needs.setdefault(r, []).append(item["name"])
    return needs


def check_deprecated(page):
    bad = []
    for item in page:
        if item["meta"].get("status", "").split("#")[0].strip() == "deprecated":
            replaced = item["meta"].get("replaced-by", "").strip()
            tail = f" - use {replaced} instead" if replaced else ""
            bad.append(f"{item['name']} is deprecated{tail}")
    return bad


# ------------------------------------------------------------- the assembly

def strip_comments(text):
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


PAGE = """<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
{brand_link}
<style>
/* A stand-in site header. Not part of any pattern - it is here because the
   defect this file exists for only appears when something sits above the
   opener, and a page with no header cannot show it. */
.page-check-header {{ display: flex; align-items: center; gap: 1rem;
  padding: .75rem 1.5rem; min-height: 4.5rem; box-sizing: border-box;
  border-bottom: 1px solid rgba(128,128,128,.35); font: 600 1rem system-ui; }}
.page-check-header span {{ margin-left: auto; font-weight: 400; opacity: .7; }}
</style>
<style>{css}</style>
<body>
<header class="page-check-header">{title}<span>assembled by ci/check_page.py</span></header>
{markup}
</body>
</html>
"""


def assemble(page):
    css = []
    markup = []
    for item in page:
        css.append(f"/* ---- {item['name']} ---- */\n{item['css']}")
        body = strip_comments(item["html"])
        repeat = item["sample"].get("_repeat")
        if repeat:
            body = repeat_block(body, repeat["class"], repeat["count"])
        markup.append(fill(body, item["sample"]))
    return "\n".join(css), "\n".join(markup)


# ------------------------------------------------------------------- runner

def main():
    ap = argparse.ArgumentParser(
        description="Check patterns as neighbours on one page.")
    ap.add_argument("page_type", help="homepage, landing, pricing, safety, article, features")
    ap.add_argument("patterns", nargs="+",
                    help="the patterns in page order; name or name:ground=deep")
    ap.add_argument("--brand", help="a real brand's global.css to assemble against")
    ap.add_argument("--out", help="directory to write the assembled page into")
    args = ap.parse_args()

    recipe, err = parse_recipe(args.patterns)
    if err:
        print(f"recipe: {err}")
        return 2

    page, chosen = [], []
    for name, mods in recipe:
        item, err = load(name)
        if err:
            print(f"recipe: {err}")
            return 2
        page.append(item)
        chosen.append(mods)

    print(f"{args.page_type}: {' -> '.join(i['name'] for i in page)}\n")

    failures = []
    for label, found in (
        ("page type", check_known_page_type(page, args.page_type)),
        ("deprecated", check_deprecated(page)),
        ("one per page", check_one_per_page(page)),
        ("avoid-with", check_avoid_with(page)),
        ("the fold", check_opener_reserves_room(page)),
        ("headings", check_headings(page)),
    ):
        for line in found:
            failures.append((label, line))

    ground_bad, ground_unknown = check_ground_run(page, chosen)
    for line in ground_bad:
        failures.append(("ground", line))

    for label, line in failures:
        print(f"  FAIL  [{label}] {line}")

    if not failures:
        print("  all page-level checks passed")

    brings = check_behaviours(page)
    if brings:
        print()
        for name, owners in sorted(brings.items()):
            print(f"  carries  {name} (from {', '.join(owners)}) - this page needs hub.js")

    needs = check_requires(page)
    if needs:
        print()
        for name, owners in sorted(needs.items()):
            print(f"  needs    {name} (for {', '.join(owners)}) - the brand must have it")

    if ground_unknown:
        print()
        print(f"  unstated ground on {', '.join(ground_unknown)} - pass "
              f"name:ground=<rung> to check the run between neighbours")

    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        css, markup = assemble(page)
        brand_link = ""
        if args.brand:
            (out / "brand.css").write_text(
                Path(args.brand).read_text(encoding="utf-8"), encoding="utf-8")
            brand_link = '<link rel="stylesheet" href="brand.css">'
        title = f"{args.page_type}: " + " + ".join(i["name"] for i in page)
        (out / "page.html").write_text(
            PAGE.format(title=title, brand_link=brand_link, css=css, markup=markup),
            encoding="utf-8")
        print(f"\n  wrote {out / 'page.html'} - open it, and look at the first screen")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
