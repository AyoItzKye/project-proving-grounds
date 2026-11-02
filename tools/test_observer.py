"""Offline checks for the Observer (tools/observer.py): the last 5 match recordings are kept; with a
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
    """The last 10 matches are kept (tools/play.py match_trace; the player: 5: 10): a new match deletes the oldest beyond
    that, hand-named traces stay, and the game list names a match by its start and difficulty."""
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
        new = play.match_trace("reach_52_ivory_tower", logs=tmp)
        open(new, "w").close()
        left = sorted(os.listdir(tmp))
        if not os.path.exists(own):
            fails.append("a hand-named trace was deleted")
        if sorted(set(left) - {os.path.basename(own)}) != sorted(names[2:] + [os.path.basename(new)]):
            fails.append(f"after a 12th match the recordings are {left} (want the last 10)")
        got = observer.match_label(os.path.join(tmp, names[5]))
        if got != "Match Oct 25 12:00, Legendary":
            fails.append(f"game list label {got!r}")
        # MCC's post-game report goes beside the last match's trace when the next match starts (it overwrites its one
        # file every match; botcore stops play.py at a match's end): only a report written just after that trace
        report, play.CARNAGE = play.CARNAGE, os.path.join(tmp, "report.xml")
        try:
            open(play.CARNAGE, "w").write("<report/>")
            last = os.path.join(tmp, names[-1])
            os.utime(play.CARNAGE, (1e9 + 9000, 1e9 + 9000))          # hours after the last trace: not its report
            if play.keep_carnage([os.path.join(tmp, n) for n in names[2:]]):
                fails.append("kept a post-game report written long after the last match")
            os.utime(play.CARNAGE, (1e9 + 10 + 60, 1e9 + 10 + 60))    # a minute after the last trace's end
            got = play.keep_carnage([os.path.join(tmp, n) for n in names[2:]])
            if got != last[:-len(".jsonl")] + ".carnage.xml" or open(got).read() != "<report/>":
                fails.append(f"the post-game report was not kept beside the last trace ({got})")
        finally:
            play.CARNAGE = report


def main():
    # a server of this copy: the one on the port given, else its own (the Observer on 8799 may be another install's,
    # with other recordings)
    u = f"http://127.0.0.1:{sys.argv[1] if len(sys.argv) > 1 else 8811}"
    fails = []
    recordings(fails)
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
