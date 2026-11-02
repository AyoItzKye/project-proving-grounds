"""Builds the human play dataset for a release: human-play-data-<version>.zip, an optional download beside the
installer (docs/HUMAN_DATA.md says what is in it and how to read it).

In the zip:
  collect/<file>.jsonl     every Data collector recording on this PC (logs/collect_*.jsonl): a person playing,
                           every tick, with the keys they pressed (the format: docs/HUMAN_DATA.md)
  matches/<match>.zip      every recorded match with bots still on this PC, as the Observer's export makes it
                           (tools/match_export.py: names replaced by Player 1, 2 ..., Xbox ids removed)
  human/                   the human reference numbers the bots are tuned against (maps/_human)
  README.md                docs/HUMAN_DATA.md
Every text that goes in has the Windows user folder replaced (match_export.scrub) and is scanned for private data
(tools/make_release.py: e-mail addresses, user folders, this PC's drives, the terms in .private_terms); one hit stops
the build.

usage: python -I human_data.py [out.zip]      (default: installer_build/human-play-data-<version>.zip)
"""
import glob
import os
import shutil
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import make_release  # noqa: E402
import match_export  # noqa: E402

LOGS = os.path.join(ROOT, "logs")


def clean(text, terms, where):
    """The text with the user folder replaced, after a privacy scan (stops on a hit)."""
    text = match_export.scrub(text, {})
    found, _ = make_release.scan_text(text, terms)
    if found:
        raise SystemExit(f"private data in {where}: {found}: not building")
    return text


def build(out):
    terms = make_release.load_terms()
    tmp = out + ".part"
    n_collect = n_match = 0
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(glob.glob(os.path.join(LOGS, "collect_*.jsonl"))):
            z.writestr("collect/" + os.path.basename(p), clean(open(p, encoding="utf-8", errors="replace").read(), terms, p))
            n_collect += 1
        work = tempfile.mkdtemp()
        try:
            for p in sorted(glob.glob(os.path.join(LOGS, "trace_*_????????-??????.jsonl"))):
                zp = match_export.export(p, os.path.join(work, os.path.basename(p)[:-6] + ".zip"))
                with zipfile.ZipFile(zp) as m:          # (the export already scrubbed it: scanned again here)
                    for name in m.namelist():
                        clean(m.read(name).decode("utf-8", "replace"), terms, f"{zp}:{name}")
                z.write(zp, "matches/" + os.path.basename(zp))
                n_match += 1
        finally:
            shutil.rmtree(work, ignore_errors=True)
        for p in glob.glob(os.path.join(ROOT, "maps", "_human", "*.json")):
            z.write(p, "human/" + os.path.basename(p))
        z.writestr("README.md", open(os.path.join(ROOT, "docs", "HUMAN_DATA.md"), encoding="utf-8").read())
    os.replace(tmp, out)
    print(f"{out}: {n_collect} Data collector recordings, {n_match} matches, {os.path.getsize(out) / 1048576:.0f} MB")
    return out


if __name__ == "__main__":
    ver = open(os.path.join(ROOT, "VERSION"), encoding="utf-8").read().strip()
    build(os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else
          os.path.join(os.path.dirname(ROOT), "installer_build", f"human-play-data-{ver}.zip"))
