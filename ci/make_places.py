#!/usr/bin/env python3
"""Give every town in the platform's location reference a latitude and longitude.

The signup behaviour asks where a visitor lives and sends the join flow a
decimal latitude and longitude, the location form its registration link takes.
The platform publishes its places - country, region, town, spelled the way it
holds them - with no coordinates. This matches each town to GeoNames
(geonames.org, CC BY 4.0) and writes lib/places/: one file per country and an
index. publish_hub.py serves them beside the bundle, in a folder named for
their edition, and the bundle names the edition it was built for.

A town is placed only where the match is safe: the name found inside its own
region; a name unique in the country, wherever the reference files it; or,
where the platform's region is an older county than the one GeoNames records,
the candidate nearest the region's other towns and within their spread. Anything else is kept with no coordinates: the visitor can still
pick it, the member search still narrows by it, and the join flow asks for the
location itself.

    python ci/make_places.py            fetch, match, write lib/places/, report
    python ci/make_places.py --check    verify what is committed, fetch nothing

Downloads go to .cache/ (ignored). Rerun when the platform's reference moves:
its "generated" date is part of the edition.
"""

import argparse
import collections
import difflib
import io
import json
import math
import statistics
import sys
import unicodedata
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "lib" / "places"
CACHE = ROOT / ".cache" / "places"
REFERENCE = "https://help.hubpeople.ai/data"
GEONAMES = "https://download.geonames.org/export/dump"
GEONAMES_ZIP = "https://download.geonames.org/export/zip"
# Countries whose visitors can give a postal code the join flow reads, and
# GeoNames' code for its postal file. The codes are split by first character, so
# a card loads only the file for the code being typed.
POSTAL = {"USA": "US"}
# Bumped when the matching changes, so a new match of the same reference is a
# new edition and a published one never changes.
MATCHER = 3
# The platform's country names, as its reference spells them, to ISO codes.
ISO = {"Argentina": "AR", "Australia": "AU", "Brazil": "BR", "Canada": "CA",
       "Ireland": "IE", "New Zealand": "NZ", "South Africa": "ZA", "Spain": "ES",
       "UK": "GB", "USA": "US"}
SOURCE = ("Coordinates from GeoNames (geonames.org), CC BY 4.0. Place names from "
          "the HubPeople location reference.")


def slug(country):
    return country.lower().replace(" ", "-")


# Spellings that differ only by convention: the reference writes "Mc Rae" and
# "Saint", GeoNames "McRae" and "St." - so both sides are folded the same way.
ABBREVIATIONS = {"st": "saint", "ste": "sainte", "mt": "mount", "ft": "fort", "pt": "point"}


def norm(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().casefold()
    words = text.replace("-", " ").replace(".", " ").replace("'", " ").split()
    words = [ABBREVIATIONS.get(w, w) for w in words]
    out = []
    for w in words:
        # "Mc Rae", "O Fallon": a prefix written apart is the same name.
        if out and out[-1] in ("mc", "o"):
            out[-1] += w
        else:
            out.append(w)
    return " ".join(out)


def fetch(url, name):
    path = CACHE / name
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "lander-patterns make_places"})
        with urllib.request.urlopen(req, timeout=300) as r:
            path.write_bytes(r.read())
    return path


def admin_names(name):
    names = {}
    for line in fetch(f"{GEONAMES}/{name}", name).read_text(encoding="utf-8").splitlines():
        code, _, ascii_name, _ = line.split("\t")
        names[code] = norm(ascii_name)
    return names


def km(a, b):
    return 111.2 * math.hypot(a[0] - b[0], (a[1] - b[1]) * math.cos(math.radians((a[0] + b[0]) / 2)))


def gazetteer(iso, admin1, admin2):
    """Every populated place and administrative area, by each of its names."""
    index = collections.defaultdict(list)
    with zipfile.ZipFile(fetch(f"{GEONAMES}/{iso}.zip", f"{iso}.zip")) as z:
        for line in io.TextIOWrapper(z.open(f"{iso}.txt"), encoding="utf-8"):
            f = line.rstrip("\n").split("\t")
            if f[6] not in ("P", "A"):
                continue
            place = {"at": (float(f[4]), float(f[5])), "populated": f[6] == "P",
                     "people": int(f[14] or 0), "names": {norm(f[1]), norm(f[2])},
                     "areas": {admin1.get(f"{iso}.{f[10]}", ""),
                               admin2.get(f"{iso}.{f[10]}.{f[11]}", "")} - {""}}
            for n in {norm(f[1]), norm(f[2])} | {norm(a) for a in f[3].split(",") if a}:
                if n:
                    index[n].append(place)
    return index


def in_region(region, place):
    r = norm(region.split(":")[-1])
    return bool(r) and any(r in a or a in r for a in place["areas"])


def match(regions, index):
    """({region: {town: [lat, long] or None}}, {region: {alias: town}}, and how
    each town was placed)."""
    placed = {region: {} for region in regions}
    people = {}
    chosen = {}
    how = collections.Counter()
    pending = []
    for region, towns in regions.items():
        for town in towns:
            cands = index.get(norm(town), [])
            here = [c for c in cands if in_region(region, c)]
            if here:
                best = max(here, key=lambda c: (c["populated"], c["people"]))
                placed[region][town] = best["at"]
                people[(region, town)] = best["people"]
                chosen[(region, town)] = best
                how["in its region"] += 1
            elif cands:
                pending.append((region, town, cands))
            else:
                how["no match"] += 1
    # A town whose name is unique in the country is where GeoNames has it, even
    # where the reference files it under an older county or another region:
    # the visitor who picks it lives there. These also anchor a region no town
    # matched by name.
    for region, town, cands in pending:
        spots = {(round(c["at"][0], 1), round(c["at"][1], 1)) for c in cands}
        if len(spots) == 1:
            placed[region][town] = cands[0]["at"]
            people[(region, town)] = max(c["people"] for c in cands)
            chosen[(region, town)] = cands[0]
    for region, town, cands in pending:
        if town in placed[region]:
            how["unique in the country"] += 1
            continue
        pts = list(placed[region].values())
        if not pts:
            how["too far to trust"] += 1
            continue
        mid = (statistics.median(p[0] for p in pts), statistics.median(p[1] for p in pts))
        spread = sorted(km(p, mid) for p in pts)[int(0.9 * (len(pts) - 1))]
        reach = min(300, max(40, 1.5 * spread))
        best = min(cands, key=lambda c: km(c["at"], mid))
        if km(best["at"], mid) <= reach:
            placed[region][town] = best["at"]
            people[(region, town)] = best["people"]
            chosen[(region, town)] = best
            how["nearest its region"] += 1
        else:
            how["too far to trust"] += 1
    # Several of the reference's names for one place in one region - Peterborough,
    # Peterbrough, Petersborough - are one town to a visitor: the one GeoNames
    # spells is shown, and the others are kept as its aliases.
    groups = collections.defaultdict(list)
    for (region, town), place in chosen.items():
        groups[(region, id(place))].append(town)
    aliases = {}
    for (region, _), towns in groups.items():
        if len(towns) < 2:
            continue
        place = chosen[(region, towns[0])]
        proper = [t for t in towns if norm(t) in place["names"]]
        keep = proper[0] if proper else max(
            towns, key=lambda t: max(difflib.SequenceMatcher(None, norm(t), n).ratio() for n in place["names"]))
        for t in towns:
            if t != keep:
                aliases.setdefault(region, {})[t] = keep
                how["an alias of another name"] += 1
    # Biggest first, so a visitor typing "Dall" in Texas is offered Dallas
    # before Dallardsville; a town with no coordinates goes last.
    out = {}
    for region, towns in regions.items():
        shown = [t for t in towns if t not in aliases.get(region, {})]
        order = sorted(shown, key=lambda t: (t not in placed[region], -people.get((region, t), 0)))
        out[region] = {t: ([round(placed[region][t][0], 3), round(placed[region][t][1], 3)]
                           if t in placed[region] else None) for t in order}
    # How many people each region's towns hold, rounded: the card offers the
    # largest regions first.
    sizes = {region: round(sum(people.get((region, t), 0) for t in out[region]), -3) for region in out}
    return out, aliases, sizes, how


def postal(country, iso, regions, aliases):
    """{first digit: {code: [region index, town or ""]}} in the platform's own
    names: the region the code is in, and its town where the reference lists it."""
    names = list(regions)
    by_norm = {norm(r.split(":")[-1]): i for i, r in enumerate(names)}
    towns = [{norm(t): t for t in regions[r]} for r in names]
    for i, r in enumerate(names):
        for alias, town in (aliases.get(r) or {}).items():
            towns[i].setdefault(norm(alias), town)
    out = collections.defaultdict(dict)
    placed = unplaced = 0
    with zipfile.ZipFile(fetch(f"{GEONAMES_ZIP}/{iso}.zip", f"{iso}-postal.zip")) as z:
        for line in io.TextIOWrapper(z.open(f"{iso}.txt"), encoding="utf-8"):
            f = line.rstrip("\n").split("\t")
            code, place, state = f[1], f[2], f[3]
            i = by_norm.get(norm(state))
            if i is None:
                unplaced += 1
                continue
            out[code[0]][code] = [i, towns[i].get(norm(place), "")]
            placed += 1
    return out, names, placed, unplaced


def build():
    admin1, admin2 = admin_names("admin1CodesASCII.txt"), admin_names("admin2Codes.txt")
    reference = json.loads(fetch(f"{REFERENCE}/countries-regions.json", "countries-regions.json")
                           .read_text(encoding="utf-8"))
    generated = reference["generated"]
    edition = f"{generated}.{MATCHER}"
    files, index = {}, {"edition": edition, "source": SOURCE, "countries": {}}
    for country in sorted(reference["countries"]):
        if country not in ISO:
            raise SystemExit(f"{country}: not in ISO - add its code before matching it")
        data = json.loads(fetch(f"{REFERENCE}/locations-{slug(country)}.json",
                                f"locations-{slug(country)}.json").read_text(encoding="utf-8"))
        if data.get("generated") != generated:
            raise SystemExit(f"{country}: its town list is from {data.get('generated')} and the "
                             f"region list from {generated} - fetch both again")
        regions, aliases, sizes, how = match(data["regions"], gazetteer(ISO[country], admin1, admin2))
        towns = sum(len(t) for t in regions.values())
        with_place = sum(1 for t in regions.values() for v in t.values() if v)
        files[f"{slug(country)}.json"] = {"edition": edition, "country": country, "source": SOURCE,
                                          "regions": regions, "aliases": aliases, "sizes": sizes}
        if country in POSTAL:
            codes, names, placed, unplaced = postal(country, POSTAL[country], regions, aliases)
            pattern = f"{slug(country)}-postal-{{}}.json"
            files[f"{slug(country)}.json"]["postal"] = pattern
            for digit, entries in sorted(codes.items()):
                files[pattern.format(digit)] = {"edition": edition, "country": country, "source": SOURCE,
                                                "regions": names, "codes": entries}
            with_town = sum(1 for e in codes.values() for v in e.values() if v[1])
            print(f"  {country:13s} {placed} postal codes in {len(codes)} files, {with_town / placed:.1%} "
                  f"with a town the reference lists, {unplaced} in no region it holds")
        index["countries"][country] = {"file": f"{slug(country)}.json",
                                       "regions": list(regions), "towns": towns, "placed": with_place}
        print(f"  {country:13s} {towns:6d} towns in {len(regions):3d} regions, "
              f"{with_place / towns:5.1%} placed  ({', '.join(f'{k} {v}' for k, v in how.most_common())})")
    files["index.json"] = index
    return files


def dump(data):
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=False) + "\n"


def check():
    """What is committed hangs together: an index naming every country file, one
    edition throughout, and nothing but two-number places or nulls."""
    faults = []
    try:
        index = json.loads((OUT / "index.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return [f"lib/places/index.json: {e}"]
    edition = index.get("edition")
    known = set()
    for country, row in index.get("countries", {}).items():
        path = OUT / row["file"]
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            faults.append(f"{path.name}: {e}")
            continue
        if data.get("edition") != edition or data.get("country") != country:
            faults.append(f"{path.name}: edition {data.get('edition')} / {data.get('country')}, "
                          f"the index says {edition} / {country}")
        if list(data["regions"]) != row["regions"]:
            faults.append(f"{path.name}: its regions are not the index's")
        for region, names in (data.get("aliases") or {}).items():
            for alias, town in names.items():
                if town not in data["regions"].get(region, {}):
                    faults.append(f"{path.name}: {region} / {alias} is an alias of {town!r}, which is not listed")
        for region, towns in data["regions"].items():
            for town, at in towns.items():
                if at is not None and not (isinstance(at, list) and len(at) == 2
                                           and -90 <= at[0] <= 90 and -180 <= at[1] <= 180):
                    faults.append(f"{path.name}: {region} / {town} has {at!r}")
        pattern = data.get("postal")
        postal_files = sorted(OUT.glob(pattern.replace("{}", "*"))) if pattern else []
        for pf in postal_files:
            codes = json.loads(pf.read_text(encoding="utf-8"))
            if codes.get("edition") != edition or codes.get("regions") != list(data["regions"]):
                faults.append(f"{pf.name}: not the edition or regions of {path.name}")
            bad = [c for c, v in codes.get("codes", {}).items()
                   if not (isinstance(v, list) and len(v) == 2 and 0 <= v[0] < len(codes["regions"])
                           and (not v[1] or v[1] in data["regions"][codes["regions"][v[0]]]))]
            faults += [f"{pf.name}: {c} names no listed region and town" for c in bad[:5]]
        known.update(p.name for p in postal_files)
    stray = {p.name for p in OUT.glob("*.json")} - {"index.json"} - known - \
        {r["file"] for r in index.get("countries", {}).values()}
    faults += [f"{name}: not in the index" for name in sorted(stray)]
    return faults


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="verify lib/places/ and fetch nothing")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    if args.check:
        faults = check()
        for f in faults:
            print(f"  FAIL  {f}")
        if not faults:
            index = json.loads((OUT / "index.json").read_text(encoding="utf-8"))
            print(f"clean: lib/places/ edition {index['edition']}, "
                  f"{len(index['countries'])} countries")
        return 1 if faults else 0
    files = build()
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.json"):
        old.unlink()
    for name, data in files.items():
        (OUT / name).write_text(dump(data), encoding="utf-8", newline="\n")
    print(f"wrote lib/places/, edition {files['index.json']['edition']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
