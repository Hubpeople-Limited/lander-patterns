#!/usr/bin/env python3
"""Emit one JSON file carrying everything a browser needs to compose a page
from this library, and write it beside the previews so Pages serves it.

**Why a bundle and not thirty fetches.** The consumer here is not an agent with
a filesystem, it is a page in somebody's browser that has to render a chooser
before anyone has clicked anything. Thirty round trips to raw.githubusercontent
is a slow first paint and thirty chances to half-load; one file is one fetch and
either arrives or does not.

**Why it is generated rather than kept.** The alternative is a copy of this
library living wherever the chooser lives, updated by hand. `LATEST` moved three
times in the day this was written. A copy would be wrong by the end of the week
and nobody would know which half was stale, so the chooser fetches and the
library publishes. Nothing to keep in step.

**What is in it, and what is deliberately not.**

Patterns ship their markup with the slots still in it, plus the sample content
that fills them, because the browser does the filling: that is the same division
`build_preview.py` uses server-side, and a pre-filled string could not be
re-filled with a partner's own words later.

Shells ship their recipe - the ordered patterns and the variant each was pinned
to - rather than assembled HTML. The assembly is a concatenation the browser can
do from the patterns it already has, and shipping it twice would be two
descriptions of one page, free to disagree.

Token sets ship whole, because they are what makes the same pattern look like a
different brand, and that is the point of the chooser.

Two hosts, one contract: `configurator.json` is whatever the current release
is, and `configurator-<tag>.json` is that release pinned. A consumer that wants
to move with the library reads the first; one that wants a fixed shape reads
the second. Both sit in preview/site/, which CI already deploys to Pages, and
Pages already answers with `Access-Control-Allow-Origin: *` - checked, because
the whole idea rests on it.
"""
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from build_preview import (  # noqa: E402
    FURNITURE_DISPLAY, OUT, ROOT, SHELL_IMAGE_SWAP, SHELL_IMAGES,
    SHELL_TOKEN_SETS, TOKEN_SETS, release_tag,
)

# The five optional tokens from TOKENS.md, with the ranges that document says
# are supported. They are repeated here rather than parsed out of the prose,
# and `check_dials_documented` below fails the build if the two ever name a
# different set - a chooser offering a dial the contract does not have would
# render pages nobody could reproduce.
#
# `tracking` is an offset and the rest are multipliers or a weight, which is
# why `default` is stated per dial instead of being assumed to be 1.
DIALS = {
    "type-scale": {"default": 1, "min": 0.9, "max": 1.2, "step": 0.01,
                   "label": "Display type size",
                   "note": "Multiplies display type only. Body copy does not move."},
    "space-scale": {"default": 1, "min": 0.9, "max": 1.2, "step": 0.01,
                    "label": "Spacing",
                    "note": "Multiplies the spacing ramp once, where it is defined."},
    "heading-leading": {"default": 1, "min": 0.95, "max": 1.15, "step": 0.01,
                        "label": "Heading line height",
                        "note": "Multiplies the line height of display type only."},
    "heading-tracking": {"default": 0, "min": -0.02, "max": 0.04, "step": 0.005,
                         "label": "Heading letter spacing",
                         "note": "Added, in em, not multiplied. Negative is the ordinary case."},
    "weight-display": {"default": 700, "min": 400, "max": 800, "step": 100,
                       "label": "Display weight",
                       "note": "Only to a weight the face actually has."},
}


def check_dials_documented():
    """The dial list here and the one in TOKENS.md must name the same tokens.

    Not a style check. A chooser that offers `--letter-spacing` because someone
    invented it here would produce a design whose recipe the toolkit cannot
    build, and the page would look right in the browser and wrong on the site.
    """
    text = (ROOT / "TOKENS.md").read_text(encoding="utf-8")
    section = text.split("## Dials", 1)
    if len(section) != 2:
        raise SystemExit("configurator: TOKENS.md has no '## Dials' section any more")
    body = section[1].split("\n## ", 1)[0]
    # Only the first cell of a table row. Reading every `--token` in the prose
    # instead caught `--font-heading` and `--color-heading`, which the section
    # mentions while explaining what the dials do to them: a check that fires
    # on a correct bundle gets switched off rather than fixed.
    documented = {m.group(1) for m in
                  re.finditer(r"^\|\s*`--([a-z-]+)`\s*\|", body, re.M)}
    if not documented:
        raise SystemExit("configurator: no dial table found under TOKENS.md '## Dials'")
    named = set(DIALS)
    if not named <= documented:
        raise SystemExit(
            f"configurator: dial(s) not in TOKENS.md: {sorted(named - documented)}")
    missing = documented - named
    if missing:
        raise SystemExit(
            f"configurator: TOKENS.md documents dial(s) this bundle omits: {sorted(missing)}")


def pattern_entry(folder, meta):
    """Markup with its slots intact, its stylesheet, and the sample that fills it."""
    markup = (folder / "pattern.html").read_text(encoding="utf-8")
    # The metadata header is for whoever places the pattern by hand. Everything
    # in it is already on the manifest entry beside this, in fields rather than
    # in a comment, so shipping it twice is bytes and a second thing to parse.
    markup = re.sub(r"\s*<!--\n.*?\n-->", "", markup, count=1, flags=re.S)
    # And then every other comment EXCEPT a slot marker. What is left in a
    # pattern file is placement guidance for a person - which modifier to take,
    # which row to duplicate - and the bundle already carries all of it as
    # data: the axes are on `meta.variants`, the repeat is `sample._repeat`.
    #
    # **A content slot is itself a comment.** Stripping without this exception
    # deleted every `<!-- slot: headline -->` in the library, and the damage
    # was invisible from anything structural: a shell composed from the bundle
    # still had the right sections in the right order with the right variant
    # classes on them, and no words in any of them. It was caught by rendering
    # one in a browser and diffing the text against the shipped shell, which
    # is now the only check that could have caught it.
    markup = re.sub(r"<!--(?!\s*slot\s*:).*?-->", "", markup, flags=re.S)
    markup = re.sub(r"\n{3,}", "\n\n", markup)
    sample_file = folder / "preview-content.json"
    return {
        "meta": meta,
        "html": markup.strip(),
        "css": (folder / "pattern.css").read_text(encoding="utf-8").strip(),
        "sample": json.loads(sample_file.read_text(encoding="utf-8")),
    }


def shell_entry(folder):
    """A shell's recipe: what it is for, and what it is made of, in order."""
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    return {
        "name": manifest["composition"],
        "version": manifest["version"],
        "page": manifest["page"],
        "patterns": [
            {"name": p["name"], "version": p["version"],
             "variant": p.get("variant", {})}
            for p in manifest["patterns"]
        ],
    }


def data_uri(path):
    """An SVG as a data: URI, so the bundle carries its own images.

    A relative filename would only resolve for a consumer served from the same
    directory as the previews, and an absolute one would tie the bundle to the
    host it happens to sit on today. These are three files of about half a
    kilobyte; inlining them costs nothing and makes the bundle answer from
    anywhere.
    """
    svg = path.read_text(encoding="utf-8").strip()
    # Percent-encode only what breaks inside a url() or an attribute. Base64
    # would be safe too and a third larger, and unreadable in a diff.
    for char, code in (("%", "%25"), ("#", "%23"), ("<", "%3C"), (">", "%3E"),
                       ('"', "%22"), ("\n", "%20")):
        svg = svg.replace(char, code)
    return "data:image/svg+xml;charset=utf-8," + svg


def build():
    check_dials_documented()
    patterns_meta = json.loads((ROOT / "patterns.json").read_text(encoding="utf-8"))

    patterns = {}
    for folder in sorted(p for p in (ROOT / "patterns").iterdir() if p.is_dir()):
        if folder.name not in patterns_meta:
            raise SystemExit(f"configurator: {folder.name} is not in patterns.json - "
                             "run ci/lint.py first")
        patterns[folder.name] = pattern_entry(folder, patterns_meta[folder.name])

    shells = {}
    for folder in sorted(p for p in (ROOT / "compositions").iterdir() if p.is_dir()):
        entry = shell_entry(folder)
        unknown = [p["name"] for p in entry["patterns"] if p["name"] not in patterns]
        if unknown:
            raise SystemExit(f"configurator: {folder.name} names pattern(s) that are "
                             f"not in the library: {unknown}")
        shells[folder.name] = entry

    token_sets = {
        name: (ROOT / "preview" / TOKEN_SETS[name]).read_text(encoding="utf-8").strip()
        for name in SHELL_TOKEN_SETS
    }

    # The platform's own tokens, and what to show instead of each while nobody
    # is standing on the platform. Shipped rather than left to the consumer,
    # because a consumer that invents them renders a page that is subtly not
    # the page this library previews: the first harness written against this
    # bundle guessed a one-item footer menu where the previews use three, and
    # the two rendered differently for no reason anybody chose.
    furniture = dict(FURNITURE_DISPLAY)
    images = {name: data_uri(ROOT / "lib" / "placeholders" / source)
              for source, name in SHELL_IMAGES.items()}
    furniture["{{logo.src}}"] = data_uri(ROOT / "preview" / "sample-wordmark.svg")
    # Sample content names the flat CI images; a consumer wants the placeholder
    # of the same shape, as a URI it can use from any origin.
    image_swap = {old: images[new] for old, new in SHELL_IMAGE_SWAP.items()}

    return {
        # No timestamp. The tag identifies the release and a build of the same
        # tree has to produce the same bytes, or `--check` could never tell a
        # real change from having been run twice.
        "tag": release_tag(),
        "generatedBy": "ci/build_configurator.py",
        "tokenSets": token_sets,
        "dials": DIALS,
        "furniture": furniture,
        "imageSwap": image_swap,
        "placeholders": images,
        "shells": shells,
        "patterns": patterns,
    }


def main():
    bundle = build()
    text = json.dumps(bundle, indent=1, sort_keys=True) + "\n"
    if not OUT.exists():
        raise SystemExit("configurator: preview/site does not exist - "
                         "run ci/build_preview.py first")
    current = OUT / "configurator.json"
    current.write_text(text, encoding="utf-8", newline="\n")

    # The pinned copy exists only where there is a release to pin to. Off CI
    # the tag reads "v75 (working tree)", and minting configurator-v75.json
    # from the first word of that would put a file on disk claiming to be a
    # release it is not, next to a real one, with no way to tell them apart.
    tagged = None
    if re.fullmatch(r"v\d+", bundle["tag"]):
        # A copy rather than a second build: two builds could differ, and then
        # the pinned file would not be the release it names.
        tagged = OUT / f"configurator-{bundle['tag']}.json"
        shutil.copy(current, tagged)

    where = current.name + (f" and {tagged.name}" if tagged else
                            " (no pinned copy: not a release build)")
    print(f"built {where}: "
          f"{len(bundle['patterns'])} pattern(s), {len(bundle['shells'])} shell(s), "
          f"{len(bundle['tokenSets'])} token set(s), {len(text) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
