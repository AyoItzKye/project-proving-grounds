"""Offline checks for the Observer (tools/observer.py): the newest 5 unsaved match recordings are kept; with a
server running (its own on 8811, or the --port given) the endpoints answer, chunks end on whole lines, files that are
not traces are refused, and the text mode describes a bot from a trace with the observer lines (a short
simulator game).

usage: python -I test_observer.py [port]      -> "observer OK"   (uses a server on port, else its own on 8811)
"""
import glob
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import testdata  # noqa: E402  (data this PC has that the public release does not ship)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")


def get(u):
    return urllib.request.urlopen(u, timeout=60)


def recordings(fails):
    """The newest 5 unsaved matches are kept (tools/play.py match_trace, tools/recording.py; Nov 3: record
    5 games by default, the newest overwriting the oldest): a new match deletes the oldest unsaved beyond
    that, a kept one and hand-named traces stay, and the game list names a match by its start and difficulty."""
    import tempfile
    sys.path.insert(0, HERE)
    import observer
    import play
    with tempfile.TemporaryDirectory() as tmp:
        own = os.path.join(tmp, "trace_h3_construct.jsonl")        # named by hand / before: kept
        open(own, "w").close()
        names = [f"trace_reach_52_ivory_tower_202610{20 + k}-120000.jsonl" for k in range(11)]
        for k, n in enumerate(names):
            with open(os.path.join(tmp, n), "w") as f:
                f.write(json.dumps(dict(t=0.0, meta=dict(map="reach_52_ivory_tower", game="reach",
                                                         bot=dict(id=1, tier="top" if k == 5 else "novice")))) + "\n")
            os.utime(os.path.join(tmp, n), (1e9 + k, 1e9 + k))     # recorded in this order
        import recording
        recording.keep(names[0][-len("20261020-120000.jsonl"):-len(".jsonl")], logs=tmp)   # kept in the Observer
        new = play.match_trace("reach_52_ivory_tower", logs=tmp, games=5)
        open(new, "w").close()
        left = sorted(os.listdir(tmp))
        if not os.path.exists(own):
            fails.append("a hand-named trace was deleted")
        if sorted(set(left) - {os.path.basename(own), "saved_games.json"}) != sorted([names[0]] + names[-4:] +
                                                                                     [os.path.basename(new)]):
            fails.append(f"after a 12th match the recordings are {left} (want the kept one and the last 5)")
        got = observer.match_label(_one(tmp, names[5]))
        if got != "Match Oct 25 12:00, Legendary":
            fails.append(f"game list label {got!r}")
        # MCC's post-game report goes beside the last match's trace when the next match starts (it overwrites its one
        # file every match; botcore stops play.py at a match's end): only a report written just after that trace
        report, play.CARNAGE = play.CARNAGE, os.path.join(tmp, "report.xml")
        try:
            open(play.CARNAGE, "w").write("<report/>")
            last = os.path.join(tmp, names[-1])
            os.utime(play.CARNAGE, (1e9 + 9000, 1e9 + 9000))          # hours after the last trace: not its report
            if play.keep_carnage([os.path.join(tmp, n) for n in names[-4:]]):
                fails.append("kept a post-game report written long after the last match")
            os.utime(play.CARNAGE, (1e9 + 10 + 60, 1e9 + 10 + 60))    # a minute after the last trace's end
            got = play.keep_carnage([os.path.join(tmp, n) for n in names[-4:]])
            if got != last[:-len(".jsonl")] + ".carnage.xml" or open(got).read() != "<report/>":
                fails.append(f"the post-game report was not kept beside the last trace ({got})")
        finally:
            play.CARNAGE = report


def other_copies(fails):
    """Games another copy of the mod recorded are listed (Nov 4: pressing refresh in the Observer listed no
    games: the install's Observer read the install's logs, no games, while the brain ran from the working
    repo's botcore.dll and recorded into the repo's logs). Copies list themselves per user (tools/recording.py
    COPIES); the other copy's games are listed with their folder, readable, keepable in their own logs, and an empty
    list has the page's empty state."""
    import tempfile
    sys.path.insert(0, HERE)
    import observer
    import recording
    was = observer.LOGS, getattr(recording, "COPIES", None)
    with tempfile.TemporaryDirectory() as tmp:
        mine, repo = os.path.join(tmp, "install", "logs"), os.path.join(tmp, "repo")
        os.makedirs(mine)
        os.makedirs(os.path.join(repo, "logs"))
        game = os.path.join(repo, "logs", "trace_h2_coagulation_20261103-221113.jsonl")
        with open(game, "w") as f:
            f.write(json.dumps(dict(t=0.0, meta=dict(map="h2_coagulation", bot=dict(id=1, tier="top")))) + "\n")
        copies = os.path.join(tmp, "per_user", "copies.json")
        os.makedirs(os.path.dirname(copies))
        json.dump([os.path.join(tmp, "install"), repo], open(copies, "w"))
        observer.LOGS, recording.COPIES = mine, copies
        try:
            got = observer.trace_files()
            if [d.get("copy") for d in got] != [repo]:
                fails.append(f"another copy's games are not listed: {got} (want its one game, copy {repo})")
            elif observer.safe_trace(got[0]["file"]) != got[0]["file"] or not os.path.samefile(got[0]["file"], game):
                fails.append(f"another copy's game {got[0]['file']} cannot be read")
            elif got[0]["kept"] is not False or got[0]["label"] != "Match Nov 03 22:11, Legendary":
                fails.append(f"another copy's game entry {got[0]}")
            if observer.safe_trace(os.path.join(repo, "logs", "..", "..", "x.jsonl")) is not None:
                fails.append("served a path outside the game list")
        finally:
            observer.LOGS, recording.COPIES = was
    page = open(os.path.join(HERE, "observer.html"), encoding="utf-8").read()
    if 'id="nogames"' not in page or "showNoGames()" not in page:
        fails.append("the page has no empty state for an empty game list")


def _one(tmp, name):
    """A Legendary match's trace (back after it was rotated out above), for the game list's label."""
    path = os.path.join(tmp, name)
    with open(path, "w") as f:
        f.write(json.dumps(dict(t=0.0, meta=dict(map="reach_52_ivory_tower", game="reach", bot=dict(id=1, tier="top"))))
                + "\n")
    return path


def main():
    # a server of this copy: the one on the port given, else its own (the Observer on 8799 may be another install's,
    # with other recordings)
    u = f"http://127.0.0.1:{sys.argv[1] if len(sys.argv) > 1 else 8811}"
    fails = []
    recordings(fails)
    other_copies(fails)
    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    testdata.need(*[] if glob.glob(os.path.join(ROOT, "logs", "trace_*.jsonl")) else ["logs/trace_*.jsonl"],
                  why="a recorded match: play one with the data collector on")
    server = None
    try:
        get(u + "/traces")
    except (urllib.error.URLError, OSError):     # none running: start one of our own on a spare port (the suite
        import time                              # runner, tools/run_tests.py, starts nothing), stopped at the end
        port, u = 8811, "http://127.0.0.1:8811"
        server = subprocess.Popen([sys.executable, "-I", os.path.join(HERE, "observer.py"), "serve", "--port", str(port)],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(60):
            try:
                get(u + "/traces")
                break
            except (urllib.error.URLError, OSError):
                time.sleep(0.5)
    try:
        run(u, fails)
    finally:
        if server is not None:
            server.terminate()


def run(u, fails):
    traces = json.loads(get(u + "/traces").read())
    if not traces:
        sys.exit("FAIL: no traces listed")
    f = traces[0]["file"]
    r = get(u + "/trace?file=" + urllib.parse.quote(f) + "&offset=0&max=5000")
    body = r.read()
    if not body.endswith(b"\n") or int(r.headers["X-Next-Offset"]) != len(body):
        fails.append("a trace chunk did not end on a whole line")
    for bad in ("../../brain/bot.py", "C:/Windows/win.ini", "..\\observer_cache\\x", "evidence/../../tools/observer.py"):
        try:
            get(u + "/trace?file=" + urllib.parse.quote(bad))
            fails.append(f"served a file that is not a trace: {bad}")
        except urllib.error.HTTPError:
            pass
    rec = json.loads(get(u + "/settings").read())        # the Recording settings (tools/recording.py)
    if not (2 <= rec.get("games", 0) <= 50 and 1 <= rec.get("minutes", 0) <= 600) or "kept" not in traces[0] \
            or not {"logs", "on", "copies"} <= set(rec):      # (the page's empty list says where it looked)
        fails.append(f"recording settings {rec}, game list entry {sorted(traces[0])}")
    for path, body in (("/keep", {"file": "../../brain/bot.py", "keep": True}), ("/settings", {"games": 3})):
        try:                                             # (only the Observer's own page may change these)
            urllib.request.urlopen(urllib.request.Request(u + path, json.dumps(body).encode(), method="POST"), timeout=30)
            fails.append(f"{path} changed without the page's header")
        except urllib.error.HTTPError:
            pass
    try:
        req = urllib.request.Request(u + "/keep", json.dumps({"file": "../../brain/bot.py", "keep": True}).encode(),
                                     headers={"X-Observer": "1"}, method="POST")
        urllib.request.urlopen(req, timeout=30)
        fails.append("kept a file that is not a recorded match")
    except urllib.error.HTTPError:
        pass
    try:
        get(u + "/base?map=" + urllib.parse.quote("../../tools"))
        fails.append("served a map outside maps/")
    except urllib.error.HTTPError:
        pass
    b = json.loads(get(u + "/base?map=h2a_ca_lockout").read())
    if not (b["w"] > 0 and b["h"] > 0 and b["zones"]):
        fails.append("no map picture data for Lockdown")
    if get(u + b["img"]).headers["Content-Type"] != "image/png":
        fails.append("the map picture is not a PNG")
    # text mode on a simulator game with the observer lines
    demo = os.path.join(ROOT, "logs", "_observer_test.jsonl")
    subprocess.run([sys.executable, "-m", "brain.sim", "--trace", demo, "--map", "h2a_ca_lockout", "--seconds", "20",
                    "--limit", "50"], cwd=ROOT, capture_output=True, timeout=600)
    out = subprocess.run([sys.executable, "-I", os.path.join(HERE, "observer.py"), "at", demo, "15"],
                         capture_output=True, text=True, timeout=120).stdout
    for want in ("weighed:", "decided at", "facing", "goal", "eyes:"):
        if want not in out:
            fails.append(f"text mode 'at' lacks '{want}'")
    # every player's attention, stillness and squad are recorded: the world rows carry pitch, seconds
    # still, teammates formed up and who is in sights; bot lines what each looks at
    rows = [json.loads(x) for x in open(demo, encoding="utf-8")]
    world = [r for d in rows if "world" in d for r in d["world"]]
    if not world or any(len(r) < 15 for r in world):
        fails.append("world rows without pitch / still / formed up / in sights")
    kinds = {d["att"][0] for d in rows if "att" in d}
    if not {"aim", "watch"} <= kinds:
        fails.append(f"bot lines record attention kinds {sorted(kinds)} (want aim and watch at least)")
    os.remove(demo)
    # observer.py spawns: a respawn is a player alive again after being dead (a short Spire Invasion stand-in: you on
    # team 0 back at your phase-1 flag, a bot of team 1 back elsewhere), each with its nearest Invasion respawn flag
    fake = os.path.join(ROOT, "logs", "trace_reach_35_island_20991231-000000.jsonl")
    row = lambda t, a0, a1: json.dumps({"t": t, "invasion": [1, 0], "world": [
        [0, 0, a0, -113.4, -328.0, -62.5, 1, 1, 0, 0, 0, 0, 0, 0, 0], [5, 1, a1, -160.0, -370.0, -55.0, 1, 1, 1, 0, 0, 0, 0, 0, 0]]})
    with open(fake, "w", encoding="utf-8") as fh:
        fh.write("\n".join([json.dumps({"t": 0, "meta": {"map": "reach_35_island"}}), row(1, 1, 1), row(2, 0, 0), row(3, 1, 1)]) + "\n")
    r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "observer.py"), "spawns", fake], capture_output=True, text=True,
                       timeout=60)
    os.remove(fake)
    lines = r.stdout.splitlines()
    mine = [ln for ln in lines if "(you)" in ln]
    if (len(mine) != 1 or "inv_res_p1 team 0 *" not in mine[0] or " River " not in mine[0]
            or not any(ln.split()[1:2] == ["#5"] for ln in lines) or "2 respawns; yours: 1" not in r.stdout):
        fails.append(f"observer.py spawns: {r.stdout[-300:]}{r.stderr[-300:]} (want your respawn at your phase-1 flag, named "
                     f"River, the bot's, 2 respawns)")
    if fails:
        sys.exit("FAIL: " + "; ".join(fails))
    print("observer OK")


if __name__ == "__main__":
    main()
