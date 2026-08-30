#!/usr/bin/env python3
"""Give every pattern a name and a sentence a partner would recognise.

    python dev/write_display_names.py [--check]

`colophon` is a printing term. `opener-split`, `claim-stack`, `anchored-split`
and `zigzag-rows` are this library talking to itself. They are good folder
names - short, unambiguous, and the thing a version pins - and they are no use
in a tool where somebody is choosing what to put on a page.

So each pattern also carries `display-name` and `summary` in its header:

    colophon      -> "Footer",  "Your site footer, with the legal links."
    opener-split  -> "Section opener"
    faq-details   -> "Questions and answers"

Same division as variants.json: the key is what ships and what a brand pins,
the label is what a person sees. The folder name never changes.

Written from here rather than by hand in 46 headers so the voice is one voice,
and re-runnable so a new pattern is a line in this file.
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# name: (display name, one sentence a partner would recognise)
NAMES = {
    "anchored-split": ("Pinned panel", "A panel that stays put on one side while the evidence for it scrolls past on the other."),
    "article-masthead": ("Article header", "The top of a written piece: the title, who wrote it and when."),
    "benefit-tiles": ("Benefit tiles", "Four tall tiles, each with an icon and a short benefit."),
    "capability-tabs": ("Feature switcher", "A row of tabs, each showing one feature in a panel below."),
    "claim-stack": ("Big promises", "Three to five promises set very large, one to a screen."),
    "colophon": ("Footer", "Your site footer, with the menu, the legal links and the copyright line."),
    "comparison-table": ("Comparison table", "Three things compared against the same list of criteria."),
    "cta-assurance": ("Reassurance line", "The short run of reassurances that sits under a join button."),
    "cta-band": ("Closing call to action", "A full-width closing band with one claim and one button."),
    "cta-curtain": ("Reveal call to action", "A full-screen closing call to action, uncovered as the page above it scrolls away."),
    "cta-image": ("Photo call to action", "A closing call to action over one full-width photograph."),
    "cta-sticky": ("Sticky join bar", "A join button fixed to the bottom of the screen on a phone."),
    "faq-details": ("Questions and answers", "Common questions, each opening to its answer when tapped."),
    "feature-panels": ("Feature panels", "A run of full-width panels, each a shade stronger than the last."),
    "gallery-scroll": ("Photo gallery", "A row of photographs you swipe sideways through."),
    "heading-block": ("Section heading", "A heading and one supporting line, to introduce what follows."),
    "hero-centred": ("Centred opener", "An opening claim centred above a wide photograph."),
    "hero-overlay": ("Full-screen opener", "One photograph filling the first screen, with the claim over it."),
    "hero-split": ("Split opener", "The opening claim on one side, a strong photograph on the other."),
    "hero-squeeze": ("One-screen page", "The whole page in a single screen: a photograph, one claim, one button."),
    "hero-stated": ("Worded opener", "An opener made of words rather than pictures."),
    "link-cluster": ("Link cluster", "A wrapping run of plain links to real pages: places, categories, topics."),
    "listing-rows": ("Listing rows", "Full-width rows rather than cards, each with a title and a line of detail."),
    "masthead-nav": ("Site header", "Your logo, the menu, and the log in and join buttons."),
    "media-card-grid": ("Photo card grid", "A grid of upright cards, each led by a photograph."),
    "member-strip": ("Member strip", "A short row of real members, with a photograph and a line each."),
    "offer-split": ("Mid-page offer", "A conversion beat with no photography: the argument on one side, the offer on the other."),
    "opener-split": ("Section opener", "A title on the left with its supporting words on the right."),
    "photo-cards": ("Photo cards", "Cards with the photograph on top and the words underneath."),
    "picker-chips": ("Quick chooser", "The first sign-up decision as one tap: a question and a row of choices."),
    "pinned-cards": ("Pinned photo cards", "Full-screen photo cards that stack over one another as you scroll."),
    "portrait-wall": ("Portrait wall", "A lattice of member portraits with the strongest one held in the middle."),
    "pricing-tiers": ("Pricing tiers", "Two or three plans side by side with matching buttons."),
    "prose-column": ("Article body", "The body of a written piece, held to a readable width."),
    "quote-feature": ("Feature quote", "One oversized testimonial on a full-width tinted stage."),
    "rating-mark": ("Rating", "A published rating shown as whole stars beside the figure."),
    "safety-protections": ("Safety protections", "Safety measures as cards, grouped by what they protect against."),
    "source-note": ("Source note", "The line under a claim saying where the figure came from."),
    "stat-rows": ("Statistic rows", "Full-width rows, each a large figure with a line explaining it."),
    "stats-band": ("Statistics band", "A full-width band of real figures, each paired with what it means."),
    "steps-numbered": ("Numbered steps", "How it works, as numbered image cards."),
    "steps-plain": ("Plain steps", "How it works, as a plain numbered lattice with no photographs."),
    "testimonial-carousel": ("Testimonial carousel", "Testimonials you move through one at a time."),
    "testimonial-grid": ("Testimonial cards", "Three testimonial cards side by side, with portraits."),
    "trust-row": ("Trust marks", "A strip of assurance marks: a membership lockup and a row of guarantees."),
    "zigzag-rows": ("Alternating rows", "Image-and-words rows where the image swaps side row to row."),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    folders = sorted(p for p in (ROOT / "patterns").iterdir() if p.is_dir())
    missing = [f.name for f in folders if f.name not in NAMES]
    if missing:
        sys.exit("no display name written for: %s" % ", ".join(missing))
    extra = sorted(set(NAMES) - {f.name for f in folders})
    if extra:
        sys.exit("display names for patterns that do not exist: %s" % ", ".join(extra))

    changed = 0
    for folder in folders:
        path = folder / "pattern.html"
        text = path.read_text(encoding="utf-8")
        display, summary = NAMES[folder.name]
        out = text
        # Sit them directly under `name:`, which is what they are labels for.
        out = re.sub(r"(?m)^display-name:.*\n", "", out)
        out = re.sub(r"(?m)^summary:.*\n", "", out)
        out = re.sub(r"(?m)^(name:\s*%s\n)" % re.escape(folder.name),
                     r"\1display-name: %s\nsummary: %s\n" % (display, summary),
                     out, count=1)
        if out == text:
            print("  %-22s UNCHANGED - is the name: line as expected?" % folder.name)
            continue
        if args.check:
            print("  %-22s would set %r" % (folder.name, display))
        else:
            path.write_text(out, encoding="utf-8", newline="\n")
            changed += 1
    print("%d pattern(s) %s" % (changed, "checked" if args.check else "written"))


if __name__ == "__main__":
    main()
