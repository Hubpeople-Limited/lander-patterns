#!/usr/bin/env python3
"""Fetch every placeholder's CDN copy and compare it with the file here.

Brands reference the CDN URL, never the file in lib/placeholders/, so a URL
that stopped answering or serves other bytes is a broken picture on every
page that placed it. lint.py checks the manifest against the files; this
checks the manifest against the CDN.

Optional and online: run it after uploading a placeholder. CI does not run
it, because a network failure is not a fault in a pull request.

    python ci/check_placeholder_urls.py

Exit codes: 0 every copy answers as image/svg+xml with the recorded sha256;
1 at least one does not.
"""
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lint import digest_bytes  # noqa: E402

MANIFEST = Path(__file__).resolve().parent.parent / "lib" / "placeholders" / "placeholders.json"


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "lander-patterns-check"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.status, response.headers.get_content_type(), response.read()


def faults(manifest=MANIFEST, fetch=fetch):
    entries = json.loads(Path(manifest).read_text(encoding="utf-8"))["placeholders"]
    out = []
    for key in sorted(entries):
        url, want = entries[key]["url"], entries[key]["sha256"]
        try:
            status, content_type, body = fetch(url)
        except Exception as e:  # any failure to fetch is a finding, never a crash
            out.append(f"{key}: {url} did not fetch ({e})")
            continue
        if status != 200:
            out.append(f"{key}: {url} answered {status}")
        elif content_type != "image/svg+xml":
            out.append(f"{key}: {url} is served as {content_type}, not image/svg+xml")
        elif digest_bytes(body) != want:
            out.append(f"{key}: {url} is not the file recorded - upload it again "
                       "and record the new url and sha256")
    return out


def main():
    found = faults()
    for line in found:
        print(f"  FAIL {line}")
    print(f"{len(found)} placeholder copy(ies) wrong" if found
          else "clean: every placeholder copy answers and matches its file")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
