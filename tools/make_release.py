"""Builds the public copy of this project: only the files that belong in the open-source release, into a folder of its
own, then scans that copy for private data. The working folder is never changed.

What goes where (rules below, by path):
  release      the source: brain/, native/ sources, the tools and tests, map knowledge made by hand or read from the
               maps' object lists (callouts, positions, features, objects, Invasion spawns), the decoded input tables,
               armor catalogs, vehicle data, the anonymized human reference play, the curated docs, our Ghidra scripts
  map pack     files made from the game's own geometry that each user could rebuild with Halo's official mod kits, too
               big for the repository: height maps, top-down pictures, glass masks, Forge piece shapes and tag names.
               Shipped as an optional download beside the release
  left out     everything else: logs and recordings, LiDAR scans and everything learned from play (each user maps and
               teaches their own), Forge layouts recorded here, raw game geometry and scenario dumps, decompiled game
               code, built binaries, third-party downloads, backups, the development log and session notes, local
               launchers, and the map tools built on a GPL library (replaced before the release)

The privacy scan fails the build on an e-mail address, a user's folder path or this PC's drive paths, and on each
personal term (a name, gamertag or Xbox ID, one per line) in .private_terms at the project root: a local file that is
never committed (.gitignore), so the terms are not in the code either. It also counts the comments still quoting
development messages (removed in the comment pass).

usage: python -I make_release.py [out_folder]      (default: a "release" folder beside this project's folder)
       python -I make_release.py --scan <folder>    only the privacy scan
"""
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
MARK = ".release-build"          # written into an output folder this script made (only those are ever emptied)

# (pattern, where): the first match wins; paths are relative, forward slashes; "*" stays within a folder, "**" crosses
RULES = (
    # left out
    ("logs/**", None), ("backups/**", None), ("downloads/**", None), ("reference/**", None),
    ("**/__pycache__/**", None), ("*.pyc", None), ("**/*.pyc", None),
    ("native/bin/**", None), ("native/**/*.obj", None), ("native/**/*.pdb", None), ("native/**/*.ilk", None),
    ("native/tests/*.pdb", None),
    ("ghidra/**/*.java", "release"), ("ghidra/**", None),
    ("tools/bsp2obj/**", None), ("tools/model2obj/**", None), ("tools/map_tools/**", None),
    ("tools/view_art/games/**", None), ("tools/view_art/maps/**", None),     # (MCC's own art: map_art.py builds it)
    ("tools/backup.py", None), ("tools/verify_checks.py", None), ("tools/test_verify_checks.py", None),("tools/identity_probe.py", None),
    ("docs/HANDOFF*.md", None), ("docs/oct31/**", None), ("docs/evidence/**", None), ("docs/ENGINEER_CHECKS.md", None),
    ("docs/RELEASE_PLAN.md", None), ("docs/RELEASE_CHECKLIST.md", None), ("docs/PLAN_*.md", None),
    ("docs/play_status.*", None), ("docs/VISION.md", None), ("docs/research/11-kev-vs-ollama.md", None),
    ("*.bat", None), ("*.lnk", None),
    ("maps/*/variants/**", None), ("maps/*/lidar*.json", None), ("maps/*/nav_learned.json", None),
    ("maps/*/los_learned.json", None), ("maps/*/rides.json", None), ("maps/*/moves_review.json", None),
    ("maps/*/wedges.json", None), ("maps/*/shots.json", None), ("maps/*/paint.json", None), ("maps/*/oob*.json", None),
    ("maps/*/stations.json", None), ("maps/*/variant.json", None), ("maps/*/*.obj", None), ("maps/*/*.xml", None),
    # map pack
    ("maps/*/heightmap.npz", "pack"), ("maps/*/topdown.png", "pack"), ("maps/*/glass.json", "pack"),
    ("maps/_shapes/**", "pack"),
    # release
    ("maps/*/callouts.json", "release"), ("maps/*/positions.json", "release"), ("maps/*/features.json", "release"),
    ("maps/*/objects.json", "release"), ("maps/*/inv_spawns.json", "release"),
    ("maps/_inputs/**", "release"), ("maps/_looks/**", "release"), ("maps/_vehicles/**", "release"),
    ("maps/_human/**", "release"), ("maps/**", None),
    ("brain/**", "release"), ("tools/**", "release"), ("native/**", "release"), ("docs/**", "release"),
    ("installer/**", "release"), ("VERSION", "release"), ("CONTRIBUTING.md", "release"), ("SECURITY.md", "release"),
    ("CODE_OF_CONDUCT.md", "release"), ("requirements.txt", "release"), ("requirements-dev.txt", "release"),
    ("README.md", "release"), ("LICENSE.md", "release"), ("NOTICE.md", "release"), (".gitignore", "release"),
)

# private data: any of these in a release file stops the build (with the personal terms of .private_terms)
PRIVATE = {
    "e-mail": r"[A-Za-z0-9._%+-]+@(?:gmail|outlook|hotmail|yahoo|icloud)\.com",
    "user folder": r"(?i)[A-Z]:[\\/]+Users[\\/]+(?!Public|Default|<|%|\{|\*)[A-Za-z0-9_.-]+",
    "this PC's drive": r"(?i)(?<![A-Za-z])A:[\\/]+(?:Steam|Claude)",
    "assistant notes": r"(?i)code" + "frame" + r"|\.claude[\\/]",   # (split: this file never matches itself)
}
# an Xbox user id (0x0009 and 12 hex digits, any suffix): only the made-up ones the tests use pass
XBOX_ID = r"(?i)(?<![0-9a-f.])(?:0x)?(0009[0-9a-f]{12})(?![0-9a-f])"     # (not digits after a decimal point)
MADE_UP_IDS = {"0009000012345678", "0009deadbeef0001"}
QUOTES = r"(?i)\bowner\b"        # development quotes still in comments (counted, removed in the comment pass)
TEXT = (".py", ".cpp", ".h", ".c", ".md", ".txt", ".json", ".bat", ".html", ".js", ".css", ".java", ".ini", ".cfg",
        ".toml", ".yml", ".yaml", ".gitignore")


# the public repository's .gitignore: everything each PC makes for itself stays out of git
PUBLIC_GITIGNORE = """# made on each PC: recordings, logs, backups
logs/
backups/
__pycache__/
*.pyc

# built: the mod, the injector and their settings, pictures and 3D bots (native/build.bat, tools/setup.py)
native/bin/
native/**/*.obj
native/**/*.pdb

# the map tools and the bundled Python of an install
tools/map_tools/
python/

# made from your copy of MCC by the first-time setup
tools/view_art/games/
tools/view_art/maps/
maps/_models/

# the map pack (a separate download: unzip it over the repository)
maps/*/heightmap.npz
maps/*/topdown.png
maps/*/glass.json
maps/_shapes/

# each PC's own LiDAR scans and what its bots learned
maps/*/lidar*.json
maps/*/nav_learned.json
maps/*/los_learned.json
maps/*/rides.json
maps/*/wedges.json
maps/*/shots.json
maps/*/paint.json
maps/*/oob*.json
maps/*/stations.json
maps/*/variants/
maps/*/source/
maps/*/roofless/
maps/*/roofless.json

# personal terms for the release privacy scan (tools/make_release.py)
.private_terms
"""


def match(path, pattern):
    """fnmatch with "**" crossing folders and "*" staying in one."""
    rx = "^" + re.escape(pattern).replace(r"\*\*/", "(?:.*/)?").replace(r"\*\*", ".*").replace(r"\*", "[^/]*") + "$"
    return re.match(rx, path) is not None


def where(path):
    """'release', 'pack' or None for a repository path."""
    for pattern, dest in RULES:
        if match(path, pattern):
            return dest
    return None


def load_terms(path=None):
    """The personal terms in .private_terms (one per line, # comments), matched case-insensitively."""
    try:
        lines = open(path or os.path.join(ROOT, ".private_terms"), encoding="utf-8").read().splitlines()
    except OSError:
        return []
    return [t.strip() for t in lines if t.strip() and not t.strip().startswith("#")]


def scan_text(text, terms=()):
    """{kind: count} of private data in one file's text (terms: personal terms), and the count of development quotes."""
    found = {k: len(re.findall(p, text)) for k, p in PRIVATE.items()}
    found["personal term"] = sum(len(re.findall(re.escape(t), text, re.I)) for t in terms)
    found["Xbox id"] = sum(1 for m in re.findall(XBOX_ID, text) if m.lower() not in MADE_UP_IDS)
    return {k: n for k, n in found.items() if n}, len(re.findall(QUOTES, text))


def scan(folder, terms=None):
    """Scans every text file under folder: (problems [(file, {kind: n})], quote count, files scanned)."""
    terms = load_terms() if terms is None else terms
    problems, quotes, n = [], 0, 0
    for dp, _, fs in os.walk(folder):
        for f in fs:
            if not f.endswith(TEXT) or f == MARK:
                continue
            p = os.path.join(dp, f)
            try:
                text = open(p, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            n += 1
            found, q = scan_text(text, terms)
            if "third_party" in p:               # (other projects' credits name their authors' public e-mails)
                found.pop("e-mail", None)
            quotes += q
            if found:
                problems.append((os.path.relpath(p, folder), found))
    return problems, quotes, n


def tracked():
    """The repository's tracked files (git ls-files), forward slashes."""
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [p for p in out.split("\n") if p]


def untracked_release_files():
    """New code not yet committed that the release would carry (brain, tools, native, installer): the release is made
    from the tracked files, so it would be missing (map data a run wrote is not code: left to the player's commits)."""
    out = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, capture_output=True,
                         text=True, check=True).stdout
    return [p for p in out.split("\n") if p.startswith(("brain/", "tools/", "native/", "installer/"))
            and where(p) == "release"]


def build(out):
    new = untracked_release_files()
    if new:
        raise SystemExit("commit these first (the release is made from committed files): " + ", ".join(new[:20]))
    pack = out + "-map-pack"
    for d in (out, pack):
        if os.path.exists(d):
            if not os.path.exists(os.path.join(d, MARK)):
                raise SystemExit(f"{d} exists and was not made by this script: not touching it")
            shutil.rmtree(d)
        os.makedirs(d)
        open(os.path.join(d, MARK), "w").write("made by tools/make_release.py; emptied on each build\n")
    counts = {"release": [0, 0], "pack": [0, 0], None: [0, 0]}
    for rel in tracked():
        dest = where(rel)
        src = os.path.join(ROOT, rel)
        size = os.path.getsize(src) if os.path.exists(src) else 0
        counts[dest][0] += 1
        counts[dest][1] += size
        if dest is None or not os.path.exists(src):
            continue
        dst = os.path.join(out if dest == "release" else pack, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.isdir(src):                   # a git submodule (native/third_party/minhook): its files, no .git
            shutil.copytree(src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".git", "*.obj", "*.pdb"))
        else:
            shutil.copy2(src, dst)
    with open(os.path.join(out, ".gitignore"), "w", encoding="utf-8", newline="\n") as f:
        f.write(PUBLIC_GITIGNORE)
    for k, label in (("release", "release"), ("pack", "map pack"), (None, "left out")):
        print(f"{label:9s} {counts[k][0]:6d} files {counts[k][1] / 1048576:8.1f} MB")
    return out, pack


def report(folder):
    problems, quotes, n = scan(folder)
    print(f"privacy scan: {n} text files, {len(problems)} with private data, {quotes} development quotes left")
    for f, found in problems[:40]:
        print(f"  {f}: " + ", ".join(f"{k} x{c}" for k, c in found.items()))
    return not problems


def main():
    args = sys.argv[1:]
    if args[:1] == ["--scan"]:
        ok = report(args[1])
    else:
        out = os.path.abspath(args[0]) if args else os.path.join(os.path.dirname(ROOT), "release")
        out, pack = build(out)
        print("release:", out)
        print("map pack:", pack)
        ok = report(out) and report(pack)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
