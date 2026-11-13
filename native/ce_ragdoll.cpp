// ce_ragdoll.cpp: Halo 2 style ragdolls for Halo CE (halo1.dll, MCC 1.3528). Halo CE has no ragdolls: a dead biped
// plays a canned death animation and freezes. Halo 2 (halo2.dll FUN_18092ab00 and friends, decoded Nov 13) turns a
// dead biped into 10 Havok rigid bodies from its physics_model (Master Chief: pelvis-torso box, head, upper arms,
// forearms, thighs, calves), joined by ragdoll constraints (cones) and limited hinges (knees, elbows), gives each body a
// velocity from the killing hit (strength min(biped value, 0.7) x (1.5 + 1.75 r), bodies further along the hit pushed
// harder, an upward part 0.75 + 0.75 r) and writes the bodies' poses into the biped's node matrices every tick.
//
// Halo CE here, same plan without Havok: a position-based solver over the cyborg skeleton.
// - Node matrices: biped object + [u16 +0x1AE] (size +0x1AC), one 0x34-byte matrix per node (scale, forward, left, up,
//   position; world space). The renderer skins from them (live Nov 13: a lifted node drew as a stretched line).
// - FUN_180b3a614(object handle) builds an object's node matrices each tick (found with a hardware write watch on a
//   biped's matrix, Nov 13). Hooked: after it runs, a ragdolled body's pose replaces the death animation's. A corpse at
//   rest (+0x10 bit 0x800000, 1.3 to 2.9 s after death) is no longer rebuilt, so the pose written at the start of each
//   tick (ce_ragdoll_tick, from botcore's tick hook) stays too.
// - Death: +0x10 bit 0x10000 (set the tick the biped dies). The solver starts 3 ticks later: the death animation picked
//   from the hit's direction has begun, and its motion gives the bodies their starting velocities and the push.
// - Bodies (Halo 2's 10): torso (pelvis, hips, spine, neck, shoulders, a point in front of the chest; kept rigid by
//   shape matching), head, upper arms, forearms (hands follow), thighs, calves (feet follow). Joint limits from Halo 2's
//   masterchief.physics_model: head cone 35 deg, hips and shoulders cones, knee hinge -7.5..80 deg, elbow hinge
//   (95 deg wide), each widened to take the pose the body died in.
// - Ground: the corpse object's own height, which the game's physics keeps on the floor (the corpse slides, falls off
//   ledges and is thrown by explosions as before; the ragdoll follows it across the floor and lies on it). No walls:
//   Halo CE's collision test was not found, so a limb can reach into a wall the corpse lies against (as CE's own death
//   animations do).
// - The push: Halo 2's strengths x PUSH_SCALE (0.3, by eye: unscaled, bodies went head over heels).
// - Drawn by forward kinematics from the bodies' turns, so limbs keep their length whatever the solver leaves.
// Skeletons are matched by node name (bip01 ...): any biped with the 16 nodes needed gets a ragdoll, others never.
// Multiplayer games only.
// Live checks (Nov 13, CE slayer, 15 bots): 56 corpses over two runs, no NaN, axes orthonormal, bodies at rest lying
// flat (top node 0.07 to 0.2 u over the floor; one 0.38); with forward kinematics bones within 0.5% of the skeleton's
// but where the death animation's own pose differs (one thigh, 6.6%); scratch tools in logs/tmp/ragdoll (death_cam.py
// films a death in front of the camera, rag_audit.py checks every corpse).
#include <windows.h>
#include <math.h>
#include <stdint.h>
#include <string.h>
#include "third_party/minhook/include/MinHook.h"

void logf(const char* fmt, ...);

namespace {

const uintptr_t RVA_NODE_MATRICES = 0xB3A614;     // void (object handle)
const uintptr_t RVA_OBJECT_HEADERS = 0x1C42248, RVA_OBJECT_POOL = 0x2D9CDF8, RVA_TAGS = 0x2D9CE10;
const uint32_t TAG_BASE = 0x50000000;
// the running game variant, +0x30 its engine (1 CTF, 2 Slayer ... as botcore's post-game rows read it): multiplayer
// only. Campaign (no engine) is left alone: its Marines and Elites, and its Anniversary graphics (Tab does nothing in
// a multiplayer game: classic only), were never tried
const uintptr_t RVA_VARIANT = 0x2E9F770;
const uint8_t PROLOGUE[24] = {0x48, 0x8B, 0xC4, 0x48, 0x89, 0x58, 0x10, 0x48, 0x89, 0x70, 0x18, 0x48, 0x89, 0x78,
                              0x20, 0x55, 0x41, 0x54, 0x41, 0x55, 0x41, 0x56, 0x41, 0x57};
const uint32_t F_DEAD = 0x10000;
const int START_TICKS = 3, MAX_NODES = 64, SLOTS = 24, CACHE = 2048;
const int SUB = 2, ITER = 6;                      // substeps a tick, solver passes a substep
const float G_SUB = 3.22f / (60.0f * 60.0f);      // gravity 32.2 ft/s (1 world unit = 10 ft) a 1/60 s substep
const float DEG = 3.14159265f / 180.0f;
const float PUSH_SCALE = 0.3f;                    // Halo 2's push strengths, scaled (set by eye, live)

struct V { float x, y, z; };
inline V operator+(V a, V b) { return {a.x + b.x, a.y + b.y, a.z + b.z}; }
inline V operator-(V a, V b) { return {a.x - b.x, a.y - b.y, a.z - b.z}; }
inline V operator*(V a, float s) { return {a.x * s, a.y * s, a.z * s}; }
inline float dot(V a, V b) { return a.x * b.x + a.y * b.y + a.z * b.z; }
inline V cross(V a, V b) { return {a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x}; }
inline float len(V a) { return sqrtf(dot(a, a)); }
inline V norm(V a, V fallback = {0, 0, 1}) { float l = len(a); return l > 1e-7f ? a * (1.0f / l) : fallback; }
inline float clampf(float v, float lo, float hi) { return v < lo ? lo : v > hi ? hi : v; }

struct Q { float w, x, y, z; };
inline Q qmul(Q a, Q b) {
    return {a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z, a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
            a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x, a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w};
}
inline Q qnorm(Q q) {
    float l = sqrtf(q.w * q.w + q.x * q.x + q.y * q.y + q.z * q.z);
    return l > 1e-9f ? Q{q.w / l, q.x / l, q.y / l, q.z / l} : Q{1, 0, 0, 0};
}
inline V qrot(Q q, V v) {
    V u{q.x, q.y, q.z};
    V t = cross(u, v) * 2.0f;
    return v + t * q.w + cross(u, t);
}
inline Q qaxis(V axis, float angle) { float s = sinf(angle * 0.5f); return {cosf(angle * 0.5f), axis.x * s, axis.y * s, axis.z * s}; }
Q qswing(V f, V t) {                               // shortest rotation taking unit f to unit t
    float d = dot(f, t);
    if (d < -0.9999f) {
        V a = fabsf(f.x) < 0.9f ? cross(f, V{1, 0, 0}) : cross(f, V{0, 1, 0});
        return qaxis(norm(a), 3.14159265f);
    }
    V c = cross(f, t);
    return qnorm(Q{1 + d, c.x, c.y, c.z});
}

// particles: nodes by name, then two made up at death
enum { P_PELVIS, P_LHIP, P_RHIP, P_CHEST, P_NECK, P_LSH, P_RSH, P_LKNEE, P_RKNEE, P_LANK, P_RANK, P_LELB, P_RELB,
       P_LWR, P_RWR, P_HEAD, P_BELLY, NP };
const int NODE_PARTICLES = 16;                     // P_HEAD's node is the head (its particle sits in the head's middle)
const char* const PARTICLE_NODE[NODE_PARTICLES] = {
    "bip01 pelvis", "bip01 l thigh", "bip01 r thigh", "bip01 spine1", "bip01 neck", "bip01 l upperarm",
    "bip01 r upperarm", "bip01 l calf", "bip01 r calf", "bip01 l foot", "bip01 r foot", "bip01 l forearm",
    "bip01 r forearm", "bip01 l hand", "bip01 r hand", "bip01 head"};
const float RADIUS[NP] = {0.05f, 0.04f, 0.04f, 0.06f, 0.04f, 0.035f, 0.035f, 0.03f, 0.03f, 0.025f, 0.025f, 0.025f,
                          0.025f, 0.025f, 0.025f, 0.05f, 0.05f};
const int TORSO_SET[] = {P_PELVIS, P_LHIP, P_RHIP, P_CHEST, P_NECK, P_LSH, P_RSH, P_BELLY};
const int NT = sizeof TORSO_SET / sizeof TORSO_SET[0];

// bodies: the torso, then bones (from particle a to b, turning with their parent body)
enum { G_TORSO, G_HEAD, G_LUA, G_LFA, G_RUA, G_RFA, G_LTH, G_LCA, G_RTH, G_RCA, NG };
struct Bone { int a, b, parent; };
const Bone BONE[NG] = {{0, 0, -1}, {P_NECK, P_HEAD, G_TORSO}, {P_LSH, P_LELB, G_TORSO}, {P_LELB, P_LWR, G_LUA},
                       {P_RSH, P_RELB, G_TORSO}, {P_RELB, P_RWR, G_RUA}, {P_LHIP, P_LKNEE, G_TORSO},
                       {P_LKNEE, P_LANK, G_LTH}, {P_RHIP, P_RKNEE, G_TORSO}, {P_RKNEE, P_RANK, G_RTH}};
struct NodeBody { const char* name; int body; };   // nodes named here turn with that body; others with their parent's
const NodeBody NODE_BODY[] = {
    {"bip01 pelvis", G_TORSO}, {"bip01 spine", G_TORSO}, {"bip01 spine1", G_TORSO}, {"bip01 neck", G_TORSO},
    {"bip01 l clavicle", G_TORSO}, {"bip01 r clavicle", G_TORSO}, {"bip01 head", G_HEAD},
    {"bip01 l upperarm", G_LUA}, {"bip01 l forearm", G_LFA}, {"bip01 l hand", G_LFA},
    {"bip01 r upperarm", G_RUA}, {"bip01 r forearm", G_RFA}, {"bip01 r hand", G_RFA},
    {"bip01 l thigh", G_LTH}, {"bip01 l calf", G_LCA}, {"bip01 l foot", G_LCA},
    {"bip01 r thigh", G_RTH}, {"bip01 r calf", G_RCA}, {"bip01 r foot", G_RCA}};
// joint limits: cones on bodies hung off the torso (an axis in the torso's frame at death: forward, left, up; the half
// angle), hinges below them (the bend axis is the one the joint was bent around at death)
struct Cone { int body; float fwd, left, up, half; };
const Cone CONE[] = {{G_HEAD, 0, 0, 1, 35}, {G_LTH, 0.35f, 0.15f, -1, 55}, {G_RTH, 0.35f, -0.15f, -1, 55},
                     {G_LUA, 0.3f, 0.7f, -0.6f, 100}, {G_RUA, 0.3f, -0.7f, -0.6f, 100}};
struct Hinge { int body; float lo, hi; bool knee; };
const Hinge HINGE[] = {{G_LCA, -7.5f, 80, true}, {G_RCA, -7.5f, 80, true}, {G_LFA, -5, 95, false}, {G_RFA, -5, 95, false}};
const int NC = sizeof CONE / sizeof CONE[0], NH = sizeof HINGE / sizeof HINGE[0];

struct Skeleton {                                  // per biped tag
    uint32_t tag;
    bool ok;
    int nodes;
    int8_t particle_node[NODE_PARTICLES];
    int8_t body[MAX_NODES];
};
Skeleton g_skel[16];

struct Cache {                                     // a live biped's node positions last tick (the start velocities)
    uint32_t handle;
    int dead_ticks;
    V obj;
    V p[NODE_PARTICLES];
};
Cache g_cache[CACHE];

struct Rag {
    uint32_t handle;
    bool used;
    int still;
    uint32_t age;
    const Skeleton* sk;
    V x[NP], xp[NP], x0[NP];
    float bone_len[NG];
    V cone_axis[NC];
    float cone_cos[NC];
    V hinge_axis[NH];
    float hinge_lo[NH], hinge_hi[NH];
    Q q[NG];
    V c0, obj;
    int nodes;
    float m0[MAX_NODES][13], out[MAX_NODES][13];
};
Rag g_rag[SLOTS];
uint32_t g_tick, g_seed = 0x9E3779B9u;
uint8_t* g_h1;
typedef void(__fastcall* nodes_fn)(uint64_t handle);
nodes_fn g_nodes_orig;

float rnd() { g_seed = g_seed * 1664525u + 1013904223u; return (g_seed >> 8) * (1.0f / 16777216.0f); }

uint8_t* object_of(uint32_t handle, int* type) {
    uint8_t* hdr = *(uint8_t**)(g_h1 + RVA_OBJECT_HEADERS);
    if (!hdr || handle == 0xFFFFFFFFu) return nullptr;
    uint32_t i = handle & 0xFFFF;
    if ((int)i >= *(int16_t*)(hdr + 0x20)) return nullptr;
    uint8_t* e = hdr + *(int32_t*)(hdr + 0x34) + i * 12;
    if (*(uint16_t*)e != (handle >> 16)) return nullptr;
    int32_t off = *(int32_t*)(e + 8);
    if (off == -1) return nullptr;
    if (type) *type = e[3];
    return *(uint8_t**)(g_h1 + RVA_OBJECT_POOL) + 0x34 + off;
}

float* matrices(uint8_t* o, int* count) {
    int16_t at = *(int16_t*)(o + 0x1AE);
    if (at == -1) return nullptr;
    *count = *(uint16_t*)(o + 0x1AC) / 0x34;
    return (float*)(o + at);
}

inline V mpos(const float* m) { return {m[10], m[11], m[12]}; }

uint8_t* tag_data(uint32_t tag) {
    uint8_t* hdr = *(uint8_t**)(g_h1 + RVA_TAGS);
    if (!hdr || tag == 0xFFFFFFFFu) return nullptr;
    uint8_t* arr = hdr + (*(uint32_t*)hdr - TAG_BASE);
    if ((int)(tag & 0xFFFF) >= *(int32_t*)(hdr + 0xC)) return nullptr;
    uint8_t* e = arr + (tag & 0xFFFF) * 0x20;
    if (*(uint32_t*)(e + 0xC) != tag) return nullptr;
    return hdr + (*(uint32_t*)(e + 0x14) - TAG_BASE);
}

const Skeleton* skeleton(uint32_t tag, int nodes) {
    for (Skeleton& s : g_skel)
        if (s.tag == tag) return s.ok && s.nodes == nodes ? &s : nullptr;
    Skeleton* s = nullptr;
    for (Skeleton& k : g_skel) if (!k.tag) { s = &k; break; }
    if (!s) return nullptr;
    memset(s, 0, sizeof *s);
    s->tag = tag;
    uint8_t* biped = tag_data(tag);
    uint8_t* model = biped ? tag_data(*(uint32_t*)(biped + 0x28 + 12)) : nullptr;
    if (!model) return nullptr;
    int count = *(int32_t*)(model + 0xB8);
    if (count != nodes || count > MAX_NODES || count < 1) return nullptr;
    uint8_t* hdr = *(uint8_t**)(g_h1 + RVA_TAGS);
    uint8_t* node = hdr + (*(uint32_t*)(model + 0xBC) - TAG_BASE);
    for (int p = 0; p < NODE_PARTICLES; p++) s->particle_node[p] = -1;
    for (int i = 0; i < count; i++) {
        const char* name = (const char*)(node + i * 0x9C);
        s->body[i] = -1;
        for (int p = 0; p < NODE_PARTICLES; p++)
            if (!_strnicmp(name, PARTICLE_NODE[p], 32)) s->particle_node[p] = (int8_t)i;
        for (const NodeBody& nb : NODE_BODY)
            if (!_strnicmp(name, nb.name, 32)) s->body[i] = (int8_t)nb.body;
    }
    for (int p = 0; p < NODE_PARTICLES; p++) if (s->particle_node[p] < 0) return nullptr;
    for (int i = 0; i < count; i++) {               // the rest turn with their nearest named parent (the torso at the top)
        int k = i, guard = 0;
        while (s->body[k] < 0 && guard++ < MAX_NODES) {
            int parent = *(int16_t*)(node + k * 0x9C + 0x24);
            if (parent < 0 || parent >= count) break;
            k = parent;
        }
        s->body[i] = s->body[k] >= 0 ? s->body[k] : (int8_t)G_TORSO;
    }
    s->nodes = count;
    s->ok = true;
    logf("ce ragdolls: skeleton of biped tag %08x matched (%d nodes)", tag, count);
    return s;
}

// a body's turn from its death pose: torso by shape matching (Mueller et al. 2016's rotation extraction, warm started)
void torso_match(Rag& r) {
    V c{0, 0, 0}, c0{0, 0, 0};
    for (int i : TORSO_SET) { c = c + r.x[i]; c0 = c0 + r.x0[i]; }
    c = c * (1.0f / NT); c0 = c0 * (1.0f / NT);
    V A[3] = {{0, 0, 0}, {0, 0, 0}, {0, 0, 0}};     // columns of sum (x - c)(x0 - c0)^T
    for (int i : TORSO_SET) {
        V p = r.x[i] - c, q = r.x0[i] - c0;
        A[0] = A[0] + p * q.x; A[1] = A[1] + p * q.y; A[2] = A[2] + p * q.z;
    }
    Q q = r.q[G_TORSO];
    for (int it = 0; it < 6; it++) {
        V R[3] = {qrot(q, {1, 0, 0}), qrot(q, {0, 1, 0}), qrot(q, {0, 0, 1})};
        V w = (cross(R[0], A[0]) + cross(R[1], A[1]) + cross(R[2], A[2])) *
              (1.0f / (fabsf(dot(R[0], A[0]) + dot(R[1], A[1]) + dot(R[2], A[2])) + 1e-9f));
        float a = len(w);
        if (a < 1e-7f) break;
        q = qnorm(qmul(qaxis(w * (1.0f / a), a), q));
    }
    r.q[G_TORSO] = q;
    for (int i : TORSO_SET) r.x[i] = c + qrot(q, r.x0[i] - c0);
}

void bone_turns(Rag& r) {
    for (int g = 1; g < NG; g++) {
        const Bone& b = BONE[g];
        V f = qrot(r.q[b.parent], norm(r.x0[b.b] - r.x0[b.a]));
        r.q[g] = qnorm(qmul(qswing(f, norm(r.x[b.b] - r.x[b.a], f)), r.q[b.parent]));
    }
}

void keep_length(Rag& r, int a, int b, float rest, float wa, float wb) {
    V d = r.x[b] - r.x[a];
    float l = len(d);
    if (l < 1e-6f) return;
    V corr = d * ((l - rest) / (l * (wa + wb)));
    r.x[a] = r.x[a] + corr * wa;
    r.x[b] = r.x[b] - corr * wb;
}

void limit_cone(Rag& r, int k) {
    const Bone& b = BONE[CONE[k].body];
    V axis = qrot(r.q[G_TORSO], r.cone_axis[k]);
    V d = r.x[b.b] - r.x[b.a];
    float l = len(d);
    if (l < 1e-6f) return;
    V u = d * (1.0f / l);
    float c = dot(u, axis);
    if (c >= r.cone_cos[k]) return;
    V perp = norm(u - axis * c, norm(cross(axis, fabsf(axis.x) < 0.9f ? V{1, 0, 0} : V{0, 1, 0})));
    float s = sqrtf(1 - r.cone_cos[k] * r.cone_cos[k]);
    r.x[b.b] = r.x[b.a] + (axis * r.cone_cos[k] + perp * s) * l;
}

void limit_hinge(Rag& r, int k) {
    const Bone& b = BONE[HINGE[k].body];
    const Bone& p = BONE[b.parent];
    V t = norm(r.x[p.b] - r.x[p.a]);
    // the parent bone's turn now (bone_turns runs after the solve: the swing of its own bone from its parent's)
    Q qp = qmul(qswing(qrot(r.q[p.parent], norm(r.x0[p.b] - r.x0[p.a])), t), r.q[p.parent]);
    V a = qrot(qp, r.hinge_axis[k]);
    a = norm(a - t * dot(a, t), norm(cross(t, fabsf(t.x) < 0.9f ? V{1, 0, 0} : V{0, 1, 0})));
    V c = r.x[b.b] - r.x[b.a];
    float l = len(c);
    if (l < 1e-6f) return;
    V cp = c - a * dot(c, a);
    if (len(cp) < 1e-6f) cp = t;
    float th = atan2f(dot(a, cross(t, cp)), dot(t, cp));
    th = clampf(th, r.hinge_lo[k], r.hinge_hi[k]);
    V dir = t * cosf(th) + cross(a, t) * sinf(th);
    r.x[b.b] = r.x[b.a] + dir * l;
}

// node matrices from the bodies' turns, joint by joint out from the torso (forward kinematics): a joint sits where its
// parent body puts it, at the skeleton's own length, so the solver's leftover error bends a limb a little but never
// stretches it (placed at the particles, limbs drew up to 40% long mid-fall, live Nov 13)
void pose(Rag& r) {
    V c{0, 0, 0};
    for (int i : TORSO_SET) c = c + r.x[i];
    c = c * (1.0f / NT);
    V root[NG];
    for (int g = 1; g < NG; g++) {
        const Bone& b = BONE[g];
        root[g] = b.parent == G_TORSO ? c + qrot(r.q[G_TORSO], r.x0[b.a] - r.c0)
                                      : root[b.parent] + qrot(r.q[b.parent], r.x0[b.a] - r.x0[BONE[b.parent].a]);
    }
    for (int n = 0; n < r.nodes; n++) {
        int g = r.sk->body[n];
        const float* m0 = r.m0[n];
        float* m = r.out[n];
        Q q = r.q[g];
        V p0 = mpos(m0);
        V p = g == G_TORSO ? c + qrot(q, p0 - r.c0) : root[g] + qrot(q, p0 - r.x0[BONE[g].a]);
        V f = qrot(q, {m0[1], m0[2], m0[3]}), l = qrot(q, {m0[4], m0[5], m0[6]}), u = qrot(q, {m0[7], m0[8], m0[9]});
        m[0] = m0[0];
        m[1] = f.x; m[2] = f.y; m[3] = f.z;
        m[4] = l.x; m[5] = l.y; m[6] = l.z;
        m[7] = u.x; m[8] = u.y; m[9] = u.z;
        m[10] = p.x; m[11] = p.y; m[12] = p.z;
    }
}

void write_pose(Rag& r, uint8_t* o) {
    int n = 0;
    float* m = matrices(o, &n);
    if (m && n == r.nodes) memcpy(m, r.out, sizeof(float) * 13 * n);
}

// one tick of a body: follow the corpse object across the floor, then SUB substeps of gravity and ITER solver passes
void step(Rag& r, uint8_t* o) {
    V obj = *(V*)(o + 0x18);
    V d = obj - r.obj;
    r.obj = obj;
    V follow{d.x, d.y, d.z > 0 ? d.z : 0};           // (down: the body falls by itself)
    if (len(d) > 0.002f) r.still = 0;
    if (len(follow) > 0) for (int i = 0; i < NP; i++) { r.x[i] = r.x[i] + follow; r.xp[i] = r.xp[i] + follow; }
    if (r.still > 20) return;                           // asleep: nothing moves it but the corpse itself
    float floor_z = obj.z;
    float moved = 0;
    for (int s = 0; s < SUB; s++) {
        for (int i = 0; i < NP; i++) {
            V v = (r.x[i] - r.xp[i]) * 0.985f;
            r.xp[i] = r.x[i];
            r.x[i] = r.x[i] + v + V{0, 0, -G_SUB};
        }
        for (int it = 0; it < ITER; it++) {
            for (int g = 1; g < NG; g++)
                keep_length(r, BONE[g].a, BONE[g].b, r.bone_len[g], BONE[g].parent == G_TORSO ? 0.35f : 0.5f, 1.0f);
            for (int k = 0; k < NC; k++) limit_cone(r, k);
            for (int k = 0; k < NH; k++) limit_hinge(r, k);
            torso_match(r);
            for (int i = 0; i < NP; i++) {
                float z = floor_z + RADIUS[i];
                if (r.x[i].z < z) {
                    r.x[i].z = z;
                    r.xp[i].x += (r.x[i].x - r.xp[i].x) * 0.35f;   // floor friction
                    r.xp[i].y += (r.x[i].y - r.xp[i].y) * 0.35f;
                }
            }
        }
        for (int i = 0; i < NP; i++) { float m = len(r.x[i] - r.xp[i]); if (m > moved) moved = m; }
    }
    bone_turns(r);
    if (moved < 0.0006f) { if (++r.still > 20) for (int i = 0; i < NP; i++) r.xp[i] = r.x[i]; }
    else r.still = 0;
    pose(r);
}

Rag* rag_of(uint32_t handle) {
    for (Rag& r : g_rag) if (r.used && r.handle == handle) return &r;
    return nullptr;
}

void start(uint32_t handle, uint8_t* o, const Skeleton* sk, float* m, int nodes, const Cache* prev) {
    Rag* r = nullptr;
    for (Rag& k : g_rag) if (!k.used) { r = &k; break; }
    if (!r) { r = &g_rag[0]; for (Rag& k : g_rag) if (k.age < r->age) r = &k; }   // all busy: the oldest body goes still
    memset(r, 0, sizeof *r);
    r->handle = handle; r->used = true; r->age = g_tick; r->sk = sk; r->nodes = nodes;
    memcpy(r->m0, m, sizeof(float) * 13 * nodes);
    r->obj = *(V*)(o + 0x18);
    V vel[NP];
    for (int p = 0; p < NODE_PARTICLES; p++) {
        r->x[p] = mpos(m + 13 * sk->particle_node[p]);
        vel[p] = prev ? (r->x[p] - prev->p[p]) - (r->obj - prev->obj) : V{0, 0, 0};   // (the corpse's own slide: followed)
        if (len(vel[p]) > 0.1f) vel[p] = norm(vel[p]) * 0.1f;
    }
    const float* hm = m + 13 * sk->particle_node[P_HEAD];
    r->x[P_HEAD] = r->x[P_HEAD] + norm(V{hm[1], hm[2], hm[3]}) * 0.05f;   // (the head bone points out of its top)
    V up = norm(r->x[P_NECK] - r->x[P_PELVIS]);
    V left = norm(r->x[P_LSH] - r->x[P_RSH]);
    left = norm(left - up * dot(left, up), V{0, 1, 0});
    V fwd = cross(left, up);
    r->x[P_BELLY] = r->x[P_CHEST] + fwd * 0.06f;
    vel[P_BELLY] = vel[P_CHEST];
    for (int i = 0; i < NP; i++) r->x0[i] = r->x[i];
    for (int g = 0; g < NG; g++) r->q[g] = Q{1, 0, 0, 0};
    for (int g = 1; g < NG; g++) r->bone_len[g] = len(r->x[BONE[g].b] - r->x[BONE[g].a]);
    V c0{0, 0, 0};
    for (int i : TORSO_SET) c0 = c0 + r->x0[i];
    r->c0 = c0 * (1.0f / NT);
    for (int k = 0; k < NC; k++) {
        const Bone& b = BONE[CONE[k].body];
        V axis = norm(fwd * CONE[k].fwd + left * CONE[k].left + up * CONE[k].up);
        float at_death = acosf(clampf(dot(norm(r->x[b.b] - r->x[b.a]), axis), -1, 1));
        float half = CONE[k].half * DEG;
        if (at_death + 5 * DEG > half) half = at_death + 5 * DEG;
        r->cone_axis[k] = axis;
        r->cone_cos[k] = cosf(half > 3.1f ? 3.1f : half);
    }
    for (int k = 0; k < NH; k++) {
        const Bone& b = BONE[HINGE[k].body];
        const Bone& p = BONE[b.parent];
        V t = norm(r->x[p.b] - r->x[p.a]), c = norm(r->x[b.b] - r->x[b.a]);
        V axis = cross(t, c);
        float bent = 0;
        if (len(axis) > 0.05f) { axis = norm(axis); bent = acosf(clampf(dot(t, c), -1, 1)); }
        else axis = HINGE[k].knee ? left : left * -1.0f;   // straight: knees fold backward, elbows forward
        r->hinge_axis[k] = axis;
        r->hinge_lo[k] = HINGE[k].lo * DEG;
        r->hinge_hi[k] = HINGE[k].hi * DEG > bent + 5 * DEG ? HINGE[k].hi * DEG : bent + 5 * DEG;
    }
    // the push (Halo 2: min(0.7, the biped's) x (1.5 + 1.75 r) world units a second, along the hit, bodies higher up
    // pushed harder so the body topples, an upward part 0.75 + 0.75 r): along the death animation's own first motion
    // (picked from the hit's side), else the corpse's slide, else backward
    V dir = (vel[P_CHEST] + vel[P_NECK] + vel[P_HEAD]) * (1.0f / 3);
    dir.z = 0;
    if (len(dir) < 0.003f) { V s = *(V*)(o + 0x24); dir = V{s.x, s.y, 0}; }
    dir = len(dir) < 0.003f ? fwd * -1.0f : norm(dir);
    // Halo 2's numbers are an impulse on Havok bodies of mass 200; as plain velocities they threw bodies head over
    // heels (live, Nov 13). Scaled by PUSH_SCALE, and the upward part even over the body (a pop, not a flip)
    float strength = PUSH_SCALE * 0.7f * (1.5f + 1.75f * rnd()) / 30.0f;   // (a tick)
    V pop{0, 0, PUSH_SCALE * (0.75f + 0.75f * rnd()) / 30.0f};
    float zlo = 1e9f, zhi = -1e9f;
    for (int i = 0; i < NP; i++) { if (r->x[i].z < zlo) zlo = r->x[i].z; if (r->x[i].z > zhi) zhi = r->x[i].z; }
    for (int i = 0; i < NP; i++) {
        float h = (r->x[i].z - zlo) / (zhi - zlo + 1e-4f);
        V v = vel[i] + dir * (strength * (0.35f + 0.65f * h)) + pop;
        r->xp[i] = r->x[i] - v * (1.0f / SUB);
    }
    pose(*r);
}

void __fastcall nodes_hook(uint64_t handle) {
    g_nodes_orig(handle);
    __try {
        int type = -1;
        uint8_t* o = object_of((uint32_t)handle, &type);
        if (!o || type != 0) return;
        if (Rag* r = rag_of((uint32_t)handle)) { write_pose(*r, o); return; }
        int nodes = 0;
        float* m = matrices(o, &nodes);
        if (!m || nodes > MAX_NODES) return;
        const Skeleton* sk = skeleton(*(uint32_t*)o, nodes);
        if (!sk) return;
        Cache& c = g_cache[handle & (CACHE - 1)];
        if (c.handle != (uint32_t)handle) { c.handle = (uint32_t)handle; c.dead_ticks = -1; }
        bool dead = (*(uint32_t*)(o + 0x10) & F_DEAD) != 0;
        if (dead && c.dead_ticks >= 0 && ++c.dead_ticks >= START_TICKS     // (dead_ticks -1: never seen alive)
            && *(int32_t*)(g_h1 + RVA_VARIANT + 0x30) > 0) {                 // multiplayer only (see RVA_VARIANT)
            start((uint32_t)handle, o, sk, m, nodes, &c);
            c.handle = 0;
            return;
        }
        if (!dead) c.dead_ticks = 0;
        c.obj = *(V*)(o + 0x18);
        for (int p = 0; p < NODE_PARTICLES; p++) c.p[p] = mpos(m + 13 * sk->particle_node[p]);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
    }
}

}  // namespace

// botcore's tick hook (start of each Halo CE tick): step every body, write its pose (a corpse at rest keeps it)
void ce_ragdoll_tick() {
    if (!g_nodes_orig) return;
    g_tick++;
    __try {
        for (Rag& r : g_rag) {
            if (!r.used) continue;
            int type = -1;
            uint8_t* o = object_of(r.handle, &type);
            int nodes = 0;
            if (!o || type != 0 || !matrices(o, &nodes) || nodes != r.nodes) { r.used = false; continue; }
            step(r, o);
            write_pose(r, o);
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        for (Rag& r : g_rag) r.used = false;
    }
}

// installed with botcore's other halo1 hooks (enabled by their MH_EnableHook(MH_ALL_HOOKS)); false: left off
bool ce_ragdoll_install(uint8_t* h1) {
    if (g_h1) MH_RemoveHook(g_h1 + RVA_NODE_MATRICES);
    g_nodes_orig = nullptr;
    for (Rag& r : g_rag) r.used = false;
    memset(g_cache, 0, sizeof g_cache);
    memset(g_skel, 0, sizeof g_skel);
    g_h1 = h1;
    if (memcmp(h1 + RVA_NODE_MATRICES, PROLOGUE, sizeof PROLOGUE)) {
        logf("ce ragdolls: not the MCC 1.3528 build decoded: off");
        return false;
    }
    if (MH_CreateHook(h1 + RVA_NODE_MATRICES, (void*)&nodes_hook, (void**)&g_nodes_orig) != MH_OK) {
        g_nodes_orig = nullptr;
        logf("ce ragdolls: hook failed");
        return false;
    }
    return true;
}
