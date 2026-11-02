"""Forge pieces and other placed objects read from the running Halo: Reach game. A map variant's pieces (Forge World's
Hemorrhage, Paradiso ...) are in its .mvar file, whose format is not documented; but in a match they are ordinary
objects. Each live scenery / crate object gives its tag id, position and axes (+0x44 position, +0x50 forward, +0x5C up).
The game keeps no tag names in memory, but the map's .map file has them in tag-index order (tools/reach_tag_names.py),
so the tag id names the piece exactly (live, Paradiso: 0x20c2 = ff_column, 0x20ee = ff_railing_2). Its shape comes from
the editing kit (tools/object_shapes.py: maps/_shapes/reach.json boxes, maps/_shapes/reach_faces.json every collision
surface), for a match's bots and for LiDAR (brain/maps.py terrain(live_blocks=...)). Since a piece goes in face by face,
each face by its angle: a block's top is floor to stand on, its sides walls, a ramp a ramp. Before, every piece was one
solid box (nothing on it walkable). A piece with no collision model (physics boxes only) is still its solid box.

(Until pieces were guessed from their bounding radius: ambiguous, Hang 'Em High doors 'found' on Forge World. Exact
names replaced it.)

Shields (energy pieces, not solid boxes) by the player's three groups (maps/_shapes/reach_shields.json, sorted live
on Forge World): every one stops shots (a sight line through it is blocked: Terrain.set_glass); a two-way shield lets
bodies through both ways, a one-way shield one way (Terrain.set_barrier with its through direction), a no-pass shield
none (a barrier both ways, or a solid box when it is not thin).
"""
import json
import math
import os
import struct
import sys

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "maps")
# per game (the live reader's TAG_GAME): the object types read (scenery, crate; machines: doors and lifts move, left
# out) and the object's position, forward and up (Halo 4 / H2A: tools/forge_dump.py on the player's ALL ITEMS maps;
# their crates hold the Forge pieces and a map's own crates, Adrift's included)
TYPES = {"reach": (6, 10), "h4": (6, 11), "h2a": (6, 11)}
AXES_AT = {"reach": (0x44, 0x50, 0x5C), "h4": (0x64, 0x70, 0x7C), "h2a": (0x64, 0x70, 0x7C)}
# never solid, by name (brain/placed.py's list: markers, beacons, spawns ...), for the games whose scenery is read whole
SKIP = ("door", "lift", "light", "camera", "cinematic", "skybox", "fx_", "sound", "hologram", "decal", "kill_volume",
        "danger_zone", "spawn", "marker", "beacon", "mp_circle", "flag_base", "flag_stand", "drop_point", "respawn",
        "health")

_SHAPES = {}


def _shapes(game="reach"):
    if game not in _SHAPES:
        p = os.path.join(ROOT, "_shapes", game + ".json")
        _SHAPES[game] = json.load(open(p, encoding="utf-8"))["shapes"] if os.path.exists(p) else {}
    return _SHAPES[game]


def shield_groups():
    """{piece name: (group, through)}: group two_way / one_way / no_pass; through (one-way pieces) "back" = a body
    passes from the piece's front (facing) side to its back, "forward" = along its facing."""
    p = os.path.join(ROOT, "_shapes", "reach_shields.json")
    if not os.path.exists(p):
        return {}
    out = {}
    for group, g in json.load(open(p, encoding="utf-8"))["groups"].items():
        th = g.get("through") if isinstance(g.get("through"), dict) else {}
        for name in g["pieces"]:
            out[name] = (group, next((v for k, v in th.items() if name.startswith(k)), None))
    return out


def _thin(lo, hi):
    return min(hi[0] - lo[0], hi[1] - lo[1]) < 0.5


def shields(pieces, groups=None, shapes=None, game="reach"):
    """[(key, a, b, z0, z1, group, through, box)] for the shields among pieces [(name, pos, (forward, left, up))]: a, b
    their line seen from above (x, y), z0..z1 their height, through the 2D direction a body may cross a one-way one,
    box (pos, axes, min, max) for sight lines. (Reach's groups only: the player sorted Forge World's shields.)"""
    groups = groups if groups is not None else shield_groups() if game == "reach" else {}
    shapes = shapes if shapes is not None else _shapes(game)
    out = []
    for k, (name, pos, (f, l, u)) in enumerate(pieces):
        g, s = groups.get(name), shapes.get(name)
        if not g or not s:
            continue
        (x0, y0, z0), (x1, y1, z1) = s["min"], s["max"]
        if y1 - y0 >= x1 - x0:                    # a wall across its facing: its long side at the middle of its depth
            c = (x0 + x1) / 2
            a = (pos[0] + f[0] * c + l[0] * y0, pos[1] + f[1] * c + l[1] * y0)
            b = (pos[0] + f[0] * c + l[0] * y1, pos[1] + f[1] * c + l[1] * y1)
        else:
            c = (y0 + y1) / 2
            a = (pos[0] + f[0] * x0 + l[0] * c, pos[1] + f[1] * x0 + l[1] * c)
            b = (pos[0] + f[0] * x1 + l[0] * c, pos[1] + f[1] * x1 + l[1] * c)
        n = math.hypot(f[0], f[1]) or 1.0
        through = {"back": (-f[0] / n, -f[1] / n), "forward": (f[0] / n, f[1] / n)}.get(g[1])
        out.append((f"shield{k}:{name}", a, b, pos[2] + z0, pos[2] + z1, g[0], through, (pos, (f, l, u), s["min"], s["max"])))
    return out


def shield_blocks(found):
    """The thick no-pass shields as solid boxes, for the terrain's build (brain/maps.py terrain(live_blocks=...): the
    nav is made from the blocks it is built with)."""
    return [box + (key,) for key, _, _, _, _, group, _, box in found if group == "no_pass" and not _thin(box[2], box[3])]


def apply_shields(T, found):
    """Shields onto terrain T: each blocks sight lines; one-way ones are barriers with their through direction, thin
    no-pass ones barriers both ways (thick ones: shield_blocks, built in). Returns how many."""
    from .core import Vec
    for key, a, b, z0, z1, group, through, box in found:
        T.set_glass(key, *box)
        if group == "one_way" or (group == "no_pass" and _thin(box[2], box[3])):
            T.set_barrier(key, Vec(a[0], a[1], 0.0), Vec(b[0], b[1], 0.0), z0, z1,
                          through=Vec(through[0], through[1], 0.0) if through else None)
    return len(found)


def _pieces(live):
    """(name, pos, (forward, left, up)) of the live scenery and crates in the running match, named by tag id."""
    names = _tag_names(live)
    game = getattr(live, "TAG_GAME", "reach")
    types, (at_p, at_f, at_u) = TYPES.get(game, TYPES["reach"]), AXES_AT.get(game, AXES_AT["reach"])
    tag_at = getattr(live, "TAG_AT", 0)
    if live._blk is None:
        live.players()
    ents, mx, _ = live._array(live.OBJECTS_AT)
    b = live.g.read(ents, mx * 0x18)
    for i in range(mx):
        if not struct.unpack_from("<H", b, i * 0x18)[0] or b[i * 0x18 + live.TYPE_AT] not in types:
            continue
        o = struct.unpack_from("<Q", b, i * 0x18 + 0x10)[0]
        try:
            head = live.g.read(o, max(at_u, tag_at) + 12)
        except OSError:
            continue
        if not head:
            continue
        tag = struct.unpack_from("<I", head, tag_at)[0] & 0xFFFF
        f, u = struct.unpack_from("<3f", head, at_f), struct.unpack_from("<3f", head, at_u)
        nf, nu = math.sqrt(sum(v * v for v in f)) or 1.0, math.sqrt(sum(v * v for v in u)) or 1.0
        f, u = tuple(v / nf for v in f), tuple(v / nu for v in u)
        name = names[tag].rsplit("\\", 1)[-1] if tag < len(names) else None
        if name and game != "reach" and any(s in name for s in SKIP):
            continue                               # (markers, beacons, spawn points: never solid)
        yield name, struct.unpack_from("<3f", head, at_p), (f, _cross(u, f), u)


def live_pieces(live):
    """[(name, pos, (forward, left, up))] of the running match's named scenery and crates: a map variant's layout
    (brain/variants.py files it, with these, under its base map); a Halo 4 / H2A map's own crates and scenery (its export
    lists none: tools/live_bots.py puts them in the nav)."""
    return [p for p in _pieces(live) if p[0]] if _tag_names(live) else []


def nav_pieces(pieces, game="reach"):
    """(blocks, shields) for the nav from pieces [(name, pos, axes)]: each piece's block() (thick no-pass shields as
    solid boxes too) and the shields (apply_shields). brain/maps.py builds a map variant's nav with them."""
    found = shields(pieces, game=game)
    return [b for b in (block(n, p, a, game=game) for n, p, a in pieces) if b] + shield_blocks(found), found


def _tag_names(live):
    """The running map's tag names by index (tools/reach_tag_names.py, cached per map)."""
    cache = getattr(live, "_tag_name_list", None)
    if cache is not None:
        return cache
    sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "tools"))
    import reach_tag_names
    map_file = live.map_name().replace("/", "\\").rsplit("\\", 1)[-1]
    live._tag_name_list = reach_tag_names.cached(map_file, getattr(live, "TAG_GAME", "reach"))
    return live._tag_name_list


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


_FACES = {}


def _faces(game="reach"):
    """{piece name: [(material, [x, y, z, ...]), ...]}: every collision surface (tools/object_shapes.py faces())."""
    if game not in _FACES:
        p = os.path.join(ROOT, "_shapes", game + "_faces.json")
        _FACES[game] = json.load(open(p, encoding="utf-8"))["faces"] if os.path.exists(p) else {}
    return _FACES[game]


def block(name, pos, axes, skip_materials=("energy", "hologram"), game="reach"):
    """One piece for the nav (nav_pieces): (pos, (forward, left, up), min, max, name[, faces]). A piece with its
    collision surfaces known carries them (faces) and goes into the nav face by face, a floor, ramp or wall by each
    face's angle, else as its solid box. None: unknown, energy and hologram alone (lights, power-ups; shields:
    apply_shields), or a box too low or small for a body to bump into. A building piece's own energy panes (the tall
    tower's, the window wall's) are solid with it."""
    s, f = _shapes(game).get(name), _faces(game).get(name)
    if not s:
        return None
    if f and not all(any(m in mat for m in skip_materials) for mat, _ in f):
        return pos, axes, s["min"], s["max"], name, f
    if any(m in s.get("material", "") for m in skip_materials):
        return None                               # (shields: apply_shields)
    lo, hi = s["min"], s["max"]
    if hi[2] - lo[2] < 0.35 or (hi[0] - lo[0]) * (hi[1] - lo[1]) < 0.04:
        return None
    return pos, axes, lo, hi, name
