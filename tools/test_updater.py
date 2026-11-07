"""The update check (tools/updater.py) and the release's text (tools/release_notes.py): a release updated in place (same
version, newer build stamp) is an update; What's new lists everything since the player's copy (every newer version
whole, and of the player's version each update built after theirs); the release text carries the build stamp the
check reads; BUILD is docs/UPDATES.md's newest stamp.

usage: python -I test_updater.py      -> "updater OK"
"""
import json
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import release_notes  # noqa: E402
import updater  # noqa: E402

MD = open(os.path.join(updater.ROOT, "docs", "UPDATES.md"), encoding="utf-8").read()
STALE = updater.BUILD_MARK.sub("", MD)                                  # (an UPDATES.md from before the stamps)
NEWEST = max(updater.BUILD_MARK.findall(MD))                         # (s181's newest update)
NEXT = ("<details open>\n<summary><b>0.2.3 s182</b> (December 1, 2026): a test version</summary>\n\n"
        "### Fixed\n- **Test**: a fix.\n\n</details>\n\n")


def texts(items):
    return " ".join(i["title"] + " " + i["text"] for i in items)


def main():
    nw = updater.is_newer
    assert nw("0.2.2-s181", "20261106-1840", "v0.2.2-s181", "20261106-2300")       # updated in place: an update
    assert not nw("0.2.2-s181", "20261106-2300", "v0.2.2-s181", "20261106-2300")   # the same build
    assert not nw("0.2.2-s181", "20261106-2300", "v0.2.2-s181", "20261106-1840")   # (an older one)
    assert nw("0.2.2-s181", "", "v0.2.2-s181", "20261106-2300")                    # a copy from before stamps
    assert not nw("0.2.2-s181", "", "v0.2.2-s181", "")                             # a release with no stamp
    assert nw("0.2.2-s180", "20261106-2300", "v0.2.2-s181", "")                    # a newer version, stamp or not
    assert not nw("0.2.2-s182", "", "v0.2.2-s181", "20261106-2300")
    assert not nw("dev", "", "v0.2.2-s181", "20261106-2300")

    secs = updater.parse_updates(MD)
    s181 = next(s for s in secs if s["key"] == (0, 2, 2, 181))
    stamps = [b for b, _ in s181["batches"]]
    assert stamps[0] == "" and stamps[1] == NEWEST and stamps[-3:] == ["20261106-2300", "20261106-1840", "20261106-1440"], stamps
    assert s181["title"].startswith("(November 6, 2026)"), s181["title"]

    n = updater.news(MD, "0.2.2-s181", "20261106-1840")                 # one update behind: only the third
    assert len(n) == 1 and "Third update" in n[0]["text"] and "Second update" not in n[0]["text"], n
    assert "Call a bot into your vehicle" in n[0]["text"] and "since your copy" in n[0]["title"]
    assert updater.news(MD, "0.2.2-s181", NEWEST) == []                 # up to date: nothing
    t = texts(updater.news(MD, "0.2.2-s181", ""))                      # a copy from before stamps: all three
    assert all(k in t for k in ("Third update", "Second update", "First release")), t[:200]
    n = updater.news(MD, "0.2.2-s180", "")                              # one version behind: s181 whole, not s180
    assert len(n) == 1 and n[0]["title"].startswith("0.2.2 s181") and "First release" in n[0]["text"], n
    n = updater.news(MD, "0.2.2-s179", "")                              # two behind: s181 then s180
    assert [i["title"].split(" (")[0] for i in n] == ["0.2.2 s181", "0.2.2 s180"], [i["title"] for i in n]
    n = updater.news(NEXT + MD, "0.2.2-s181", "20261106-1840")          # a new version and an update of ours
    assert [i["title"].split(" (")[0].split(":")[0] for i in n] == ["0.2.3 s182", "0.2.2 s181"], n
    assert "Third update" in n[1]["text"] and "Second update" not in n[1]["text"]

    # check() and info(): the release's body gives its build, its tag's UPDATES.md gives What's new
    body = release_notes.notes(MD, "0.2.2-s181", NEWEST)
    assert f"<!-- build: {NEWEST} -->" in body and "Download **ProjectProvingGrounds-Setup-0.2.2-s181.exe**" in body
    assert body.count("<!-- build:") == len(stamps) - 1 and "/docs/KNOWN_BUGS.md" in body
    for bad in (("0.2.2-s181", "20261106-2359"), ("0.9.9-s999", "")):
        try:
            release_notes.notes(MD, *bad)
            raise AssertionError(f"no error for {bad}")
        except ValueError:
            pass
    rel = dict(tag_name="v0.2.2-s181", name="Project Proving Grounds 0.2.2 s181", html_url=updater.RELEASES + "/tag/v0.2.2-s181",
               body=body, assets=[dict(name="ProjectProvingGrounds-Setup-0.2.2-s181.exe", size=5,
                                       browser_download_url="https://example.invalid/setup.exe")])
    asked = []

    class Reply:
        def __init__(self, data):
            self.data = data

        def read(self, *a):
            return self.data

    def urlopen(req, timeout=0):
        asked.append(req.full_url)
        if req.full_url == updater.API:
            return Reply(json.dumps(rel).encode())
        if req.full_url == updater.NOTES.format(tag="v0.2.2-s181") and notes_ok:
            assert req.get_header("Accept") == "application/vnd.github.raw"
            return Reply((MD if notes_ok == "new" else STALE).encode())
        raise OSError("offline")

    tmp = tempfile.mkdtemp()
    updater.STATE = os.path.join(tmp, "update.json")
    updater.urllib.request.urlopen = urlopen
    updater.json.load = (lambda f, _load=json.load: json.loads(f.read()) if isinstance(f, Reply) else _load(f))
    updater.current, updater.build = (lambda: "0.2.2-s181"), (lambda: "20261106-1840")
    notes_ok = "new"
    i = updater.check(force=True)
    assert asked[-1] == updater.NOTES.format(tag="v0.2.2-s181") and "api.github.com" in asked[-1], asked
    assert i["available"] and i["same_version"] and i["latest_build"] == NEWEST and i["can_install"], i
    assert len(i["news"]) == 1 and "Third update" in i["news"][0]["text"], i["news"]
    updater.build = lambda: NEWEST
    i = updater.info()
    assert not i["available"] and i["news"] == [], i
    # its UPDATES.md not read, or an older copy of it (no stamp of this release): the release's text, of our version
    # only the updates built after ours
    for notes_ok in (False, "stale"):
        updater.build = lambda: "20261106-1440"
        i = updater.check(force=True)
        t = i["news"][0]["text"] if i["news"] else ""
        assert i["available"] and len(i["news"]) == 1 and "<!--" not in t and "Download" not in t, (notes_ok, i["news"])
        assert "Third update" in t and "Second update" in t and "First release" not in t, (notes_ok, t[:300])
    updater.current, updater.build = (lambda: "0.2.2-s180"), (lambda: "")
    i = updater.info()                                                  # (a version behind: the whole text)
    assert i["available"] and not i["same_version"] and "First release" in i["news"][0]["text"], i
    st = json.load(open(updater.STATE, encoding="utf-8"))
    assert time.time() - st["checked"] < 60 and st["latest"] == "v0.2.2-s181"

    stamps = updater.BUILD_MARK.findall(MD)                             # the repository's own BUILD: the newest stamp
    build = open(os.path.join(updater.ROOT, "BUILD"), encoding="utf-8").read().strip()
    assert build == max(stamps), (build, max(stamps))
    print("updater OK")


if __name__ == "__main__":
    main()
