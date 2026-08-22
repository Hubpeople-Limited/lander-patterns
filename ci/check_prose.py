#!/usr/bin/env python3
"""Check commit messages and pull-request text against the writing policy.

This checks PROSE WE PUBLISH ABOUT the code - commit messages, pull-request
titles and bodies - not the code itself. Pointing it at a source file will
produce false positives, because ordinary code contains ordinary words.

Usage:
  python ci/check_prose.py --range origin/main..HEAD   commit messages in a range
  python ci/check_prose.py --file body.txt             a pull-request body
  python ci/check_prose.py --text "..."                one string

Exit code 0 = clean. Any finding prints `where: rule: detail` and exits 1.

This repository is public and permanently readable. A commit message is not
a note to a colleague: it is a paragraph a stranger can read years later,
attached to the change forever, and it cannot be edited once it is out. The
policy, and the sources behind it, are in WRITING.md; this file enforces the part a machine can see, which
is vocabulary. Tone is a review question.
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Someone's job, or someone's person. A change is described by what it does,
# never by who did it or who got it wrong.
PEOPLE = [
    "the designer", "our designer", "the developer", "our developer",
    "the reviewer", "the contributor", "the author of", "the previous dev",
    "the team", "our team", "the client", "the customer", "the partner",
    "the agency", "the intern", "whoever wrote", "someone wrote",
]

# Blame, and its passive-aggressive cousins. A defect is stated as a
# condition of the code, not as a failing of a person.
BLAME = [
    "should have", "shouldn't have", "should never have", "failed to",
    "forgot to", "neglected to", "didn't bother", "did not bother",
    "sloppy", "careless", "obviously wrong", "clearly wrong",
    "nonsense", "no idea why", "who thought", "makes no sense",
    "badly written", "poorly written", "a mess", "hack job",
]

# How the change came to be. Interesting internally, noise in public, and it
# leaks working method.
PROCESS = [
    "review round", "hostile review", "code review found", "the reviewer",
    "round 1", "round 2", "round 3", "round 4", "round 5", "round 6",
    "critic", "conversation", "prompt", "llm", "chatgpt", "claude",
    "sprint", "standup", "retro", "ticket", "jira", "azure devops",
    "backlog", "story points",
]

# Precise defect description. In a public repo this is a map of where the
# weakness is in every older version somebody is still pinned to, so the
# convention everywhere is: describe the fix, not the hole.
DISCLOSURE = [
    "vulnerability", "vulnerable", "exploit", "exploitable",
    "attack vector", "can be abused", "allows an attacker",
    "security hole", "security fix", "use after free", "use-after-free",
    "overflow", "xss", "csrf", "sql injection", "script injection",
    "proof of concept", "reproduction steps",
]

CATEGORIES = [
    ("people", PEOPLE,
     "name the change, not a person or a role"),
    ("blame", BLAME,
     "state the condition of the code, not a failing"),
    ("process", PROCESS,
     "how the change came about is internal; say what it does"),
    ("disclosure", DISCLOSURE,
     "describe the fix, not the weakness - older versions are still in use"),
]

findings = []


def needles():
    """The private list of strings that must never appear publicly. Supplied
    at scan time, never stored here."""
    raw = os.environ.get("LANDER_LEAK_NEEDLES")
    local = ROOT / "ci" / "leak-needles.local"
    if raw is None and local.is_file():
        raw = local.read_text(encoding="utf-8")
    if not raw:
        return None
    return [n.strip().lower() for n in raw.splitlines() if n.strip()] or None


def check(where, text, leak_list):
    low = text.lower()
    # A term inside quotes or backticks is being MENTIONED, not used. A commit
    # that changes which words a checker bans has to be able to name them, and
    # this gate rejected exactly that commit - which makes the rule
    # unstateable in its own history. Quoting is the escape hatch, and it is
    # deliberately narrow: narration in quotation marks is still narration and
    # still reads as narration, so nothing is gained by hiding it there.
    unquoted = re.sub(r"\"[^\"]*\"|'[^']*'|`[^`]*`", " ", low)
    for name, terms, why in CATEGORIES:
        for term in terms:
            if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", unquoted):
                findings.append(f"{where}: {name}: says '{term}' - {why}")
                break
    # First person. A commit is written in the imperative about the code.
    if re.search(r"(?<!\w)(i|my|we|our)\s+(think|thought|chose|decided|"
                 r"found|missed|broke|added it because)(?!\w)", low):
        findings.append(f"{where}: voice: first-person narration - describe "
                        "the change, not the author's reasoning")
    if leak_list:
        for n in leak_list:
            if n in low:
                findings.append(f"{where}: leak: a private string appears "
                                "(the string itself is not printed)")
                break


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--range")
    ap.add_argument("--file")
    ap.add_argument("--text")
    args = ap.parse_args()

    leak_list = needles()
    if leak_list is None and os.environ.get(
            "LANDER_LEAK_SKIP", "").lower() != "true":
        print("ci/check_prose.py: no needle list supplied - set "
              "LANDER_LEAK_NEEDLES. Refusing to report clean on a check that "
              "did not run", file=sys.stderr)
        return 1

    if args.range:
        out = subprocess.run(
            ["git", "log", "--format=%H%x1f%B%x1e", args.range],
            capture_output=True, text=True, cwd=ROOT)
        if out.returncode != 0:
            print(f"cannot read {args.range}: {out.stderr.strip()}",
                  file=sys.stderr)
            return 1
        for record in out.stdout.split("\x1e"):
            if not record.strip():
                continue
            sha, _, body = record.strip().partition("\x1f")
            check(f"commit {sha[:8]}", body, leak_list)
    elif args.file:
        check(args.file, Path(args.file).read_text(encoding="utf-8"), leak_list)
    elif args.text:
        check("text", args.text, leak_list)
    else:
        ap.print_help()
        return 1

    if findings:
        print("\n".join(findings))
        print(f"\n{len(findings)} finding(s). See WRITING.md.")
        return 1
    print("prose: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
