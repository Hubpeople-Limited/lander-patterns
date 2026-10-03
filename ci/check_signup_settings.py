#!/usr/bin/env python3
"""Hold the sign-up card's list of settings and words to the behaviour bundle.

patterns/signup-card/settings.json is the one machine-readable list of what a
page can set on the card: every data-hub-signup-* setting with the values it
takes and its default, which settings have a -wide twin read from 60rem, and
every word the card shows with its English default, the {tokens} it may carry
and, for a list, how many entries. The toolkit reads it to let a page set any
of them and to check what a page set. A list that drifts from lib/hub.js tells
a page it can set something the card ignores, or hides something it could
set, so this compares the two:

  words     the list's words are exactly SIGNUP_WORDS, each with the same
            default; its tokens are the ones that default carries, in order;
            a list word's count is the default's
  settings  every name hub.js reads with opt() or optAt() that is not a word
            is listed, and every listed setting is read: by name, as an
            interest step (chipStep), or as a moment's own lines (say-<moment>
            for each moment speak() is called with)
  twins     the settings marked wide are exactly the ones read with optAt()
  values    every value a choice takes other than its default is a word the
            bundle names (a value nothing names does nothing); a screens
            setting's steps are SIGNUP_STEPS, a moments setting's moments
            SIGNUP_MOMENTS
  shape     every row has a kind the toolkit knows, and the fields that kind
            needs

    python ci/check_signup_settings.py
    python ci/check_signup_settings.py --list path/settings.json --bundle path/hub.js

Exit codes: 0 clean; 1 at least one disagreement; 2 a file is missing or
unreadable.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIST = ROOT / "patterns" / "signup-card" / "settings.json"
BUNDLE = ROOT / "lib" / "hub.js"

# Each kind of setting, and the fields a row of that kind must carry. The
# toolkit checks a page's value by kind, so a kind it does not know is a
# setting it cannot check.
KINDS = {"choice": ("values", "default"), "age": ("values", "min", "max", "default"),
         "labels": (), "places": (), "guid": (), "url": (), "lines": ("tokens",),
         "label-lines": ("tokens",), "screens": ("steps",), "moments": ("values", "moments", "default")}
READ = re.compile(r'\bopt(?:At)?\("([a-z][\w-]*)"\)')
TWIN = re.compile(r'\boptAt\("([a-z][\w-]*)"\)')
CHIPS = re.compile(r'\bchipStep\("([a-z][\w-]*)"\)')
SPOKEN = re.compile(r'\bspeak\("([a-z][\w-]*)"')
WORDS = re.compile(r"const SIGNUP_WORDS = \{(.*?)\n\};", re.S)
PAIR = re.compile(r'"([\w-]+)":\s*"((?:[^"\\]|\\.)*)"')
TOKEN = re.compile(r"\{(\w+)\}")


def constant_list(js, name):
    """A one-line array constant in the bundle, or None."""
    m = re.search(rf"const {name} = (\[[^\]]*\]);", js)
    return json.loads(m.group(1)) if m else None


def named(js):
    """Every word the bundle names: its string literals and its object keys."""
    return set(re.findall(r'"([^"\\\n]*)"', js)) | set(re.findall(r"\b([a-z][\w-]*)\s*:", js))


def faults(table, js):
    """Every way `table` (the parsed list) and `js` (the bundle) disagree."""
    out = []
    m = WORDS.search(js)
    if not m:
        return ["hub.js: no SIGNUP_WORDS to compare the list's words with"]
    words = {k: json.loads(f'"{v}"') for k, v in PAIR.findall(m.group(1))}
    listed = table.get("words") or {}
    for k in sorted(set(words) - set(listed)):
        out.append(f"words: {k!r} is a word the card shows and the list leaves out")
    for k in sorted(set(listed) - set(words)):
        out.append(f"words: {k!r} is listed and the card has no such word")
    for k in sorted(set(words) & set(listed)):
        row = listed[k]
        if row.get("default") != words[k]:
            out.append(f"words: {k!r} defaults to {words[k]!r} in hub.js and {row.get('default')!r} in the list")
        carried = []
        for t in TOKEN.findall(words[k]):
            if t not in carried:
                carried.append(t)
        if list(row.get("tokens") or []) != carried:
            out.append(f"words: {k!r} carries {carried} in hub.js and the list says {row.get('tokens') or []}")
        if "list" in row and row["list"] != len(words[k].split(";")):
            out.append(f"words: {k!r} is a list of {len(words[k].split(';'))} in hub.js and the list says {row['list']}")
    settings = table.get("settings") or {}
    twins = set(TWIN.findall(js))
    read = {n for n in READ.findall(js) if n not in words}
    read = {n[:-5] if n.endswith("-wide") and n[:-5] in twins else n for n in read}
    read |= set(CHIPS.findall(js)) | {f"say-{m}" for m in SPOKEN.findall(js)}
    for n in sorted(read - set(settings)):
        out.append(f"settings: hub.js reads {n!r} and the list leaves it out")
    for n in sorted(set(settings) - read):
        out.append(f"settings: {n!r} is listed and hub.js never reads it")
    marked = {n for n, row in settings.items() if row.get("wide")}
    for n in sorted(twins ^ marked):
        out.append(f"settings: {n!r} " + ("is read with a -wide twin and not marked wide" if n in twins
                                          else "is marked wide and hub.js reads no twin for it"))
    words_named = named(js)
    for n, row in sorted(settings.items()):
        kind = row.get("kind")
        if kind not in KINDS:
            out.append(f"settings: {n!r} has kind {kind!r}; the kinds are {', '.join(KINDS)}")
            continue
        for f in KINDS[kind]:
            if f not in row:
                out.append(f"settings: {n!r} ({kind}) has no {f!r}")
        if kind in ("choice", "moments"):
            for v in row.get("values") or []:
                if v != row.get("default") and v not in words_named:
                    out.append(f"settings: {n!r} takes {v!r}, which hub.js never names, so it would do nothing")
        if kind == "screens" and row.get("steps") != constant_list(js, "SIGNUP_STEPS"):
            out.append(f"settings: {n!r} lists the steps {row.get('steps')} and hub.js's SIGNUP_STEPS are "
                       f"{constant_list(js, 'SIGNUP_STEPS')}")
        if kind == "moments" and row.get("moments") != constant_list(js, "SIGNUP_MOMENTS"):
            out.append(f"settings: {n!r} lists the moments {row.get('moments')} and hub.js's SIGNUP_MOMENTS are "
                       f"{constant_list(js, 'SIGNUP_MOMENTS')}")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Hold the sign-up card's settings list to the bundle.")
    ap.add_argument("--list", default=str(LIST))
    ap.add_argument("--bundle", default=str(BUNDLE))
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    try:
        table = json.loads(Path(args.list).read_text(encoding="utf-8"))
        js = Path(args.bundle).read_text(encoding="utf-8")
    except (OSError, ValueError) as e:
        print(f"signup settings: cannot read the list or the bundle - {e}")
        return 2
    found = faults(table, js)
    for line in found:
        print(f"  FAIL  {line}")
    if found:
        print(f"\n{len(found)} disagreement(s) between {Path(args.list).name} and {Path(args.bundle).name}.")
        return 1
    print(f"  clean: {len(table['settings'])} settings and {len(table['words'])} words, as lib/hub.js reads them")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
