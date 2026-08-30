#!/usr/bin/env python3
"""Write each pattern's variants.json - the words a chooser shows for a rung.

    python dev/write_variant_notes.py [--check]

A rung is a word like `menu-centre`. It is a class name: precise, versioned,
pinned by brands, and no use at all to somebody deciding what a page should
look like. So each axis carries a LABEL a person would expect to see - the
name another CMS would give it - and each rung carries its own, plus a line
saying what picking it does.

    ground   -> "Background",   soft -> "Light"
    menu     -> "Mobile menu",  drawer -> "Slide-out drawer"

The class names never change here. A chooser shows the labels; the recipe it
hands over still says `ground=soft`, because that is what the library, the
page checker and every brand stylesheet already agree on.

The notes live with the pattern, because the pattern owns the meaning and is
what changes when the meaning does. Written from here rather than by hand in
eight folders so the wording stays in one voice.
"""
import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# The ground ladder is one vocabulary across the library, so it gets one set of
# words everywhere it appears. CONTRIBUTING.md carries the table behind it.
GROUND = {
    "label": "Background",
    "note": "The colour behind this section. Change it between one section and "
            "the next so the page reads as bands instead of one flat colour.",
    "rungs": {
        "plain": ("Default", "The page's own background colour. Quiet, and the "
                             "right choice for most sections."),
        "soft": ("Light", "A soft tint. The easiest way to separate one section "
                          "from the one above it."),
        "brand": ("Brand colour", "Your brand colour, with text chosen to stay "
                                  "readable on it. Best used once or twice a "
                                  "page, not on everything."),
        "deep": ("Dark", "A dark band. The boldest option, and the one that "
                         "loses its impact if you use it more than once."),
    },
}

NOTES = {
    "anchored-split": {"ground": GROUND},
    "claim-stack": {"ground": GROUND},
    "colophon": {"ground": GROUND},
    "link-cluster": {"ground": GROUND},
    "listing-rows": {"ground": GROUND},
    "hero-stated": {
        "ground": GROUND,
        "alignment": {
            "label": "Text alignment",
            "note": "Where the opening words sit.",
            "rungs": {
                "default": ("Left", "Aligned to the left. Easier to read, "
                                    "especially for longer text."),
                "centred": ("Centred", "Good for a short headline with one line "
                                       "under it. Long paragraphs are harder to "
                                       "read centred."),
            },
        },
    },
    "opener-split": {
        "rule": {
            "label": "Divider",
            "note": "Whether a thin line separates this block from what comes "
                    "next.",
            "rungs": {
                "default": ("None", "No line."),
                "ruled": ("Hairline", "A thin line underneath. Useful when the "
                                      "next section has the same background and "
                                      "would otherwise blend into this one."),
            },
        },
    },
    "masthead-nav": {
        "ground": GROUND,
        "layout": {
            "label": "Desktop layout",
            "note": "How the header is arranged on a computer screen.",
            "rungs": {
                "inline": ("Single row", "Logo, menu and buttons all on one row. "
                                         "The usual choice, and the shortest."),
                "centred": ("Stacked", "Logo on its own line with the menu "
                                       "centred underneath. A more formal look, "
                                       "but the header is twice as tall."),
            },
        },
        "menu": {
            "label": "Mobile menu",
            "note": "What the menu does on a phone, where the links will not fit "
                    "in a row.",
            "rungs": {
                "drawer": ("Slide-out drawer", "A panel slides in over the page. "
                                               "Full height, and it scrolls on "
                                               "its own if you have a lot of "
                                               "links. What most people expect "
                                               "on a phone."),
                "panel": ("Drop-down panel", "A panel drops down from the "
                                             "header, full width. Lighter, and "
                                             "best when you only have two or "
                                             "three links."),
                "row": ("Scrolling row", "No button at all - the links stay in a "
                                         "row you swipe sideways. Only works "
                                         "with a few short links."),
            },
        },
        "sticky": {
            "label": "Sticky header",
            "note": "Whether the header stays on screen as people scroll.",
            "rungs": {
                "static": ("Off", "The header scrolls away with the page, "
                                  "leaving the whole screen for your content."),
                "pinned": ("On", "The header stays at the top. People find their "
                                 "way around about 22% faster and your sign-up "
                                 "button is always there, but it takes up room "
                                 "on every screen."),
            },
        },
        "menu-align": {
            "label": "Menu alignment",
            "note": "Which side the links line up on inside the mobile menu. It "
                    "does not move the menu itself.",
            "rungs": {
                "menu-start": ("Left", "Lined up on the left. Easiest to scan, "
                                       "and the default."),
                "menu-centre": ("Centre", "Calmer, though sub-links lose the "
                                          "indent line that marks them out."),
                "menu-end": ("Right", "Lined up on the right, so they follow on "
                                      "from the button that opened them."),
            },
        },
        "menu-side": {
            "label": "Menu position",
            "note": "Which side the menu button sits on. The menu opens from the "
                    "same side, so the button is always beside what it opens.",
            "rungs": {
                "side-start": ("Left", "Button on the left, menu opens from the "
                                       "left."),
                "side-end": ("Right", "Button on the right, menu opens from the "
                                      "right. The default."),
            },
        },
    },
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    sys.path.insert(0, str(ROOT / "ci"))
    import lint

    changed = 0
    for name, axes in sorted(NOTES.items()):
        folder = ROOT / "patterns" / name
        meta = lint.parse_header((folder / "pattern.html").read_text(encoding="utf-8"),
                                 folder / "pattern.html")
        declared = lint.parse_variants(meta.get("variants", "")) or {}
        if set(declared) != set(axes):
            sys.exit("%s: notes cover %s, pattern declares %s"
                     % (name, sorted(axes), sorted(declared)))
        out = {}
        for axis, rungs in declared.items():
            spec = axes[axis]
            # A shared vocabulary may cover more rungs than a pattern offers -
            # the ground ladder has four and most patterns take two. What must
            # not happen is a declared rung with no words for it.
            missing = [r for r in rungs if r not in spec["rungs"]]
            if missing:
                sys.exit("%s %s: no note for %s" % (name, axis, ", ".join(missing)))
            out[axis] = {
                "label": spec["label"],
                "note": spec["note"],
                # The pattern's own rung order, so a chooser shows them the way
                # the pattern lists them rather than however a dict happened to.
                "rungs": {r: {"label": spec["rungs"][r][0],
                              "note": spec["rungs"][r][1]} for r in rungs},
            }
        text = json.dumps(out, indent=2, ensure_ascii=False) + "\n"
        path = folder / "variants.json"
        current = path.read_text(encoding="utf-8") if path.is_file() else None
        if args.check:
            print("  %-16s %s" % (name, "matches" if current == text else "WOULD CHANGE"))
        else:
            if current != text:
                path.write_text(text, encoding="utf-8", newline="\n")
                changed += 1
            print("  %-16s %d axes, %d rungs"
                  % (name, len(out), sum(len(a["rungs"]) for a in out.values())))
    if not args.check:
        print("%d file(s) written or updated" % changed)


if __name__ == "__main__":
    main()
