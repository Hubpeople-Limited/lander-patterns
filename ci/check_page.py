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


# Height properties that can make a section claim a whole screen. The first
# version of this checked only `min-height`, so `height: 100svh` and
# `min-block-size: 100svh` - the same defect, differently spelled - went
# straight through.
HEIGHT_PROPS = r"(?:min-height|height|min-block-size|block-size)"
VIEWPORT_HEIGHT = re.compile(
    rf"(?<![-\w])({HEIGHT_PROPS})\s*:\s*([^;{{}}]*\b100(?:svh|vh|dvh|lvh)\b[^;{{}}]*)",
    re.I)

# A correct opener subtracts something that is not zero. Matching the dial's
# NAME is not enough: `calc(100svh + var(--x-above))` names it and is worse
# than the bug, and `var(--x-above, 0px)` names it and subtracts nothing.
SUBTRACTS = re.compile(
    r"calc\(\s*100(?:svh|vh|dvh|lvh)\s*-\s*var\(\s*(--[\w-]+)\s*(?:,\s*([^)]*?)\s*)?\)",
    re.I)
# The second term, and only `whole-page` patterns are held to it. Matched on
# the token's name rather than its position, because the two subtractions can
# be written in either order and neither is wrong.
SUBTRACTS_FOOTER = re.compile(
    r"-\s*var\(\s*(--[\w-]*footer[\w-]*)\s*(?:,\s*([^)]*?)\s*)?\)", re.I)
ZERO = re.compile(r"^0[a-z%]*$", re.I)


def strip_css_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def opener_fault(name, css, whole_page=False):
    """Judge one pattern's CSS as if it opened a page. Returns a list.

    A pattern that claims a whole viewport is right to do so, and wrong to
    measure it from the top of the document: a real page has a site header
    above the opener and the pattern cannot see it. What falls off the bottom
    is whatever the pattern put last, which on every opener here is the join
    control.

    A `whole-page` pattern owes a second subtraction. Its promise is that the
    PAGE is one viewport, and a page has a footer under it - injected at serve
    time on this platform, so no markup here can enclose it and no amount of
    care about the header can make the sum come out. Subtracting only the
    header put a live squeeze page 177px past an 800px viewport, 166 of them
    the footer.
    """
    bad = []
    for prop, value in VIEWPORT_HEIGHT.findall(strip_css_comments(css)):
        m = SUBTRACTS.search(value)
        if m and not ZERO.match((m.group(2) or "").strip() or "none"):
            if whole_page:
                bad += footer_fault(name, prop, value)
            continue
        if m:
            bad.append(
                f"{name} claims a whole viewport and subtracts "
                f"var({m.group(1)}, {m.group(2)}) - a zero default subtracts "
                f"nothing, so the dial exists and the fold is still wrong"
            )
            continue
        bad.append(
            f"{name} opens the page with {prop}: {value.strip()} and subtracts "
            f"nothing for what sits above it. On a page with a site header the "
            f"foot of this section - the join control - lands one header-height "
            f"below the fold. It needs "
            f"calc(100svh - var(--page-header-height, 9.5rem))"
        )
    return bad


def footer_fault(name, prop, value):
    """The second subtraction a `whole-page` pattern owes. Returns a list."""
    m = SUBTRACTS_FOOTER.search(value)
    if m and not ZERO.match((m.group(2) or "").strip() or "none"):
        return []
    if m:
        return [f"{name} is whole-page and subtracts var({m.group(1)}, "
                f"{m.group(2)}) for the footer - a zero default subtracts "
                f"nothing, so the page still scrolls by the height of it"]
    return [f"{name} is whole-page: yes and its {prop} allows for what sits "
            f"above it but not for the site footer under it. A page is not "
            f"one viewport while a footer follows it. It needs a second term "
            f"- var(--page-footer-height, 12.5rem)"]


# Patterns that legitimately claim a whole viewport without subtracting: they
# sit mid-page or at the end, where nothing is above them in the viewport by
# the time a reader arrives. Named here rather than reasoned about in prose,
# so that adding a third one is a decision somebody makes on purpose.
FULL_VIEWPORT_EXEMPT = {"cta-curtain", "pinned-cards"}


def check_opener_reserves_room(page):
    """Judge the pattern that opens the page - whichever one that is.

    The first version judged `page[0]` and stopped, which meant putting a
    heading-block or a trust-row above the hero switched the check off - and
    adding something above the opener makes the defect worse, not better. The
    opener is the first *section*; components before it do not change the fact
    that the hero is measuring from below them.
    """
    for item in page:
        if item["meta"].get("type", "").split("#")[0].strip() != "section":
            continue
        if item["name"] in FULL_VIEWPORT_EXEMPT:
            return []
        return opener_fault(item["name"], item["css"],
                            item["meta"].get("whole-page") == "yes")
    return []


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


def axes_of(meta):
    """`ground=plain|brand|deep; alignment=default|centred` -> {axis: {values}}.

    Semicolons between axes, pipes between values - not the comma every other
    metadata field uses. Splitting on commas produced an axis literally called
    "deep; alignment=default", which still rejected the one bad fixture, for
    entirely the wrong reason.
    """
    axes = {}
    for clause in (c.strip() for c in meta.get("variants", "").split(";")):
        if not clause:
            continue
        key, _, values = clause.partition("=")
        axes[key.strip()] = {v.strip() for v in values.split("|") if v.strip()}
    return axes


def check_variant_choice(page, chosen):
    """A modifier the pattern does not offer is a page that cannot be built.

    A fixture in this very file asked for `hero-stated:ground=soft`. The
    pattern declares `ground=plain|brand|deep` and ships no `--soft` rule, so
    the "real page that must stay valid" was one nobody could build. Nothing
    noticed, because an unknown key or value simply switched the ground check
    off and the run still printed a pass.
    """
    bad = []
    for item, mods in zip(page, chosen):
        axes = axes_of(item["meta"])
        for key, value in mods.items():
            if key not in axes:
                offered = ", ".join(sorted(axes)) or "none"
                bad.append(
                    f"{item['name']} has no {key!r} axis to vary - it offers: {offered}"
                )
            elif value not in axes[key]:
                bad.append(
                    f"{item['name']} has no {key}={value} - it offers "
                    f"{key}={'|'.join(sorted(axes[key]))}"
                )
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


def apply_variants(name, meta, body, mods):
    """Swap the chosen modifier class in for the one the markup ships.

    Swap, do not append. The markup already ships a default -
    `class="hero-stated hero-stated--plain"` - so appending leaves both on
    the element and lets source order decide, which is not a choice anybody
    made. The first version of assemble() appended, and every rung rendered
    as the default while the checks reasoned about the rung you asked for.

    Shared with ci/compose.py, which builds the same markup into shells and
    must make the same swap or its pages would contradict their manifests.
    """
    for key, value in mods.items():
        swapped = False
        for known in sorted(axes_of(meta).get(key, ())):
            old = f'{name}--{known}'
            if old in body:
                body = body.replace(old, f'{name}--{value}')
                swapped = True
                break
        if not swapped:
            body = re.sub(
                r'(class="[^"]*\b' + re.escape(name) + r')(")',
                r'\1 ' + f'{name}--{value}' + r'\2', body, count=1)
    return body


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


def assemble(page, chosen):
    """Build the page the recipe actually asked for.

    The first version ignored the modifiers, so a recipe naming
    `hero-stated:ground=deep` was checked as deep and rendered as the default -
    the artifact you were told to open contradicted the thing you were told
    about it.
    """
    css = []
    markup = []
    for item, mods in zip(page, chosen):
        css.append(f"/* ---- {item['name']} ---- */\n{item['css']}")
        # The pattern's own markup, comments and all. They are stripped at the
        # END of this loop, not here: a content slot IS an HTML comment
        # (`<!-- slot: title -->`), so stripping first deletes the very thing
        # fill() looks for, and every assembled page renders with empty
        # headings. The library's own rule 4 says to strip in the same pass
        # that fills; this function had it backwards from the day it was
        # written, and nothing caught it because no gate reads the artifact.
        body = item["html"]
        repeat = item["sample"].get("_repeat")
        if repeat:
            body = repeat_block(body, repeat["class"], repeat["count"])
        body = apply_variants(item["name"], item["meta"], body, mods)
        # Fill first, then strip whatever comments remain - the metadata
        # header and the notes to whoever places the pattern, none of which
        # belongs to the reader.
        markup.append(strip_comments(fill(body, item["sample"])))
    return "\n".join(css), "\n".join(markup)


# ------------------------------------------------------------------- runner

def sweep():
    """Every pattern in the library, judged as if it opened a page.

    The recipes cannot carry this. A fixture proves something about the
    compositions somebody thought to write down, and the first version of this
    file left thirty of forty-four patterns in no fixture at all - so the fold
    rule, written for a defect that reached a live site, was enforced on five
    openers and silent on the rest while the suite printed "clean".

    The rule does not actually need a page: a pattern that claims a whole
    viewport and subtracts nothing is wrong wherever it lands, unless it is one
    of the few that never has anything above it. So sweep the library and hold
    every pattern to it.
    """
    bad = []
    for folder in sorted(PATTERNS.iterdir()):
        if not folder.is_dir() or folder.name in FULL_VIEWPORT_EXEMPT:
            continue
        css_path = folder / "pattern.css"
        if not css_path.exists():
            continue
        html_path = folder / "pattern.html"
        meta = parse_meta(html_path.read_text(encoding="utf-8")) \
            if html_path.exists() else {}
        bad += opener_fault(folder.name, css_path.read_text(encoding="utf-8"),
                            meta.get("whole-page") == "yes")
    return bad


def main():
    if "--sweep" in sys.argv:
        bad = sweep()
        exempt = ", ".join(sorted(FULL_VIEWPORT_EXEMPT))
        print(f"sweep: every pattern judged as an opener (exempt: {exempt})")
        print()
        for line in bad:
            print(f"  FAIL  [the fold] {line}")
        if not bad:
            print(f"  clean: {sum(1 for f in PATTERNS.iterdir() if f.is_dir())} "
                  f"pattern(s), none claims a viewport it does not measure")
        return 1 if bad else 0

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
        ("variant", check_variant_choice(page, chosen)),
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
        css, markup = assemble(page, chosen)
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
