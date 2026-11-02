"""The LiDAR simulator's controls (tools/lidar_sim.py Control) and spots to cover (tools/lidar_director.py):

1. a marked spot sends the SPOT_BOTS nearest free bots there (their job is ("go", the spot)), they are listed to drop
   their old goal at once, and a bot reaching it marks it covered and frees them; a spot nobody reaches is given up;
   clearing the spots frees every bot
2. the control refuses an unknown map, a speed not offered and a spot before a map runs; a pick queues that map and
   ends the one running; stop empties the queue

usage: python -I test_lidar_spots.py      -> "lidar spots OK"
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import testdata  # noqa: E402  (data this PC has that the public release does not ship)


def main():
    testdata.need("maps/beavercreek/heightmap.npz", why="the map pack")
    import jumpphys as J
    import lidar_director as D
    import lidar_sim
    from brain.maps import get_map, terrain
    from lidar import Recorder
    fails = []
    T = J.prepare(terrain(get_map("beavercreek")))
    rec = Recorder("beavercreek", count_run=False)
    d = D.LidarDirector(T, rec, [])
    ctl = lidar_sim.Control(["beavercreek", "bloodgulch"])
    ctl.T, ctl.current = T, "beavercreek"
    spot = ctl.snap(float(d.x[len(d.x) // 2]), float(d.y[len(d.y) // 2]), float(d.z[len(d.z) // 2]))
    if spot is None:
        raise SystemExit("FAIL: a floor point did not snap to floor")
    sx, sy, sz = spot
    bots = {i: (sx + 4.0 * (i + 1), sy, sz) for i in range(6)}      # bot 0 nearest, bot 5 farthest
    d.add_spot(spot)
    d.plan(0.0, bots)
    sent = sorted(i for i, j in d.jobs.items() if j[0] == "spot")
    if sent != list(range(D.SPOT_BOTS)) or d.job(0, bots[0]) != ("go", d.spots[0]["pos"]):
        fails.append(f"1. sent {sent}, job {d.job(0, bots[0])} (want the {D.SPOT_BOTS} nearest, going to the spot)")
    if sorted(d.new_spot_bots) != sent:
        fails.append(f"1. bots to drop their goal {d.new_spot_bots}")
    bots[0] = (sx + 0.5, sy, sz)                                     # one gets there
    d.plan(D.PERIOD + 0.1, bots)
    if not d.spots[0]["done"] or any(j[0] == "spot" for j in d.jobs.values()):
        fails.append(f"1. reached spot not covered: {d.spot_view()}")
    d.add_spot((sx + 1.0, sy + 1.0, sz))
    far = {i: (sx + 200.0, sy, sz) for i in range(3)}
    d.plan(2 * D.PERIOD, far)
    d.plan(2 * D.PERIOD + D.SPOT_GIVE_UP + 1, far)
    if not d.spots[1]["given_up"]:
        fails.append(f"1. a spot nobody reached was not given up: {d.spot_view()}")
    d.add_spot((sx + 2.0, sy, sz))
    d.plan(400.0, far)
    d.clear_spots()
    if d.spots or any(j[0] == "spot" for j in d.jobs.values()):
        fails.append("1. clearing left spots or spot jobs")
    # 2. the control's checks
    if ctl.command({"action": "pick", "name": "nowhere"})[0] != 404:
        fails.append("2. an unknown map was accepted")
    if ctl.command({"action": "speed", "speed": 3})[0] != 400 or ctl.command({"action": "speed", "speed": 8})[0] != 200:
        fails.append("2. speeds: 3 not refused or 8 not taken")
    ctl.current, ctl.T = None, None
    if ctl.command({"action": "spot", "x": sx, "y": sy, "z": sz})[0] != 409:
        fails.append("2. a spot before a map runs was accepted")
    ctl.current = "beavercreek"
    ctl.command({"action": "pick", "name": "bloodgulch"})
    if ctl.queue != ["bloodgulch"] or not ctl.stop_now:
        fails.append(f"2. pick: queue {ctl.queue}, stop the running map {ctl.stop_now}")
    ctl.command({"action": "stop"})
    if ctl.queue:
        fails.append("2. stop left a queue")
    if fails:
        print("FAIL")
        for f in fails:
            print(f)
        raise SystemExit(1)
    print(f"lidar spots OK (the {D.SPOT_BOTS} nearest bots sent, covered when reached, given up after "
          f"{D.SPOT_GIVE_UP:.0f} s, cleared; control checks hold)")


if __name__ == "__main__":
    main()
