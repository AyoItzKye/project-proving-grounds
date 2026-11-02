"""The LiDAR director.

Each mapping bot (tools/lidar.py Roomba) already walks to its own nearest unpainted floor. The director looks at the
whole map instead, every PERIOD seconds:
  - the map of the map: every walkable floor cell of the level data (Terrain.lwalk), sampled every STEP cells, split
    into reachable (by walking, teleporters and the jumps people and bots landed: graph_h, from the spawns) and not;
  - the boundary: the box around all walkable floor (where bots are ever sent), and how much of each part is painted;
  - regions: the unpainted reachable floor in connected pieces (per floor level), each with its size and a spot in
    it; islands: unpainted floor no walk reaches (roofs, ledges): a jump or a climb is the only way;
  - jobs: each bot keeps its region until it is painted, else takes the best free one (big and near, spread over the
    team: never two bots on one region while another region has nobody); the bot nearest an island within reach
    gets a jump job: walk to the take-off side, then call the jump (Roomba.pocket) toward it.
Roomba.pick asks job(index, pos): ("go", (x, y, z)), ("jump", (x, y, z)) or None (its own frontier).
"""
import math
import time

import numpy as np

STEP = 2                 # sample every 2nd nav cell each way (0.5 u apart): regions are coarse anyway
PERIOD = 6.0             # seconds between plans
MIN_CELLS = 6            # smaller pieces are paint noise, not a region
ISLAND_REACH = 30.0      # a bot this close (flat) to an island takes its jump job
JUMP_NEAR = 5.0          # at the take-off side: call the jump
REGION_BONUS = 25.0      # path units a bot's own region is worth over nearer unpainted floor elsewhere
JUMP_JOB_S = 40.0        # a jump job not reached by then is dropped
ISLANDS = True           # give out island jump jobs (off: A/B runs)
ISLAND_AFTER = 0.7       # ... once this share of the reachable floor is painted
ISLAND_BOTS = 2          # ... to this many bots at a time
SPOT_BOTS = 3            # bots sent to each spot a person marked to cover (the simulator's view)
SPOT_DONE_R = 2.5        # a bot this close (flat, within 2 u up or down) has covered the spot
SPOT_GIVE_UP = 120.0     # seconds: a spot no bot reached by then has no way there


class LidarDirector:
    def __init__(s, T, rec, spawns=()):
        from scipy.ndimage import label  # noqa: F401  (checked here: the director needs SciPy's labelling)
        from brain.terrain import NAV_CELL
        s.T, s.rec, s.spawns = T, rec, list(spawns)
        s.cell = NAV_CELL * STEP
        walk = T.lwalk[:, ::STEP, ::STEP]
        s.l, s.j, s.i = np.nonzero(walk)
        s.shape = walk.shape
        jj, ii = s.j * STEP, s.i * STEP
        s.x = T.x0 + (ii + 0.5) * NAV_CELL
        s.y = T.y0 + (jj + 0.5) * NAV_CELL
        s.z = T.lz[s.l, jj, ii]
        s.bounds = (float(s.x.min()), float(s.y.min()), float(s.x.max()), float(s.y.max())) if len(s.x) else None
        s.next_t, s.regions, s.islands, s.jobs = 0.0, [], [], {}
        s.painted_share, s.reach_share = 0.0, 0.0
        s.last_line = 0.0
        s.spots, s.new_spot_bots = [], []        # spots a person marked to cover; bots just sent to one

    def add_spot(s, pos):
        """A spot to cover: the nearest SPOT_BOTS free bots go there first (replanned at once)."""
        s.spots.append(dict(pos=tuple(float(v) for v in pos), done=False, given_up=False, since=None))
        s.next_t = 0.0

    def clear_spots(s):
        s.spots = []
        s.jobs = {k: j for k, j in s.jobs.items() if j[0] != "spot"}
        s.next_t = 0.0

    def spot_view(s):
        """[{pos, done, given_up, bots}] for the view."""
        on = {}
        for j in s.jobs.values():
            if j[0] == "spot":
                on[j[2]] = on.get(j[2], 0) + 1
        return [dict(pos=[round(v, 2) for v in sp["pos"]], done=sp["done"], given_up=sp["given_up"], bots=on.get(k, 0))
                for k, sp in enumerate(s.spots)]

    def _spots(s, now, bots):
        """Marks spots covered (a bot got there) or given up, and sends the nearest free bots to the open ones."""
        for k, sp in enumerate(s.spots):
            if sp["done"] or sp["given_up"]:
                continue
            x, y, z = sp["pos"]
            if any(math.hypot(p[0] - x, p[1] - y) < SPOT_DONE_R and abs(p[2] - z) < 2.0 for p in bots.values()):
                sp["done"] = True
            elif sp["since"] is not None and now - sp["since"] > SPOT_GIVE_UP:
                sp["given_up"] = True
        open_ = {k for k, sp in enumerate(s.spots) if not sp["done"] and not sp["given_up"]}
        s.jobs = {i: j for i, j in s.jobs.items() if j[0] != "spot" or (j[2] in open_ and i in bots)}
        for k in sorted(open_):
            sp = s.spots[k]
            have = sum(1 for j in s.jobs.values() if j[0] == "spot" and j[2] == k)
            free = sorted((math.hypot(p[0] - sp["pos"][0], p[1] - sp["pos"][1]) + 2.0 * abs(p[2] - sp["pos"][2]), i)
                          for i, p in bots.items() if s.jobs.get(i, (None,))[0] not in ("spot", "jump"))
            for _, i in free[:max(0, SPOT_BOTS - have)]:
                s.jobs[i] = ("spot", sp["pos"], k, now)
                s.new_spot_bots.append(i)
            if sp["since"] is None and (have or free):
                sp["since"] = now

    def _reach(s):
        """Reachable sample cells: Terrain.reach, recomputed over graph_h (new links bots landed count at once)."""
        T = s.T
        if s.spawns:
            T.set_spawns(s.spawns)
        reach = getattr(T, "reach", None)
        if reach is None:
            return np.ones(len(s.x), bool)
        return reach[s.l, s.j * STEP, s.i * STEP]

    def _pieces(s, mask):
        """Connected pieces of the sample cells in mask, per floor level (8-neighbour in the plane): [(size, centre
        sample index)] with the centre the member cell nearest the piece's mean, biggest first."""
        from scipy.ndimage import label
        grid = np.zeros(s.shape, bool)
        grid[s.l[mask], s.j[mask], s.i[mask]] = True
        lab, n = label(grid, structure=np.array([[[0] * 3] * 3, [[1] * 3] * 3, [[0] * 3] * 3]))
        s._lab = lab                              # (the last call's labels: regions, for region_bias)
        if not n:
            return []
        ids = lab[s.l, s.j, s.i]
        out = []
        for k in range(1, n + 1):
            m = np.nonzero(ids == k)[0]
            if len(m) < MIN_CELLS:
                continue
            mx, my = s.x[m].mean(), s.y[m].mean()
            c = m[np.argmin((s.x[m] - mx) ** 2 + (s.y[m] - my) ** 2)]
            out.append((len(m), int(c), m))
        return sorted(out, key=lambda r: -r[0])

    def plan(s, now, bots):
        """bots: {index: (x, y, z)} of the living mapping bots. Recomputes the map and gives out jobs."""
        if now < s.next_t:
            return
        s.next_t = now + PERIOD
        t0 = time.time()
        painted = s.rec.explored_many(s.x, s.y, s.z)
        reach = s._reach()
        s.reach_share = float(reach.mean()) if len(reach) else 0.0
        s.painted_share = float((painted & reach).sum() / max(1, reach.sum()))
        s.regions = s._pieces(reach & ~painted)
        s.region_lab = s._lab                     # sample grid -> region label (0: painted, unreachable or tiny)
        s.islands = s._pieces(~reach & ~painted)
        s._spots(now, bots)
        taken = {}
        for idx, pos in sorted(bots.items()):
            job = s.jobs.get(idx)
            if job and job[0] == "spot":
                continue                              # (a marked spot: _spots keeps or ends it)
            keep = next((r for r in s.regions if job and job[0] == "go" and r[1] == job[2]), None) if job else None
            if keep is not None:                      # its region still has unpainted floor: keep it (new members)
                s.jobs[idx] = ("go", None, keep[1], keep[2])
                taken[keep[1]] = taken.get(keep[1], 0) + 1
                continue
            if job and job[0] == "jump" and now - job[3] < JUMP_JOB_S:
                continue                              # (a take-off it never gets to: dropped after JUMP_JOB_S)
            s.jobs.pop(idx, None)
        # islands: the nearest bot (not already on one) within reach of each, one bot an island
        on_island = {j[2] for j in s.jobs.values() if j[0] == "jump"}
        # (only once most of the walkable floor is painted, two bots at a time: jump tries early on cost the walking
        # bots a sixth of their painting in the simulator, Boneyard)
        late = ISLANDS and s.painted_share >= ISLAND_AFTER
        for size, c, members in (s.islands[:6] if late else []):
            if c in on_island or len(on_island) >= ISLAND_BOTS:
                continue
            free = [(math.hypot(p[0] - s.x[c], p[1] - s.y[c]), idx) for idx, p in bots.items() if idx not in s.jobs]
            free = [f for f in free if f[0] < ISLAND_REACH]
            if not free:
                continue
            _, idx = min(free)
            p = bots[idx]
            # the take-off side: the reachable painted-or-not cell nearest the island
            near = np.nonzero(reach)[0]
            if not len(near):
                continue
            k = near[np.argmin((s.x[near] - s.x[c]) ** 2 + (s.y[near] - s.y[c]) ** 2)]
            s.jobs[idx] = ("jump", (float(s.x[k]), float(s.y[k]), float(s.z[k])), c, now)
            on_island.add(c)
        # regions: big and near, spread over the bots
        for idx, p in sorted(bots.items()):
            if idx in s.jobs or not s.regions:
                continue
            def value(r):
                size, c, _ = r
                d = math.hypot(p[0] - s.x[c], p[1] - s.y[c]) + 2.0 * abs(p[2] - s.z[c])
                return math.sqrt(size) / (1.0 + d / 20.0) / (1.0 + 2.0 * taken.get(c, 0))
            size, c, members = max(s.regions, key=value)
            s.jobs[idx] = ("go", None, c, members)
            taken[c] = taken.get(c, 0) + 1
        s.plan_s = time.time() - t0

    def job(s, index, pos):
        """("go", target) / ("jump", take-off) for this bot, or None. A jump job at its take-off side: ("call", None)."""
        j = s.jobs.get(index)
        if not j:
            return None
        if j[0] == "spot":
            return ("go", j[1])
        if j[0] == "jump":
            if math.hypot(pos[0] - j[1][0], pos[1] - j[1][1]) < JUMP_NEAR:
                s.jobs.pop(index, None)
                return ("call", None)
            return j[:2]
        # a region: no target of its own. The bot's frontier search (by path, Roomba.frontier) prefers it instead
        # (region_bias): straight-line targets ignored walls and floors and painted a third less (sim, Boneyard)
        return None

    def region_bias(s, index, ll, jj, ii):
        """For Roomba.frontier: an extra score (in path units) for candidate nav nodes inside this bot's region."""
        j = s.jobs.get(index)
        lab = getattr(s, "region_lab", None)
        if not j or j[0] != "go" or lab is None:
            return 0.0
        rid = lab[s.l[j[2]], s.j[j[2]], s.i[j[2]]]
        if not rid:
            return 0.0
        inside = lab[ll, np.minimum(jj // STEP, lab.shape[1] - 1), np.minimum(ii // STEP, lab.shape[2] - 1)] == rid
        return REGION_BONUS * inside

    def line(s, now):
        """A status line every 30 s (None in between)."""
        if now - s.last_line < 30.0:
            return None
        s.last_line = now
        jobs = ", ".join(f"{i}:{j[0]}" for i, j in sorted(s.jobs.items()))
        return (f"director: {100 * s.painted_share:.0f}% of the reachable floor painted, {len(s.regions)} regions and "
                f"{len(s.islands)} islands left, plan {getattr(s, 'plan_s', 0):.2f} s; jobs {jobs or 'none'}")
