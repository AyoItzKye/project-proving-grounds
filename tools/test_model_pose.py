"""The profile view's 3D bots hold their guns by the game's own hand markers: checks that fail on the code before.

1. mount: on a small made-up arm, the hand's marker lands exactly on the gun's grip, in the grip's turn, and the
   forearm's roll for a straighter wrist does not move it
2. curl: the fingers close toward the palm (the old pose left them splayed)
3. flat_part: a gun part with no diffuse map gets a gun colour of its own (dark under its own glow map; a glow for a
   luminous part), never "" (the renderer then gave it the armor colour: Halo 2's battle rifle was green)
4. make_models' clean-up of unused textures (a re-export numbers them anew) keeps every texture a model names
5. the packed models (when tools/make_models.py has exported them on this machine): both hands reach the gun, no wrist
   turns more than 45 degrees from the game's bind pose, every elbow bends on its own hinge (the player:
   the IK only swung the upper arm, the hinges 0.35-0.65 of the natural way), the gun
   held in the palm (Reach's and Halo 2: Anniversary's hand markers sit at the wrist: the sword's hilt hung outside the
   fist), and the gun no more than 9 mm into the torso and legs of the default pieces (the arms and hands left out;
   "Halo 3 rifle in body a lil bit": 16 mm, Reach, Halo 2: Anniversary and Halo 4 26-30 mm)
6. ... a Spartan holds the rifle close at low ready: both elbows at least 0.045 u (a Spartan's units) below the shoulders (the right one sat level
   with the shoulder, a flared "chicken wing"), the grip hand within 0.15 u in front of the pelvis (it was out at arm's
   length, the rifle standing up before the face from the side), the muzzle down toward the left knee (its slope -0.3
   or steeper, the player's picture), the knees and feet no wider than 1.15 / 1.25 times the model's own stance ("Halo
   CE kinda bow legged": its knees 1.30 times)
7. ... an Elite slouches forward as in the player's picture: the torso 12 to 22 degrees forward, the face 2 to 25 degrees down
   (Reach's "looking up too much"), its feet no wider than 1.3 times the model's own stance (they were half again as
   wide, a crab's crouch)
8. read_obj leaves out Reach's Elite assassination knives (elite_knifeblade_l / _r: thin blue blades out of both fists
   in every profile), not its other body parts
9. a forearm's roll spread along its twist helpers (the elbow's piece none, the hand all: rolled whole at the elbow it
   tore Halo 2: Anniversary's elbow armour, "completely self explanatory")

usage: python -I test_model_pose.py      -> "model pose OK"
"""
import os
import struct
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import model_pack2 as mp  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, ".."))


def arm():
    """A pelvis, a right arm hanging down (each bone's x along it, as Halo's) and an index finger with a slight curl."""
    def m(x, y, p):
        z = np.cross(x, y)
        M = np.eye(4)
        M[:3, :3] = [x, y, z]
        M[3, :3] = p
        return M
    down, side = np.array([0, 0, -1.0]), np.array([0, 1.0, 0])
    bones = [("pelvis", -1, m(np.array([1.0, 0, 0]), side, (0, 0, 0.4))),
             ("r_upperarm", 0, m(down, side, (0, -0.09, 0.57))),
             ("r_forearm", 1, m(down, side, (0, -0.09, 0.46))),
             ("r_hand", 2, m(down, side, (0, -0.09, 0.345))),
             ("r_index_low", 3, m(down, side, (0, -0.088, 0.295))),
             ("r_index_mid", 4, m(down, side, (0, -0.086, 0.278))),
             ("r_index_tip", 5, m(down, side, (0, -0.082, 0.266)))]
    return mp.Skeleton(bones)


HANDY = ("hand", "finger", "index", "middle", "ring", "pinky", "thumb", "grip", "wrist", "palm")


def gun_depth(S, body, held, W, origin):
    """How far the gun sinks under the skin of the torso and legs of the body's default pieces (u): its vertices
    against the nearest body vertex's normal (the arms and hands left out: a grip sits in the fist, the forearms on the
    gun)."""
    from scipy.spatial import cKDTree
    pos, nrm, _, faces = mp.read_obj(body, (), mp.instance_owners(body + ".regions.json"))
    bones, idx, w = mp.read_skin(body + ".skin")
    regions = {}
    for (region, pi, perm, mat) in faces:
        regions.setdefault(region, set()).add((pi, perm))
    keep = []
    for region, perms in regions.items():
        pick = next((p for p in perms if p[1] in ("default", "base")), min(perms))
        keep += [faces[k] for k in faces if k[0] == region and (k[1], k[2]) == pick and faces[k]]
    vi = np.unique(np.concatenate([np.asarray(f, np.int64) for f in keep]))
    handy = np.array([any(t in n for t in HANDY + ("upperarm", "forearm", "elbow", "clav", "shoulder"))
                      for n, _, _ in bones])
    vi = vi[~handy[idx[vi, np.argmax(w[vi], axis=1)]]]
    P, N = S.skin(pos[vi], nrm[vi], idx[vi], w[vi])
    wpos, _, _, wfaces = mp.read_obj(held)
    G = wpos[np.unique(np.concatenate([np.asarray(f, np.int64) for f in wfaces.values() if f]))] @ W + origin
    dist, j = cKDTree(P).query(G)
    s = np.einsum("ij,ij->i", G - P[j], N[j])
    inside = (dist < 0.03) & (s < 0)
    return float(-s[inside].min()) if inside.any() else 0.0


def palm_gaps(S, bm, species, held, W, origin):
    """{"r", "l": how far each palm is from the gun's nearest vertex (u, in a Spartan's units)}: the palm 60% of the way
    from the wrist joint to the middle (or index) knuckle; Halo: CE has no finger bones, its hand marker sits there."""
    from scipy.spatial import cKDTree
    wpos, _, _, wf = mp.read_obj(held)
    tree = cKDTree(wpos[np.unique(np.concatenate([np.asarray(f, np.int64) for f in wf.values() if f]))] @ W + origin)
    k = (S.pos("head")[2] - min(m[3, 2] for m in S.pose)) / 0.61
    out = {}
    for side in ("r", "l"):
        knuck = next((n for n in S.names if n.endswith((f"{side}_middle1", f"{side}_middle_low", f"{side}_index1"))), None)
        h = S.pos(f"{side}_hand")
        if knuck is None:
            mk = mp.hand_hold(S, bm, "right" if side == "r" else "left", species)
            p = mk[1] @ S.pose[mk[0]][:3, :3] + S.pose[mk[0]][3, :3]
        else:
            p = h + 0.6 * (S.pose[S.names.index(knuck)][3, :3] - h)
        out[side] = float(tree.query(p)[0] / k)
    return out


def head_pitch(S):
    """How far the face turned down from the model's own rest (degrees, negative down): the head bone's axis that
    points forward at rest, its slope now against its slope then."""
    h = S.i("head")
    R0, R1 = S.bind[h][:3, :3], S.pose[h][:3, :3]
    axis = max(range(3), key=lambda j: abs(R0[j][0]))
    slope = lambda f: np.degrees(np.arctan2(f[2], np.hypot(f[0], f[1])))
    sgn = np.sign(R0[axis][0])
    return float(slope(sgn * R1[axis]) - slope(sgn * R0[axis]))


def main():
    fails = []
    # 1. the marker on the grip, exactly
    S = arm()
    marker = (3, np.array([0.047, 0.004, -0.004]), mp.qrow((0.0, 0.0, np.sin(np.radians(7.5)), np.cos(np.radians(7.5)))))
    grip = np.array([0.12, -0.05, 0.42])
    W = mp.frame(np.array([0.3, 0.7, -0.6]), np.array([0, 0.6, 0.7]))
    bend, short = mp.mount(S, "r_hand", "r_upperarm", "r_forearm", marker, grip, W, np.array([-0.3, -0.8, -0.4]))
    H = S.pose[S.i("r_hand")]
    at, turn = marker[1] @ H[:3, :3] + H[3, :3], marker[2] @ H[:3, :3]
    if short > 1e-6 or np.abs(at - grip).max() > 1e-6 or np.abs(turn - W).max() > 1e-6:
        fails.append(f"mount: marker at {at.round(4)} turn off by {np.abs(turn - W).max():.2e}, want {grip}; short {short}")
    lengths = [np.linalg.norm(S.pos(a) - S.pos(b)) for a, b in (("r_upperarm", "r_forearm"), ("r_forearm", "r_hand"))]
    if abs(lengths[0] - 0.11) > 1e-6 or abs(lengths[1] - 0.115) > 1e-6:
        fails.append(f"mount: the arm's bones changed length {lengths}")
    # 2. the fingers close toward the palm (+y in the hand)
    tip = lambda: (np.r_[S.pos("r_index_tip"), 1] @ np.linalg.inv(S.pose[S.i("r_hand")]))[1]
    before = tip()
    mp.curl(S, "r", 55)
    if tip() - before < 0.01:
        fails.append(f"curl: the index tip moved {tip() - before:.4f} toward the palm, want a closed hand")
    # 3. a gun part without a diffuse map
    with tempfile.TemporaryDirectory() as d:
        from PIL import Image
        f = mp.flat_part(d, "h2w", "battle_rifle_metal", "diffuse", {})
        g = mp.flat_part(d, "h3w", "display", "diffuse", {"self_illum": {"file": "t1.png"}})
        lum = mp.flat_part(d, "h2elitew", "plasma_rifle_luminous", "self_illum", {})   # (its name was cut at 47
        if len(lum) > 47 or not os.path.exists(os.path.join(d, lum)):                    # characters: no glow)
            fails.append(f"flat_part: {lum!r} does not fit the .mdl's 47 characters or was not written")
        if not f or not g or not lum or mp.flat_part(d, "h2w", "battle_rifle_metal", "normal", {}):
            fails.append(f"flat_part: diffuse {f!r}, under a glow map {g!r}, glow {lum!r}")
        else:
            rgb = Image.open(os.path.join(d, f)).getpixel((0, 0))[:3]
            dark = Image.open(os.path.join(d, g)).getpixel((0, 0))[:3]
            if rgb != mp.FLAT[-1][1] or max(dark) > 30:
                fails.append(f"flat_part: gunmetal {rgb}, under a glow map {dark}")
    # 3b. Halo 2: Anniversary's armor maps: ..._s the surface, ..._d the colour mask, ..._c1 a control map (its bots were
    #     red and green: the mask drawn as the colour); other games' maps keep their usage
    h2a = [{"usage": "diffuse", "bitmap": "x\\h2a_var1_armor_s", "file": "a"}, {"usage": "other", "bitmap": "x\\h2a_var1_armor_c1",
           "file": "b"}, {"usage": "diffuse", "bitmap": "x\\h2a_var1_armor_d", "file": "c"}]
    got = [mp.slot_of(m, h2a) for m in h2a]
    plain = [{"usage": "diffuse", "bitmap": "x\\assault_rifle_d", "file": "d"}, {"usage": "other", "bitmap": "x\\ar_c1", "file": "e"}]
    if got != ["diffuse", "control", "color_change"] or [mp.slot_of(m, plain) for m in plain] != ["diffuse", "other"]:
        fails.append(f"slot_of: H2A armor {got}, a plain gun {[mp.slot_of(m, plain) for m in plain]}")
    # 4. make_models' clean-up keeps what a model names and removes the rest
    sys.argv = ["make_models.py"]
    import make_models
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "tex"))
        files = [b"used_diffuse.png", b"", b"used_normal.jpg", b"", b""]
        with open(os.path.join(d, "x.mdl"), "wb") as fh:
            fh.write(b"HBMD" + struct.pack("<IIIII", 2, 0, 0, 0, 1) + struct.pack("<6f", *[0.0] * 6))
            fh.write(b"mat".ljust(48, b"\0") + b"".join(f.ljust(48, b"\0") for f in files) + struct.pack("<2f", 1, 0))
        for t in ("used_diffuse.png", "used_normal.jpg", "old_t17012_diffuse.png"):
            open(os.path.join(d, "tex", t), "wb").close()
        gone = make_models.prune(d)
        if gone != 1 or sorted(os.listdir(os.path.join(d, "tex"))) != ["used_diffuse.png", "used_normal.jpg"]:
            fails.append(f"prune: removed {gone}, left {sorted(os.listdir(os.path.join(d, 'tex')))}")
    # 9. a forearm's roll spread along its twist helpers: the elbow's piece none, a helper halfway half, the hand all
    #    (rolled whole at the elbow it tore H2A's elbow armour)
    def mk(x, p):
        M = np.eye(4)
        M[3, :3] = p
        return M
    T = mp.Skeleton([("b_l_forearm", -1, mk(0, (0, 0, 0))), ("b_l_elbow_armor", 0, mk(0, (0, 0, 0))),
                     ("b_l_forearm_helper2", 0, mk(0, (0.05, 0, 0))), ("b_l_hand", 0, mk(0, (0.1, 0, 0)))])
    mp.roll_forearm(T, "l_forearm", "l_hand", np.array([1.0, 0, 0]), 90)
    turned = lambda n: np.degrees(np.arccos(np.clip((np.trace(T.pose[T.i(n)][:3, :3]) - 1) / 2, -1, 1)))
    got = [round(turned(n)) for n in ("l_forearm", "l_elbow_armor", "l_forearm_helper2", "l_hand")]
    if got != [0, 0, 45, 90]:
        fails.append(f"roll_forearm: forearm, elbow armour, helper, hand turned {got} (want [0, 0, 45, 90])")
    # 8. the knives are left out, the body kept
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "e.obj")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write("v 0 0 0\nv 1 0 0\nv 0 1 0\ng body|0|default|elite_base_upper\nf 1 2 3\n"
                     "g body|0|default|elite_knifeblade_l\nf 1 2 3\ng body|0|default|elite_knifeblade_r_plasma\nf 1 2 3\n")
        kept = sorted(k[3] for k in mp.read_obj(p)[3])
        if kept != ["elite_base_upper"]:
            fails.append(f"read_obj: kept {kept} (want only the body, not the assassination knives)")
    # 5. the real models, where exported (make_models' list, with each model's own hold)
    seen, base = 0, {k: dict(v) for k, v in mp.HOLDS.items()}
    for weapon, species, game, _, _, _, opts in make_models.MODELS:
        body = os.path.join(ROOT, "maps", "_models", game, species + ".obj")
        held = os.path.join(ROOT, "maps", "_models", game, weapon + "_weapon.obj")
        if not all(os.path.exists(p) for p in (body + ".skin", body + ".markers.json", held + ".markers.json")):
            continue
        seen += 1
        mp.HOLDS = {k: dict(v) for k, v in base.items()}
        if "--hold" in opts:
            mp.apply_hold(species, opts[opts.index("--hold") + 1])
        two = "--one-hand" not in opts
        bones = mp.read_skin(body + ".skin")[0]
        S, B = mp.Skeleton(bones), mp.Skeleton(bones)
        bm = mp.read_markers(body + ".markers.json")
        W, origin, out = mp.pose_hold(S, species, bm, mp.gun_markers(held), two)
        if two and "left" not in out:
            fails.append(f"{weapon}: two-handed, but the left hand is not on the gun")
        for hand, (b, sh) in out.items():
            if sh > 0.005 or b > 45:
                fails.append(f"{weapon}: {hand} hand {sh:.3f} u short of the gun, wrist turned {b:.0f} degrees")
        for side in ("r", "l"):                                # each elbow on its own hinge
            a, e, c = (S.pos(f"{side}_{n}") for n in ("upperarm", "forearm", "hand"))
            n = np.cross(e - a, c - e)
            h = S.hinge(f"{side}_upperarm", f"{side}_forearm", f"{side}_hand") @ S.pose[S.i(f"{side}_upperarm")][:3, :3]
            if np.linalg.norm(n) > 1e-6 and np.dot(h, n) / np.linalg.norm(h) / np.linalg.norm(n) < 0.95:
                fails.append(f"{weapon}: the {side} elbow bends off its own hinge ({np.dot(h, n) / np.linalg.norm(h) / np.linalg.norm(n):+.2f})")
        rh = mp.hand_hold(S, bm, "right", species)             # in the palm: past halfway to the knuckles
        kn = [k for k, nm in enumerate(S.names) if nm.endswith(("r_index1", "r_index_low", "r_middle1", "r_middle_low"))]
        if kn:
            Hb = S.bind[S.i("r_hand")]
            reach = np.linalg.norm((S.bind[kn[0]][3, :3] - Hb[3, :3]) @ Hb[:3, :3].T)
            if np.linalg.norm(rh[1]) < 0.5 * reach:
                fails.append(f"{weapon}: the gun held {np.linalg.norm(rh[1]):.3f} u from the wrist joint, the knuckles "
                             f"{reach:.3f} (want in the palm)")
        dp = gun_depth(S, body, held, W, origin)
        if dp > 0.009:
            fails.append(f"{weapon}: the gun {dp * 1000:.0f} mm into the body")
        if two:                                                # both palms on the gun (the player: "Halo reach
            for side, gap in palm_gaps(S, bm, species, held, W, origin).items():   # spartan not holding gun with left
                if gap > 0.035:                                # hand": its wrist marker read as a palm put it 0.042 off)
                    fails.append(f"{weapon}: the {side} palm {gap:.3f} u from the gun (want on it, within 0.035)")
        feet = min(m[3, 2] for m in S.pose)
        k = (S.pos("head")[2] - feet) / 0.61                  # a Spartan's units (its head 0.61 over its feet)
        pel = S.pos("pelvis")
        span = lambda Sk, n: float(np.linalg.norm((Sk.pos("l_" + n) - Sk.pos("r_" + n))[:2]))
        fwd = mp.FWD @ mp.rot(mp.UP, mp.HOLDS[species]["yaw"])
        if species == "spartan":
            for side in ("r", "l"):
                drop = (S.pos(f"{side}_upperarm")[2] - S.pos(f"{side}_forearm")[2]) / k
                if drop < 0.045:
                    fails.append(f"{weapon}: the {side} elbow only {drop:+.2f} u below its shoulder (flared out)")
            ahead = (S.pos("r_hand") - pel) @ fwd / k
            if ahead > 0.15 or W[0][2] > -0.3:
                fails.append(f"{weapon}: the grip hand {ahead:.2f} u in front of the pelvis (want within 0.15), the "
                             f"muzzle's slope {W[0][2]:+.2f} (want down, -0.3 or steeper)")
            if span(S, "calf") > 1.15 * span(B, "calf") or span(S, "foot") > 1.25 * span(B, "foot"):
                fails.append(f"{weapon}: bow legged: knees {span(S, 'calf'):.3f} u apart (its own {span(B, 'calf'):.3f}), "
                             f"feet {span(S, 'foot'):.3f} (its own {span(B, 'foot'):.3f})")
            # a stance, not stiff legs: the easy knee at least 12 degrees, both bending forward
            bends = []
            for side in ("l", "r"):
                a, kn, c = (S.pos(f"{side}_{n}") for n in ("thigh", "calf", "foot"))
                u, v = (kn - a) / np.linalg.norm(kn - a), (c - kn) / np.linalg.norm(c - kn)
                bends.append(np.degrees(np.arccos(np.clip(u @ v, -1, 1))))
                if (kn - c) @ fwd < 0:
                    fails.append(f"{weapon}: the {side} knee behind its ankle (bent backward)")
            if max(bends) < 12:
                fails.append(f"{weapon}: stiff legs: knees bent {bends[0]:.0f} / {bends[1]:.0f} degrees (want the easy one 12+)")
        else:
            neck = next(n for n in ("neck", "neck0") if n in S.names or "b_" + n in S.names)
            v = S.pos(neck) - pel
            lean = np.degrees(np.arctan2(v @ fwd, v[2]))
            hp = head_pitch(S)
            if span(S, "foot") > 1.3 * span(B, "foot") or not 12.0 <= lean <= 22.0 or not -25.0 <= hp <= -2.0:
                fails.append(f"{weapon}: feet {span(S, 'foot'):.3f} u apart (its own {span(B, 'foot'):.3f}), torso "
                             f"{lean:.0f} degrees forward (want 12-22), face {hp:+.0f} degrees from its rest (want 2-25 "
                             f"down)")
    mp.HOLDS = base
    # 6. Halo 3's packed Spartan wears every backpack its customization table lists (the player: "the backpacks dont
    #    appear on the avatars"), each at the torso: centred 0.05-0.40 u from the chest pieces (against the back, not in it or off in the air)
    h3 = os.path.join(ROOT, "native", "bin", "models", "h3_spartan.mdl")
    if os.path.exists(h3):
        import json
        b = open(h3, "rb").read()
        _, ng, nv, ni, nm = struct.unpack_from("<IIIII", b, 4)
        off = 48 + nm * (48 + 5 * 48 + 8)
        groups = []
        for k in range(ng):
            region = b[off:off + 24].split(b"\0")[0].decode()
            perm = b[off + 24:off + 56].split(b"\0")[0].decode()
            first, count = struct.unpack_from("<II", b, off + 64)
            groups.append((region, perm, first, count))
            off += 76
        verts = np.frombuffer(b, np.float32, nv * 8, off).reshape(nv, 8)[:, :3]
        ind = np.frombuffer(b, np.uint32, ni, off + nv * 32)
        at = lambda rg, pm: [verts[ind[f:f + n]] for r, p, f, n in groups if r == rg and (pm is None or p == pm)]
        chest = np.vstack(at("chest", None)).mean(0)
        opts = json.load(open(os.path.join(ROOT, "maps", "_looks", "h3_armory.json")))["options"]["45"]
        for (region, perm, _), in opts:
            if perm == "empty":
                continue
            got = at(region, perm)
            d = np.linalg.norm(np.vstack(got).mean(0) - chest) if got else None
            if d is None or not 0.05 <= d <= 0.40:
                fails.append(f"h3_spartan.mdl: backpack {perm} " + ("missing" if d is None else f"{d:.2f} u from the chest"))
    if fails:
        print("FAIL")
        print("\n".join(fails))
        sys.exit(1)
    print(f"model pose OK ({seen} of {len(make_models.MODELS)} packed models checked)")


if __name__ == "__main__":
    main()
