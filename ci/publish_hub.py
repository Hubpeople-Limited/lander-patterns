#!/usr/bin/env python3
"""Build the published form of lib/hub.js into publish/.

The bundle is delivered to pages rather than copied into them, so it needs two
URL forms and they behave differently:

    /hub-behaviours/1.4.0/hub.min.js    pinned, immutable, cached for a year
    /hub-behaviours/v1/hub.min.js       the current 1.x, cached for an hour

A served page loads the floating one, so a released fix reaches every live page
without that page being rebuilt. The pinned one is what a site references when
it wants to hold a version still, and what a floating URL is rolled back to.
Once published its bytes never change, because something out there is holding
it.

`publish/` only ever grows, and it is committed. The host replaces its whole
contents on each deploy, so the accumulated tree in the repository is both the
record of every version ever served and the thing that stops a deploy quietly
deleting a URL a site still points at.

    python ci/publish_hub.py             build, write, update the manifest
    python ci/publish_hub.py --dry-run   the same work against a copy
    python ci/publish_hub.py --check     verify what is committed, build nothing

Minification is esbuild through npx, pinned. --minified supplies the file from
somewhere else and skips the download.
"""

import argparse
import base64
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "hub-behaviours"
ESBUILD = "esbuild@0.25.0"

# The floating URL is a compromise between a fix arriving and a page paying for
# it. Fifty minutes of max-age with a day of stale-while-revalidate means a
# repeat visitor is never blocked on the network for it, and a release is live
# within the hour.
FLOATING_CACHE = "public, max-age=3000, stale-while-revalidate=86400"
PINNED_CACHE = "public, max-age=31536000, immutable"

# A module script is fetched in CORS mode whatever its origin, so a bundle
# served from a different host than the page needs this header or the browser
# refuses it before parsing a byte.
SHARED_HEADERS = {
    "access-control-allow-origin": "*",
    "cross-origin-resource-policy": "cross-origin",
    "x-content-type-options": "nosniff",
}

SEMVER = re.compile(r"\d+\.\d+\.\d+")
VERSION = re.compile(r"window\.HubBehaviours\s*=\s*\{[^}]*?version\s*:\s*"
                     r"[\"']([^\"']+)[\"']", re.S)


def read_version(text):
    """The single source of truth for what is published.

    The constant is what the bundle reports about itself at runtime, so
    publishing anything else would leave a page unable to say truthfully which
    version it is running.
    """
    m = VERSION.search(text)
    if not m:
        return None, ("the bundle does not declare a version on "
                      "window.HubBehaviours, so there is nothing to publish "
                      "it as")
    version = m.group(1).strip()
    if not SEMVER.fullmatch(version):
        return None, (f"version {version!r} is not major.minor.patch - the "
                      f"URL shape and the floating major are both derived "
                      f"from it")
    return version, None


def integrity(data):
    """The hash that goes in a tag's integrity attribute.

    Only ever published for a pinned URL: a floating URL is meant to change
    under a page that already holds it, which is exactly what the attribute
    exists to prevent.
    """
    return "sha384-" + base64.b64encode(
        hashlib.sha384(data).digest()).decode("ascii")


def minify(source, out_dir):
    """esbuild, as a module, with a sourcemap beside it.

    The bundle ships readable too. Someone looking at why a page behaves as it
    does gets the source rather than one long line, and it costs a file.
    """
    out = out_dir / "hub.min.js"
    run = subprocess.run(
        ["npx", "--yes", ESBUILD, str(source), "--minify", "--format=esm",
         "--target=es2020", "--sourcemap", f"--outfile={out}"],
        capture_output=True, text=True, shell=(sys.platform == "win32"))
    if run.returncode != 0:
        return None, ("esbuild did not run, so nothing was minified:\n"
                      + (run.stderr or run.stdout).strip())
    return out, None


def config(majors):
    """The host's routing file, generated rather than hand-kept.

    The cache headers are the whole delivery contract, and a floating URL
    cached like an immutable one strands every page on whatever it fetched
    last - so the rules are written from the same list the files are.
    """
    routes = [{"route": f"/{BASE}/v{major}/*",
               "headers": {"cache-control": FLOATING_CACHE, **SHARED_HEADERS}}
              for major in majors]
    routes.append({"route": f"/{BASE}/manifest.json",
                   "headers": {"cache-control": FLOATING_CACHE,
                               **SHARED_HEADERS}})
    # Everything else under the prefix is a pinned version directory. The
    # floating rules are above it and evaluation stops at the first match, so
    # this can be the broad one.
    routes.append({"route": f"/{BASE}/*",
                   "headers": {"cache-control": PINNED_CACHE,
                               **SHARED_HEADERS}})
    return {
        "trailingSlash": "never",
        "routes": routes,
        "mimeTypes": {".js": "text/javascript", ".map": "application/json"},
        # A host that serves one page for anything it does not recognise would
        # answer a mistyped version URL with HTML and a 200, and a module
        # script would try to parse it. Everything under the prefix is excluded
        # so a URL that does not exist says so.
        "navigationFallback": {"rewrite": "/404.html",
                               "exclude": [f"/{BASE}/*"]},
        "responseOverrides": {"404": {"rewrite": "/404.html"}},
    }


INDEX = """<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Behaviour bundle</title>
<style>
  body {{ font: 16px/1.6 system-ui, sans-serif; margin: 3rem auto;
         max-width: 44rem; padding: 0 1.25rem; color: #16181d;
         background: #fff; }}
  code, pre {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
              font-size: 0.9em; }}
  pre {{ background: #f4f5f7; padding: 0.9rem 1rem; border-radius: 6px;
         overflow-x: auto; }}
  h1 {{ font-size: 1.4rem; }}
  h2 {{ font-size: 1.05rem; margin-top: 2rem; }}
  @media (prefers-color-scheme: dark) {{
    body {{ color: #e8eaed; background: #16181d; }}
    pre {{ background: #23262d; }}
  }}
</style>
<h1>Behaviour bundle</h1>
<p>The JavaScript half of the pattern library, served as an ES module. Markup
opts in with <code>data-hub-module</code> attributes, which do nothing until
this file is on the page.</p>

<h2>Current release</h2>
<p><strong>{version}</strong>, {bytes:,} bytes minified.</p>

<h2>For a page the platform serves</h2>
<p>The floating URL for the major. Each release repoints it, so a fix arrives
without the page being rebuilt.</p>
<pre>&lt;script type="module"
        src="/{base}/v{major}/hub.min.js"&gt;&lt;/script&gt;</pre>

<h2>For a site that holds a version still</h2>
<p>Immutable, so it can carry an integrity hash. A module script is fetched
cross-origin, which is what the <code>crossorigin</code> attribute is for.</p>
<pre>&lt;script type="module" crossorigin="anonymous"
        src="/{base}/{version}/hub.min.js"
        integrity="{integrity}"&gt;&lt;/script&gt;</pre>

<h2>Every version</h2>
<p><a href="/{base}/manifest.json">manifest.json</a> lists each published
version with its integrity hash and the date it was first served.</p>
</html>
"""

NOT_FOUND = """<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="robots" content="noindex">
<title>Not found</title>
<style>body { font: 16px/1.6 system-ui, sans-serif; margin: 4rem auto;
  max-width: 34rem; padding: 0 1.25rem; }</style>
<h1>Not found</h1>
<p>No file is served at this address. <a href="/">What this host serves.</a></p>
</html>
"""


def load_manifest(out):
    path = out / BASE / "manifest.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"versions": {}, "current": {}}


def build(source_path, out, minified_path=None):
    """Everything the host is given, as {relative path: bytes}.

    Returned rather than written so the caller decides whether this run is a
    rehearsal, and so the immutability check has something to compare against
    before anything has been touched.
    """
    source = source_path.read_bytes()
    version, why = read_version(source.decode("utf-8"))
    if version is None:
        return None, why
    major = version.split(".")[0]

    tmp = Path(tempfile.mkdtemp(prefix="hub-publish-"))
    try:
        if minified_path:
            built = tmp / "hub.min.js"
            shutil.copy(minified_path, built)
        else:
            built, why = minify(source_path, tmp)
            if built is None:
                return None, why
        minified = built.read_bytes()
        smap_path = built.with_suffix(".js.map")
        files = {"hub.min.js": minified, "hub.js": source}
        if smap_path.is_file():
            files["hub.min.js.map"] = smap_path.read_bytes()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # A published version is a promise. If this one is already out there with
    # different bytes, the version was not bumped and a page holding the pin
    # would silently be served different code.
    served = out / BASE / version / "hub.min.js"
    if served.is_file() and served.read_bytes() != minified:
        return None, (f"{version} is already published and the bundle no "
                      f"longer builds to it. A published version's bytes "
                      f"never change - bump the version in the bundle instead")

    manifest = load_manifest(out)
    record = manifest["versions"].get(version, {})
    manifest["versions"][version] = {
        "integrity": integrity(minified),
        "bytes": len(minified),
        # First publication, not this run: the date a URL started being served
        # is the useful one, and re-running must not move it.
        "published": record.get("published", date.today().isoformat()),
        "path": f"/{BASE}/{version}/hub.min.js",
    }
    majors = sorted({v.split(".")[0] for v in manifest["versions"]}, key=int)
    manifest["current"] = dict(manifest.get("current", {}))
    manifest["current"][f"v{major}"] = version
    manifest["floating"] = {f"v{m}": f"/{BASE}/v{m}/hub.min.js"
                            for m in majors}

    tree = {}
    for directory in (f"{BASE}/{version}", f"{BASE}/v{major}"):
        for name, data in files.items():
            tree[f"{directory}/{name}"] = data
    tree[f"{BASE}/manifest.json"] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    tree["staticwebapp.config.json"] = (
        json.dumps(config(majors), indent=2) + "\n").encode("utf-8")
    tree["index.html"] = INDEX.format(
        version=version, major=major, base=BASE, bytes=len(minified),
        integrity=manifest["versions"][version]["integrity"]).encode("utf-8")
    tree["404.html"] = NOT_FOUND.encode("utf-8")
    return {"version": version, "files": tree, "minified": len(minified),
            "source": len(source),
            "integrity": manifest["versions"][version]["integrity"]}, None


def write(tree, out):
    for rel, data in tree.items():
        target = out / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=ROOT / "lib" / "hub.js")
    ap.add_argument("--out", type=Path, default=ROOT / "publish")
    ap.add_argument("--check", action="store_true",
                    help="verify what is committed without building")
    ap.add_argument("--dry-run", action="store_true",
                    help="do the whole build against a copy and write nothing")
    ap.add_argument("--minified", type=Path,
                    help="use this file instead of running esbuild")
    args = ap.parse_args(argv)

    if args.check:
        result, why = build(args.source, args.out, args.minified)
        if why:
            print(why)
            return 1
        missing = [rel for rel, data in result["files"].items()
                   if not (args.out / rel).is_file()
                   or (args.out / rel).read_bytes() != data]
        if missing:
            print(f"{args.out.name}/ is not what the bundle builds to at "
                  f"{result['version']}:")
            for rel in sorted(missing):
                print(f"  {rel}")
            print("Run ci/publish_hub.py and commit what it writes.")
            return 1
        print(f"{args.out.name}/ matches the bundle at {result['version']}")
        return 0

    out = args.out
    rehearsal = None
    if args.dry_run:
        # Against a copy of what is already published, so the immutability
        # check has the real history to judge against.
        rehearsal = Path(tempfile.mkdtemp(prefix="hub-dry-run-"))
        out = rehearsal / "publish"
        if args.out.is_dir():
            shutil.copytree(args.out, out)
        else:
            out.mkdir(parents=True)
    try:
        result, why = build(args.source, out, args.minified)
        if why:
            print(why)
            return 1
        write(result["files"], out)
        where = "would publish" if args.dry_run else "published"
        print(f"{where} {result['version']}")
        print(f"  integrity {result['integrity']}")
        print(f"  {result['minified']:,} bytes minified, "
              f"from {result['source']:,}")
        return 0
    finally:
        if rehearsal:
            shutil.rmtree(rehearsal, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
