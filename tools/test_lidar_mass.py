"""The LiDAR simulator's "Every map" (tools/lidar_sim.py Control, action "all"):

1. with no game, every map with level data in turn, each Forge layout (maps/<map>/variants/<id>) right after its map
2. with a game ("reach"), only that game's maps, layouts included
3. an unknown game is refused (400) and leaves the queue as it was
4. it ends with its window (closed), never while its window is open and the page is quiet (a confirm dialog)
5. an empty Forge canvas (no floor) is a "nothing to scan" row, not a failure
6. its progress is kept (user/lidar_all.json): a run stopped after two maps goes on with the rest next time, a skipped
   map counts as done, "fresh" starts over, a finished run is forgotten; a single map pick is not part of it

usage: python -I test_lidar_mass.py      -> "lidar mass OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import jumpphys as J  # noqa: E402
import lidar  # noqa: E402
import lidar_sim  # noqa: E402


def main():
    import tempfile
    tmp = tempfile.mkdtemp()
    Control = lidar_sim.Control

    class TmpControl(Control):          # (never the user's own saved run: user/lidar_all.json)
        def __init__(s, names):
            Control.__init__(s, names)
            s.resume_path = os.path.join(tmp, "lidar_all.json")
    lidar_sim.Control = TmpControl
    fails = []
    names = lidar.map_list_names()
    layouts = [m for m in names if "/variants/" in m]
    ctl = lidar_sim.Control(names)
    code, _ = ctl.command({"action": "all"})
    if code != 200 or ctl.queue != names:
        fails.append(f"1. every map: {code}, {len(ctl.queue)} queued of {len(names)}")
    if layouts and not set(layouts) <= set(ctl.queue):
        fails.append("1. the Forge layouts are left out of every map")
    for m in layouts:
        base = m.partition("/")[0]
        if base in ctl.queue and m in ctl.queue and ctl.queue.index(m) < ctl.queue.index(base):
            fails.append(f"1. {m} runs before its map")
    ctl = lidar_sim.Control(names)
    code, _ = ctl.command({"action": "all", "game": "reach"})
    want = [m for m in names if J.game_of(m.partition("/")[0]) == "reach"]
    if code != 200 or ctl.queue != want or not any("/variants/" in m for m in ctl.queue):
        fails.append(f"2. Reach: {code}, {len(ctl.queue)} queued, want {len(want)} with its layouts")
    before = list(ctl.queue)
    code, ans = ctl.command({"action": "all", "game": "halo5"})
    if code != 400 or ctl.queue != before:
        fails.append(f"3. an unknown game: {code} {ans}, queue changed {ctl.queue != before}")
    # 4. the simulator's end with its view (view_gone): its own window open, it waits however long the page is quiet
    # (the "Simulate every ... map?" question blocks the page's polls: left open 8 min on a fresh install, the simulator
    # had stopped at 90 s and the OK found nothing); a closed window (last_seen 0) ends it; a browser tab, 90 s unpolled
    win, t0 = object(), 1000.0
    if lidar_sim.view_gone(win, t0, t0 + 600.0):
        fails.append("4. its window open, 10 min with the page quiet: the simulator stopped")
    if not lidar_sim.view_gone(win, 0.0, t0):
        fails.append("4. its window closed: the simulator kept on")
    if lidar_sim.view_gone(None, t0, t0 + 60.0) or not lidar_sim.view_gone(None, t0, t0 + 91.0):
        fails.append("4. a browser tab: not ended at 90 s unpolled")
    # 5. an empty Forge canvas (H2A's skyboxes: no floor, every floor its layouts' pieces) in a game's run: a row that
    # says so, no FAILED ZeroDivisionError (a fresh install's "Every Halo 2 Anniversary map", three of them)
    import io
    from types import SimpleNamespace
    log = io.StringIO()
    o = SimpleNamespace(walkers=4, aircraft=0, minutes=0.1, speed=0.0, max_real=5.0, window=False, no_director=False,
                        hold=0.0, open=False)
    got = lidar_sim.run_map("h2a_ca_forge_skybox01", o, lidar_sim.Switch(), 1, 1, log, None)
    if got is not None or "no floor: an empty Forge canvas" not in log.getvalue():
        fails.append(f"5. an empty Forge canvas: {got!r}, log {log.getvalue()!r}")
    # 6. resume and skip
    ctl = lidar_sim.Control(names)
    ctl.command({"action": "all", "game": "ce"})
    ce = list(ctl.queue)
    for m in ce[:2]:                    # two maps finish
        ctl.current = ctl.next_map()
        ctl.finished(m, 10, 0, 60.0, False)
        ctl.map_done(m, False)
    ctl.current = ctl.next_map()        # the third: skipped
    code, _ = ctl.command({"action": "skip"})
    ctl.finished(ce[2], 5, 0, 30.0, True)
    ctl.map_done(ce[2], True)
    ctl.current = ctl.next_map()        # the fourth: Stop and save (not done)
    ctl.command({"action": "stop"})
    ctl.finished(ce[3], 5, 0, 30.0, True)
    ctl.map_done(ce[3], True)
    ctl.current = None
    view = ctl.resume_view().get("ce")
    if code != 200 or view != dict(done=3, total=len(ce)):
        fails.append(f"6. after 2 done, 1 skipped, 1 stopped: skip {code}, resume {view} (want 3 of {len(ce)})")
    ctl2 = lidar_sim.Control(names)
    code, ans = ctl2.command({"action": "all", "game": "ce"})
    if ctl2.queue != ce[3:] or ans.get("resumed") != 3:
        fails.append(f"6. Every Halo CE map again: {len(ctl2.queue)} queued, first {ctl2.queue[:1]} (want {ce[3:4]}), {ans}")
    ctl2.command({"action": "pick", "name": ce[5]})
    ctl2.current = ctl2.next_map()
    ctl2.finished(ce[5], 5, 0, 30.0, False)
    ctl2.map_done(ce[5], False)
    if ctl2.resume_view().get("ce") != dict(done=3, total=len(ce)):
        fails.append("6. a single map pick counted into the Every map run")
    ctl2.command({"action": "all", "game": "ce", "fresh": True})
    if ctl2.queue != ce or "ce" in ctl2.resume_view():
        fails.append(f"6. fresh: {len(ctl2.queue)} queued (want all {len(ce)}), saved {ctl2.resume_view()}")
    for m in ce:                        # the whole run done: forgotten
        ctl2.current = ctl2.next_map()
        ctl2.finished(m, 1, 0, 1.0, False)
        ctl2.map_done(m, False)
    if "ce" in ctl2.resume_state():
        fails.append("6. a finished run is still kept")
    code, _ = ctl2.command({"action": "skip"})
    if code != 409:
        fails.append(f"6. skip with nothing running: {code} (want 409)")
    if fails:
        sys.exit("FAIL\n" + "\n".join(fails))
    print(f"lidar mass OK ({len(names)} maps and layouts, {len(want)} Reach with its {sum('/variants/' in m for m in want)} "
          "layouts)")


if __name__ == "__main__":
    main()
