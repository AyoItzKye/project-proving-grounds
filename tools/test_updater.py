"""The update check (tools/updater.py) and the release's text (tools/release_notes.py): a release updated in place (same
version, newer build stamp) is an update; What's new lists everything since the player's copy (every newer version
whole, and of the player's version each item built after theirs; one + Added and one - Fixed list per version); the
release text carries the build stamp the check reads; BUILD is docs/UPDATES.md's newest stamp.

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
NEXT = ("<details open>\n<summary><b>0.2.3</b> (December 1, 2026): a test version</summary>\n\n"
        "### - Fixed\n- <!-- build: 20261201-1200 --> **Test**: a fix.\n\n</details>\n\n")


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

    # one section per version, each one "+ Added" and one "- Fixed" list (no dated updates), every item stamped with
    # the build it came in ("" before stamps)
    secs = updater.parse_updates(MD)
    v022 = next(s for s in secs if s["key"][:3] == (0, 2, 2))
    assert all({i["head"] for i in s["items"]} <= {"+ Added", "- Fixed"} for s in secs), [s["name"] for s in secs]
    assert "#### " not in MD and "update (November" not in MD and "<!--" not in texts([dict(title="", text=i["text"])
                                                                                       for i in v022["items"]])
    stamps = [i["build"] for i in v022["items"] if i["build"]]
    assert max(stamps) == NEWEST and "20261106-1440" in stamps and any(not i["build"] for i in v022["items"]), stamps
    assert v022["title"].startswith("(November 6 to 11, 2026)"), v022["title"]

    n = updater.news(MD, "0.2.2-s181", "20261106-1840")                 # updates behind: the items since, by list
    t = texts(n)
    assert len(n) == 1 and "since your copy" in n[0]["title"] and "Call a bot into your vehicle" in t, n
    assert "Gravity lifts" not in t and "Jetpacks" not in t and "+ Added" in t and "- Fixed" in t, t[:300]
    assert updater.news(MD, "0.2.2-s181", NEWEST) == []                 # up to date: nothing
    t = texts(updater.news(MD, "0.2.2-s181", ""))                      # a copy from before stamps: all of 0.2.2
    assert all(k in t for k in ("Halo 2 vehicles", "Gravity lifts", "Jetpacks")), t[:200]
    t = texts(updater.news(MD, "0.2.2-s180", ""))                      # an older 0.2.2 build: all of 0.2.2
    assert "Jetpacks" in t and "Halo 2 vehicles" in t, t[:200]
    n = updater.news(MD, "0.2.1", "")                                   # a version behind: 0.2.2 whole
    assert len(n) == 1 and n[0]["title"].startswith("0.2.2 (") and "Jetpacks" in n[0]["text"], n
    n = updater.news(MD, "0.2.0", "")                                   # two behind: 0.2.2 then 0.2.1
    assert [i["title"].split(" (")[0] for i in n] == ["0.2.2", "0.2.1"], [i["title"] for i in n]
    n = updater.news(NEXT + MD, "0.2.2-s181", "20261106-1840")          # a new version and an update of ours
    assert [i["title"].split(" (")[0].split(":")[0] for i in n] == ["0.2.3", "0.2.2"], n
    assert "Call a bot" in n[1]["text"] and "Gravity lifts" not in n[1]["text"]

    # check() and info(): the release's body gives its build, its tag's UPDATES.md gives What's new
    body = release_notes.notes(MD, "0.2.2-s181", NEWEST)
    assert f"<!-- build: {NEWEST} -->" in body and "Download **ProjectProvingGrounds-Setup-0.2.2-s181.exe**" in body
    assert body.count("<!-- build:") == len(stamps) and "/docs/KNOWN_BUGS.md" in body and "### + Added" in body
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
    assert len(i["news"]) == 1 and "Call a bot" in i["news"][0]["text"], i["news"]
    assert "Gravity lifts" not in i["news"][0]["text"], i["news"]
    updater.build = lambda: NEWEST
    i = updater.info()
    assert not i["available"] and i["news"] == [], i
    # its UPDATES.md not read, or an older copy of it (no stamp of this release; a launcher from before one section per
    # version reads the release's text this way too): of our version only the items built after ours
    for notes_ok in (False, "stale"):
        updater.build = lambda: "20261106-1440"
        i = updater.check(force=True)
        t = i["news"][0]["text"] if i["news"] else ""
        assert i["available"] and len(i["news"]) == 1 and "<!--" not in t and "Download" not in t, (notes_ok, i["news"])
        assert "Call a bot" in t and "Gravity lifts" in t and "Jetpacks" not in t, (notes_ok, t[:300])
    updater.current, updater.build = (lambda: "0.2.2-s180"), (lambda: "")
    i = updater.info()                                                  # (an older build: the whole text)
    assert i["available"] and not i["same_version"] and "Jetpacks" in i["news"][0]["text"], i
    st = json.load(open(updater.STATE, encoding="utf-8"))
    assert time.time() - st["checked"] < 60 and st["latest"] == "v0.2.2-s181"

    stamps = updater.BUILD_MARK.findall(MD)                             # the repository's own BUILD: the newest stamp
    build = open(os.path.join(updater.ROOT, "BUILD"), encoding="utf-8").read().strip()
    assert build == max(stamps), (build, max(stamps))

    # automatic updates (tools/launcher.py try_auto_install): on by default; a newer version found goes in, unless MCC
    # runs (the next look tries again); off: told only (the player saw the notice and never the update, Nov 11)
    import launcher
    os.remove(updater.STATE)
    updater.save({})
    assert updater.info()["auto"], "automatic updates are on by default"
    started = []
    real = (updater.install, launcher.conflicts.mcc_running, launcher.paths.wine)
    updater.install = lambda on_start=None: started.append(1) or True
    launcher.paths.wine = lambda: False
    try:
        got = dict(auto=True, available=True, can_install=True)
        launcher.conflicts.mcc_running = lambda: True
        assert not launcher.try_auto_install(None, got) and not started, "installed while MCC runs"
        launcher.conflicts.mcc_running = lambda: False
        assert launcher.try_auto_install(None, got) and started, "an update found was not installed"
        started.clear()
        assert not launcher.try_auto_install(None, dict(got, auto=False)) and not started, "installed with auto off"
    finally:
        updater.install, launcher.conflicts.mcc_running, launcher.paths.wine = real
    print("updater OK")


if __name__ == "__main__":
    main()
