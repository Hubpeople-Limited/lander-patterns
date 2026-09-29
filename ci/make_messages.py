#!/usr/bin/env python3
"""The sign-up card's encouraging lines, and the rule they are held to.

A short line appears in the card after an answer: after "I am", "looking for",
where the visitor lives, each interest ticked, and on the last step. The lines
live in lib/messages/:

    steps.json       lines for each moment, for every brand
    excite.json      lines for each interest on the Excite platform, by label
    affinity.json    the same for Affinity

The two platforms' files are never mixed: an interest's line is written for its
platform's audience, and Excite's are adult. The card loads only its own.

THE RULE. A line talks about what the visitor's answer does for them, or who it
draws to them. It never says how many people are on the site - no counts,
amounts or popularity, no "members" or "here" - because that is untrue on a
brand with no members yet. It cites no survey or study, uses no dash, and runs
to at most 90 characters. Health and disability labels carry one plain line.

    python ci/make_messages.py --check                   hold every line to the rule
    python ci/make_messages.py --import DIR              write the interest files from
                                                         reviewed batches in DIR
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "lib" / "messages"
PLATFORMS = ("excite", "affinity")
MOMENTS = ("iam", "seeking", "location", "interest", "last")
MAX = 90
# The moments' tokens, filled from the visitor's own answers; a capital first
# letter asks for the answer capitalised.
TOKENS = re.compile(r"\{(who|Who|place|Place|interest|Interest)\}")

# Counts, amounts and popularity: what makes a line untrue on a brand with no members.
CLAIMS = re.compile(
    r"(?i)\b(plenty|many|most|lots?|loads?|popular|popularity|common(ly)?|biggest|largest|crowds?|"
    r"regulars?|turnouts?|loyal|members?|here|on the site|this site|the site|platform|app|"
    r"community|you'?re not alone|thousands|hundreds|millions|majority|typical(ly)?|often|usually|"
    r"frequently|countless|numerous|widely|well[- ]populated|no shortage|in good company)\b")
# Evidence nobody can check.
EVIDENCE = re.compile(r"(?i)\b(surveys?|stud(y|ies)|research(ers)?|data|statistics?|scientists?|"
                      r"universit(y|ies)|psycholog(y|ists?)|experts?|polls?|report(s|ed)?)\b")
DASHES = re.compile(r"[‒–—―]| - |--")
DIGITS = re.compile(r"\d|%")


def line_faults(line, tokens_allowed=False):
    """Why a line breaks the rule, as a list; empty when it holds."""
    faults = []
    bare = TOKENS.sub("", line) if tokens_allowed else line
    if "{" in bare or "}" in bare:
        faults.append("an unknown token")
    if len(TOKENS.sub("Somewhere", line)) > MAX:
        faults.append(f"over {MAX} characters")
    for name, rx in (("a claim word", CLAIMS), ("evidence", EVIDENCE), ("a dash", DASHES), ("a number", DIGITS)):
        m = rx.search(bare)
        if m:
            faults.append(f"{name} ({m.group(0)!r})")
    if not line.strip() or line != line.strip():
        faults.append("empty or padded")
    elif not re.search(r"[.!?]$", line):
        faults.append("not a sentence")
    return faults


def check():
    faults = []
    try:
        steps = json.loads((OUT / "steps.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return [f"steps.json: {e}"]
    edition = steps.get("edition")
    for moment in MOMENTS:
        lines = steps.get("steps", {}).get(moment) or []
        if len(lines) < 2:
            faults.append(f"steps.json: {moment} needs at least two lines, so the card can vary")
        for line in lines:
            faults += [f"steps.json: {moment}: {f}: {line!r}" for f in line_faults(line, tokens_allowed=True)]
    unknown = set(steps.get("steps", {})) - set(MOMENTS)
    faults += [f"steps.json: no moment called {m!r}" for m in sorted(unknown)]
    for platform in PLATFORMS:
        path = OUT / f"{platform}.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            faults.append(f"{path.name}: {e}")
            continue
        if data.get("platform") != platform:
            faults.append(f"{path.name}: says it is {data.get('platform')!r}, not {platform}")
        if data.get("edition") != edition:
            faults.append(f"{path.name}: edition {data.get('edition')}, steps.json is {edition}")
        for label, lines in data.get("interests", {}).items():
            if not lines or len(set(lines)) != len(lines):
                faults.append(f"{path.name}: {label}: no lines, or a line twice")
            for line in lines:
                faults += [f"{path.name}: {label}: {f}: {line!r}" for f in line_faults(line)]
    return faults


def import_batches(folder):
    """The interest files from reviewed batches: {platform, items: [{label, lines}]}."""
    steps = json.loads((OUT / "steps.json").read_text(encoding="utf-8"))
    edition = steps["edition"]
    for platform in PLATFORMS:
        interests = {}
        for batch in sorted(Path(folder).glob(f"{platform}-*.json")):
            for item in json.loads(batch.read_text(encoding="utf-8"))["items"]:
                label = item["label"].strip()
                if label in interests:
                    interests[label] = list(dict.fromkeys(interests[label] + item["lines"]))
                else:
                    interests[label] = item["lines"]
        data = {"edition": edition, "platform": platform,
                "source": "Rewritten from the registration-flow skill's interest tips.",
                "interests": dict(sorted(interests.items(), key=lambda kv: kv[0].lower()))}
        (OUT / f"{platform}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n",
                                              encoding="utf-8", newline="\n")
        print(f"  {platform}: {len(interests)} interests, "
              f"{sum(len(v) for v in interests.values())} lines")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--import", dest="folder", help="reviewed batches to write the interest files from")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    if args.folder:
        import_batches(args.folder)
    faults = check()
    for f in faults:
        print(f"  FAIL  {f}")
    if not faults:
        print("clean: every sign-up line holds to the rule")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(main())
