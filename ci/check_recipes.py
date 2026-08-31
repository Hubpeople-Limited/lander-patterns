#!/usr/bin/env python3
"""Hold every page recipe to its grammar, and regenerate the menu from them.

A composition is a THING - page markup, assembled and maintained. A recipe is
the order sheet above it: which shell, which ground each band sits on, how the
page opens and closes, the structural signature it commits to, and the slot
where a brand's own typeface pairing arrives. Two brands taking `pricing` get
the same shell and, with two different recipes, genuinely different pages.

That only holds while the recipes stay machine-readable, and the failure mode
is quiet. A recipe naming a shell that no longer exists still reads perfectly
to a person. So does one whose `grounds` list has four rungs for a five-band
shell - the fifth band simply arrives with nobody having decided anything about
it, which is the design round the recipe existed to save. So does a recipe that
pins `shell: pricing@3`, right up to the release where `pricing@4` lands and the
menu quietly offers last month's page. None of that is visible by reading.

    python ci/check_recipes.py             check, and rewrite recipes/README.md
    python ci/check_recipes.py --check     fail if the committed README differs
    python ci/check_recipes.py --broken    the positive control, below

WHAT IT CHECKS. The fenced `recipe` block: the fields present, in order, none
unknown, none repeated, no blank line inside the fence. A pin that matches its
own filename, and no two recipes sharing one. A `shape` from the seven the
building vocabulary has and no eighth. A `shell` that is a real folder under
`compositions/`, named WITHOUT its version. A `look` entry naming a real
pattern, also without a version, and an `axis=value` that pattern actually
declares - read through `ci/check_page.py`'s own `axes_of`, so the recipes and
the page checker can never disagree about what a pattern offers. A `grounds`
list as long as the shell has bands. A `signature` of ten words or fewer, and
`pairing: brand`, which is a slot rather than a value.

WHAT IT DELIBERATELY DOES NOT CHECK, and each of these is a judgement rather
than an oversight:

- Whether two recipes on one shell are different enough to both be worth
  offering. That is the entire value of the layer and no machine can see it.
  It is a review question, and the menu is short enough to read.
- The words in `opens`, `closes` and `notes`. They are one line of plain
  language for somebody choosing, and a vocabulary rule over them would either
  be trivially satisfied or would start rejecting good sentences.
- Whether a ground run reads well - whether two neighbouring bands landing on
  the same rung run together. `ci/check_page.py` answers that about a page it
  can see the markup of; here there is only a rung list, and a rule that cannot
  tell a considered repeat from a careless one is a rule that gets switched off.
- A ground restated in `look`. `grounds` owns the ground run and `look` carries
  the other dials, but `ground` is a legal axis on eight patterns, so failing it
  here would mean this gate holding an opinion the pattern metadata does not.
  CONTRIBUTING.md states the convention; two descriptions of one ground would
  drift, and the review that spots it is cheaper than the false positives.

BANDS EXCLUDE THE FURNITURE. A shell carries `masthead-nav` at the top and
`colophon` at the foot, and both are brand-level - settled once for a site, not
per page. A recipe restating them would be a second copy of a decision already
made, so `grounds` runs from the first real band to the last and the count here
does the same.

THE POSITIVE CONTROL. `--broken` runs synthetic recipes - one per fault this
file can report - through the same code path the real ones take, and requires
every fault to fire. It also runs a valid recipe through and requires silence,
because a gate that rejects everything catches nothing either. Exit 0 on that
run means every fault was detected. The fixtures live in this file rather than
in `recipes/`: a broken recipe committed to the menu is a broken recipe an
agent can fetch.

Exit codes: 0 clean; 1 at least one recipe is wrong, or the committed
`recipes/README.md` is stale; 2 the request itself is unusable.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
RECIPES = ROOT / "recipes"
COMPOSITIONS = ROOT / "compositions"
PATTERNS = ROOT / "patterns"
MENU = RECIPES / "README.md"

from check_page import axes_of, parse_meta          # noqa: E402


# The fields, in the order a recipe states them, with whether one is owed.
# Order is checked as well as membership: a reader scanning nineteen of these
# is reading down a column, and a field that moves is one they stop finding.
FIELDS = [
    ("recipe", True),
    ("shape", True),
    ("shell", True),
    ("look", False),
    ("grounds", True),
    ("opens", True),
    ("closes", True),
    ("signature", True),
    ("pairing", True),
    ("notes", False),
]
REQUIRED = [name for name, owed in FIELDS if owed]
KNOWN = [name for name, _ in FIELDS]

# The building vocabulary's own seven, spelled the way a recipe spells them.
# The pattern header writes the same shapes with spaces; the two lists are the
# same list and a spelling drift between them is a lookup that returns nothing.
SHAPES = ["narrative", "peer-set", "comparison", "progression",
          "single-claim", "question-and-answer", "reference"]

# The ground ladder, four rungs and no others, exactly as CONTRIBUTING.md has
# it. A fifth name here would be a fifth name a builder cannot generalise.
RUNGS = ["plain", "soft", "brand", "deep"]

# Page furniture. Decided once for a site, so no recipe restates it and the
# band count skips it at both ends.
FURNITURE = {"masthead-nav", "colophon"}

PIN = re.compile(r"^([a-z0-9]+(?:-[a-z0-9]+)*)@([0-9]+)$")
FENCE = re.compile(r"^```recipe[ \t]*\n(.*?)^```[ \t]*$", re.M | re.S)
SIGNATURE_WORDS = 10


# ------------------------------------------------------------- what it reads

def shells():
    """{shell name without its version: {"page": ..., "bands": [...]}}.

    Read from each composition's own manifest rather than from its folder name
    or its README, because the manifest is what `ci/compose.py` writes and is
    the only one of the three that cannot describe a page the generator did not
    produce.
    """
    out = {}
    for folder in sorted(COMPOSITIONS.iterdir()):
        manifest = folder / "manifest.json"
        if not folder.is_dir() or not manifest.is_file():
            continue
        data = json.loads(manifest.read_text(encoding="utf-8"))
        names = [p["name"] for p in data.get("patterns", [])]
        out[data["composition"]] = {
            "page": data.get("page", ""),
            "folder": folder.name,
            "bands": [n for n in names if n not in FURNITURE],
        }
    return out


def pattern_axes():
    """{pattern name: {axis: {values}}} for every pattern in the library."""
    out = {}
    for folder in sorted(PATTERNS.iterdir()):
        markup = folder / "pattern.html"
        if not folder.is_dir() or not markup.is_file():
            continue
        out[folder.name] = axes_of(parse_meta(markup.read_text(encoding="utf-8")))
    return out


def split_block(text):
    """The fenced block's lines, or a fault. Returns (lines, fault-or-None)."""
    found = FENCE.findall(text)
    if not found:
        return None, ("fence", "no ```recipe block - a recipe is the fenced "
                              "block and the prose under it, in that order")
    if len(found) > 1:
        return None, ("fence", f"{len(found)} ```recipe blocks - a file is one "
                               f"recipe, and a second block is one nobody reads")
    lines = found[0].split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    return lines, None


def prose_of(text):
    """The first sentence under the fence - the menu line's own words.

    Taken from the prose rather than from a summary field on purpose. A recipe
    that carried both would carry two descriptions of one thing, and the one
    nobody reads is the one that goes stale.
    """
    after = FENCE.split(text)[-1] if FENCE.search(text) else ""
    for para in (p.strip() for p in after.split("\n\n")):
        if not para or para.startswith("#"):
            continue
        flat = " ".join(para.split())
        stop = flat.find(". ")
        return flat[:stop + 1] if stop != -1 else flat
    return ""


# ------------------------------------------------------------- what it judges
#
# Each check appends (kind, sentence). The kind is what the positive control
# asserts on, so it is part of this file's contract rather than a label: a
# fault renamed here without the control being told is a fault the control
# stops proving.

def field_faults(lines):
    """The fence's own grammar - shape of the lines, not their meanings."""
    bad = []
    seen = []
    for line in lines:
        if not line.strip():
            bad.append(("fields", "a blank line inside the fence - the block "
                                  "is read as one run of fields"))
            continue
        if ":" not in line:
            bad.append(("fields", f"{line.strip()!r} is not `field: value`"))
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        if key not in KNOWN:
            bad.append(("fields", f"unknown field {key!r} - a recipe carries "
                                  f"{', '.join(KNOWN)}"))
            continue
        if key in seen:
            bad.append(("fields", f"{key!r} appears twice"))
            continue
        if not value.strip():
            bad.append(("fields", f"{key!r} has no value"))
        seen.append(key)

    for name in REQUIRED:
        if name not in seen:
            bad.append(("fields", f"no {name!r} - it is required"))

    wanted = [n for n in KNOWN if n in seen]
    if seen != wanted and not any(k == "fields" for k, _ in bad):
        bad.append(("fields", f"fields out of order: {', '.join(seen)} - a "
                              f"recipe reads {', '.join(wanted)}"))
    return bad


def values_of(lines):
    out = {}
    for line in lines:
        if ":" in line and line.strip():
            key, _, value = line.partition(":")
            out.setdefault(key.strip(), value.strip())
    return out


def pin_faults(stem, values):
    bad = []
    pin = values.get("recipe", "")
    if not PIN.match(pin):
        bad.append(("pin", f"recipe: {pin!r} is not <kebab-name>@<version> - a "
                           f"recipe is pinned the way a pattern is"))
    elif pin != stem:
        bad.append(("pin", f"recipe: {pin} in a file called {stem}.md - the "
                           f"filename IS the pin, so the two cannot differ"))
    return bad


def shape_faults(values):
    shape = values.get("shape", "")
    if shape and shape not in SHAPES:
        return [("shape", f"shape: {shape!r} is not one of the seven content "
                          f"shapes - {', '.join(SHAPES)}")]
    return []


def shell_faults(values, known):
    """Pinless, and a shell that exists. Both halves matter for the same reason.

    A pinned shell is a menu item that ages: `pricing@3` resolves to one folder
    for as long as that folder is current and to last month's page afterwards,
    while a bare `pricing` resolves against the brand's own record first and the
    library's current release after it.
    """
    name = values.get("shell", "")
    if not name:
        return []
    if "@" in name:
        bare = name.split("@")[0]
        return [("shell", f"shell: {name} names a version - write {bare}. A "
                          f"pinned shell resolves to the release it was written "
                          f"against, not the one being built from")]
    if name not in known:
        offered = ", ".join(sorted(known)) or "none"
        return [("shell", f"shell: no composition called {name!r} - the shells "
                          f"are {offered}")]
    return []


def look_faults(values, axes):
    """`<pattern> axis=value[ axis=value]; <pattern> axis=value`."""
    raw = values.get("look", "")
    bad = []
    for entry in (e.strip() for e in raw.split(";")):
        if not entry:
            continue
        parts = entry.split()
        name = parts[0]
        if "@" in name:
            bare = name.split("@")[0]
            bad.append(("look", f"look: {name} names a version - write {bare}. "
                                f"A dial is set on whichever version the build "
                                f"resolves to"))
            continue
        if name not in axes:
            bad.append(("look", f"look: no pattern called {name!r} in patterns/"))
            continue
        if len(parts) == 1:
            bad.append(("look", f"look: {name} sets no dial - an entry is a "
                                f"pattern and at least one axis=value"))
            continue
        for dial in parts[1:]:
            axis, sep, value = dial.partition("=")
            if not sep or not value:
                bad.append(("look", f"look: {dial!r} on {name} is not "
                                    f"axis=value"))
            elif axis not in axes[name]:
                offered = ", ".join(sorted(axes[name])) or "none"
                bad.append(("look", f"look: {name} has no {axis!r} axis - it "
                                    f"offers: {offered}"))
            elif value not in axes[name][axis]:
                bad.append(("look", f"look: {name} has no {axis}={value} - it "
                                    f"offers {axis}="
                                    f"{'|'.join(sorted(axes[name][axis]))}"))
    return bad


def grounds_faults(values, known):
    """One rung per band, and the shell says how many bands there are.

    Both numbers go in the message. A recipe with four rungs for a five-band
    shell is not obviously wrong from either end on its own, and the fix is
    different depending on which number the writer believed.
    """
    raw = values.get("grounds", "")
    rungs = [r.strip() for r in raw.split(",") if r.strip()]
    bad = []
    for rung in rungs:
        if rung not in RUNGS:
            bad.append(("grounds", f"grounds: {rung!r} is not a rung on the "
                                   f"ground ladder - {', '.join(RUNGS)}"))
    shell = values.get("shell", "")
    if shell in known:
        bands = known[shell]["bands"]
        if len(rungs) != len(bands):
            bad.append(("grounds", f"grounds: {len(rungs)} rung(s) for a shell "
                                   f"with {len(bands)} band(s) - {shell} runs "
                                   f"{' -> '.join(bands)}, and the header and "
                                   f"footer are not bands"))
    return bad


def signature_faults(values):
    words = values.get("signature", "").split()
    if len(words) > SIGNATURE_WORDS:
        return [("signature", f"signature: {len(words)} words - a structural "
                              f"signature is {SIGNATURE_WORDS} or fewer, or it "
                              f"is a description of the page instead")]
    return []


def pairing_faults(values):
    """`brand` and nothing else. The slot is the whole point of the field.

    A library recipe naming a face would be a menu item that had already made
    the one decision a brand cannot share with any other brand.
    """
    got = values.get("pairing", "")
    if got and got != "brand":
        return [("pairing", f"pairing: {got!r} - a library recipe is "
                            f"brand-agnostic, so this is the literal `brand`, "
                            f"a slot filled from the brand's own record")]
    return []


def faults_in(stem, text, known=None, axes=None):
    """Every fault in one recipe file. Returns a list of (kind, sentence)."""
    known = shells() if known is None else known
    axes = pattern_axes() if axes is None else axes

    lines, fence_fault = split_block(text)
    if fence_fault:
        return [fence_fault]

    bad = field_faults(lines)
    values = values_of(lines)
    bad += pin_faults(stem, values)
    bad += shape_faults(values)
    bad += shell_faults(values, known)
    bad += look_faults(values, axes)
    bad += grounds_faults(values, known)
    bad += signature_faults(values)
    bad += pairing_faults(values)
    return bad


def duplicate_faults(records):
    """Two recipes on one pin. Cross-file, so it cannot live in faults_in.

    A pin is what a brand records when it takes a recipe, so two files claiming
    one is a recorded choice that no longer names a single page.
    """
    bad = []
    seen = {}
    for stem, values in records:
        pin = values.get("recipe", "")
        if not pin:
            continue
        if pin in seen:
            bad.append((stem, ("duplicate", f"recipe: {pin} is already claimed "
                                            f"by {seen[pin]}.md - a pin names "
                                            f"one recipe")))
        else:
            seen[pin] = stem
    return bad


# ------------------------------------------------------------- what it writes

def menu(records, known):
    """recipes/README.md - the whole file, from the recipes themselves."""
    rows = []
    for stem, values, sentence in records:
        shell = values.get("shell", "")
        page = known.get(shell, {}).get("page", "")
        rows.append((page, values.get("recipe", stem), shell,
                     values.get("shape", ""), sentence))
    rows.sort(key=lambda r: (r[0], r[1]))

    out = ["# Recipes", "",
           "One line per recipe - generated by `ci/check_recipes.py` from "
           "`recipes/*.md`, never hand-edited.",
           "Put two or three of these in front of whoever the page is for, "
           "described in their words and never by the pin - a pin is what "
           "gets recorded, not what gets offered. Then read only the chosen "
           "recipe's file: it names the shell to fetch and the decisions "
           "already made above it.",
           ""]
    for page, pin, shell, shape, sentence in rows:
        out.append(f"- **{pin}** - {page} - {shape} - shell: {shell} - "
                   f"{sentence}")
    return "\n".join(out) + "\n"


# -------------------------------------------------------- the positive control
#
# One fixture per fault kind this file can report, plus one that must stay
# quiet. The kind each one is expected to raise is asserted, not merely the
# fact that something failed: a fixture that trips a different check would
# otherwise report the gate as working while the check it was written for sat
# dead.

VALID = """```recipe
recipe: sample-control@1
shape: reference
shell: pricing
look: hero-stated alignment=centred
grounds: plain, soft, plain, brand
opens: a claim, set large, with the price named in the line under it
closes: a full-width band on the brand colour
signature: stated opener, tier cards, questions, band
pairing: brand
notes: a sample recipe, used only to prove this gate fires
```

A sample recipe for the control run. It exists to be checked rather than
offered, and nothing fetches it.
"""


def broken_fixtures():
    """(label, stem, text, the kind it must raise)."""
    def edit(old, new, stem="sample-control@1"):
        return stem, VALID.replace(old, new)

    cases = [
        ("no fenced block", "sample-control@1",
         "A recipe with no fence in it at all.\n", "fence"),
        ("two fenced blocks", "sample-control@1", VALID + "\n" + VALID, "fence"),
        ("a blank line inside the fence", *edit(
            "shape: reference", "\nshape: reference"), "fields"),
        ("a field the grammar has no room for", *edit(
            "notes: a sample", "colour: pink\nnotes: a sample"), "fields"),
        ("the same field twice", *edit(
            "shape: reference", "shape: reference\nshape: narrative"), "fields"),
        ("a required field missing", *edit("pairing: brand\n", ""), "fields"),
        ("fields out of their order", *edit(
            "shape: reference\nshell: pricing",
            "shell: pricing\nshape: reference"), "fields"),
        ("a pin that is not name@version", *edit(
            "recipe: sample-control@1", "recipe: sample-control"), "pin"),
        ("a pin disagreeing with its filename", "sample-other@1", VALID, "pin"),
        ("a shape outside the seven", *edit(
            "shape: reference", "shape: listicle"), "shape"),
        ("a pinned shell", *edit("shell: pricing", "shell: pricing@3"), "shell"),
        ("a shell with no composition behind it", *edit(
            "shell: pricing", "shell: pricing-imaginary"), "shell"),
        ("a pinned pattern in look", *edit(
            "look: hero-stated", "look: hero-stated@4"), "look"),
        ("a look naming no pattern in the library", *edit(
            "look: hero-stated alignment=centred",
            "look: hero-imaginary alignment=centred"), "look"),
        ("an axis the pattern does not declare", *edit(
            "alignment=centred", "sparkle=on"), "look"),
        ("a value the axis does not offer", *edit(
            "alignment=centred", "alignment=diagonal"), "look"),
        ("a rung off the ground ladder", *edit(
            "grounds: plain, soft", "grounds: pink, soft"), "grounds"),
        ("fewer rungs than the shell has bands", *edit(
            "grounds: plain, soft, plain, brand", "grounds: plain, soft"),
         "grounds"),
        ("more rungs than the shell has bands", *edit(
            "grounds: plain, soft, plain, brand",
            "grounds: plain, soft, plain, soft, brand"), "grounds"),
        ("a signature past ten words", *edit(
            "signature: stated opener, tier cards, questions, band",
            "signature: a stated opener, then the tier cards, then the "
            "questions, then the closing band"), "signature"),
        ("a pairing naming a face instead of the slot", *edit(
            "pairing: brand", "pairing: Fraunces over Hanken Grotesk"),
         "pairing"),
    ]
    return cases


def run_control():
    known, axes = shells(), pattern_axes()
    print("ci/check_recipes.py, the positive control")
    missed = []

    for label, stem, text, want in broken_fixtures():
        kinds = [k for k, _ in faults_in(stem, text, known, axes)]
        ok = want in kinds
        print(f"  {'ok  ' if ok else 'MISSED'} {label:<48} [{want}] "
              f"got {kinds or ['nothing']}")
        if not ok:
            missed.append(label)

    # Cross-file, so it takes two records rather than one fixture.
    values = values_of(split_block(VALID)[0])
    dup = duplicate_faults([("sample-control@1", values),
                            ("sample-copy@1", values)])
    ok = any(k == "duplicate" for _, (k, _) in dup)
    print(f"  {'ok  ' if ok else 'MISSED'} {'two recipes sharing one pin':<48} "
          f"[duplicate] got {[k for _, (k, _) in dup] or ['nothing']}")
    if not ok:
        missed.append("two recipes sharing one pin")

    # The other half. A gate that rejects every recipe catches nothing either,
    # and would be indistinguishable from this run passing.
    kinds = [k for k, _ in faults_in("sample-control@1", VALID, known, axes)]
    ok = not kinds
    print(f"  {'ok  ' if ok else 'FAIL'} {'a valid recipe raises nothing':<48} "
          f"got {kinds or ['nothing']}")
    if not ok:
        missed.append("a valid recipe raises nothing")

    print()
    if missed:
        print(f"  CONTROL FAILED: {len(missed)} case(s) the gate cannot see - "
              + ", ".join(missed))
        return 1
    print(f"  control: {len(broken_fixtures()) + 1} fault(s) caught and a valid "
          f"recipe left alone. The gate fires.")
    return 0


# ---------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="fail if the committed recipes/README.md is stale")
    ap.add_argument("--broken", action="store_true",
                    help="the positive control: synthetic faults that must fire")
    args = ap.parse_args()

    if args.broken:
        return run_control()

    if not RECIPES.is_dir():
        print("ci/check_recipes.py: no recipes/ directory", file=sys.stderr)
        return 2

    known, axes = shells(), pattern_axes()
    if not known:
        print("ci/check_recipes.py: no compositions to check a shell against - "
              "run ci/compose.py first", file=sys.stderr)
        return 2

    faults = []
    records = []
    files = sorted(p for p in RECIPES.glob("*.md") if p.name != "README.md")
    print(f"ci/check_recipes.py, {len(files)} recipe(s)")

    for path in files:
        text = path.read_text(encoding="utf-8")
        bad = faults_in(path.stem, text, known, axes)
        for kind, message in bad:
            faults.append(f"[{kind}] {path.name}: {message}")
        lines, fence_fault = split_block(text)
        if fence_fault:
            continue
        values = values_of(lines)
        records.append((path.stem, values, prose_of(text)))
        shell = values.get("shell", "")
        bands = len(known.get(shell, {}).get("bands", []))
        print(f"  {values.get('recipe', path.stem)}: {shell} "
              f"({bands} band(s)), {values.get('shape', '?')}")

    for stem, (kind, message) in duplicate_faults(
            [(s, v) for s, v, _ in records]):
        faults.append(f"[{kind}] {stem}.md: {message}")

    print()
    for line in faults:
        print(f"  FAIL  {line}")
    if faults:
        print(f"\n  {len(faults)} fault(s) - the menu is not rewritten while a "
              f"recipe is wrong")
        return 1

    written = menu(records, known)
    current = MENU.read_text(encoding="utf-8") if MENU.is_file() else None
    if args.check:
        if current != written:
            print("  FAIL  [stale] recipes/README.md differs from the recipes "
                  "it is generated from - run: python ci/check_recipes.py")
            return 1
        print(f"  clean: {len(records)} recipe(s), and recipes/README.md is "
              f"what they generate")
        return 0

    if current != written:
        MENU.write_text(written, encoding="utf-8")
        print(f"  clean: {len(records)} recipe(s) - recipes/README.md rewritten")
    else:
        print(f"  clean: {len(records)} recipe(s) - recipes/README.md unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
