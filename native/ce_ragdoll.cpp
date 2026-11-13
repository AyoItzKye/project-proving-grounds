// ce_ragdoll.cpp: Halo 2 style ragdolls for Halo CE (halo1.dll, MCC 1.3528). Halo CE has no ragdolls: a dead biped
// plays a canned death animation and freezes. Halo 2 (halo2.dll FUN_18092ab00 and friends, decoded Nov 13; ghidra/rag)
// turns a dead biped into 10 Havok rigid bodies (pelvis-torso, head, upper arms, forearms, thighs, calves) joined by
// ragdoll constraints (cone, plane and twist limits) at the hips, shoulders and neck and limited hinges at the knees
// and elbows, keeps the body's motion, pushes it along the killing hit, collides it with the world and writes the
// bodies' poses into the biped's node matrices every tick.
//
// Halo CE here, the same plan in a rigid-body solver of its own (extended position based dynamics, Mueller et al. 2020:
// substeps, position-level joint, limit and contact constraints, velocities from the corrected positions):
// - Node matrices: biped object + [u16 +0x1AE] (size +0x1AC), one 0x34-byte matrix per node (scale, forward, left, up,
//   position; world space); the renderer skins from them. FUN_180b3a614(object handle) rebuilds an object's matrices
//   each tick (found with a hardware write watch): hooked, a ragdolled body's pose replaces the death animation's.
//   ce_ragdoll_tick (botcore's CE tick hook, the start of each tick) steps every body and writes its pose too: a
//   corpse at rest (+0x10 bit 0x800000) is no longer rebuilt by the game, so that write stays.
// - Death: +0x10 bit 0x10000 (the tick the biped dies). The bodies start 3 ticks later from the death animation's pose
//   and its motion (each body's linear and angular velocity from its node over the last tick, so a running body or
//   one thrown by an explosion keeps going), plus a push in the direction of that motion (Halo 2's strengths x 0.3).
// - Joints: Halo 2's: ball joints (swing within a cone, twist about the bone) at the hips, shoulders and neck, hinges at
//   the knees and elbows. Halo 2's own frames do not fit CE's nodes (CE's live animations sat 18-28 deg off their twist
//   zero), so the limits come from CE's own animations: 42,181 live poses of 15 bots (logs/tmp/ragdoll/fit_limits.py),
//   each joint's swing ellipse, hinge range and twist range at the 0.5 / 99.5 percentiles plus 5 deg. A body never
//   bends further than a living Spartan does. Twist stays within Halo 2's widths (5 to 7.5 deg, the head 20) of the
//   twist it died with. A pose outside a limit at death is let back inside over half a second (no snap).
// - World: halo1's collision_test_vector (FUN_180b913fc, found from the readers of the BSP's root node) against the
//   structure, each tick, from every collision sphere along its motion and down; contact planes kept for the tick's
//   substeps. Friction (static and sliding), no bounce. Gravity 1.4 x CE's (bodies looked weightless at 1x).
//   Parts collide with each other too (every sphere pair but joint neighbours and pairs touching at death).
// - Rest: a body whose every part moves under 0.06 u/s for 10 ticks stops (exact pose kept); parts on the ground roll
//   against resistance; one only drifting (under 0.3 u/s) after 6 s, or any after 15 s, stops too. A kick to its
//   corpse object from the game (a grenade: the corpse's speed jumps) wakes it with that kick.
// - The corpse object is moved under the body each tick (object_set_position, FUN_180b359e8): the game culls a body
//   by its object (a 0.42 u sphere, the map area it is filed in), and bodies 1-6 u from it vanished mid-air and as
//   they settled (live, Nov 13).
// Skeletons are matched by node name (the cyborg's 19 bip01 nodes); other bipeds never. Multiplayer games only.
#include <windows.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "third_party/minhook/include/MinHook.h"

void logf(const char* fmt, ...);

namespace {

const uintptr_t RVA_NODE_MATRICES = 0xB3A614;       // void (object handle)
const uintptr_t RVA_OBJECT_UPDATE = 0xB3A06C;       // bool (object handle): one object's whole update each tick (FUN_180b3a06c)
const uintptr_t RVA_SNAPSHOT = 0xB3AF10;            // void (object handle): copies the nodes for the renderer (FUN_180b3af10)
const uintptr_t RVA_COLLISION_TEST = 0xB913FC;      // bool (flags, point*, vector*, ignore object, result*)
const uintptr_t RVA_GC_VETO = 0xB394F8;            // bool (object handle): the garbage collector's veto, true = keep it
const uintptr_t RVA_PLAYERS = 0x1C40480;           // the players array's header pointer
const uintptr_t RVA_SET_POSITION = 0xB359E8;        // object_set_position (handle, position*, forward*, up*)
const uintptr_t RVA_OBJECT_HEADERS = 0x1C42248, RVA_OBJECT_POOL = 0x2D9CDF8, RVA_TAGS = 0x2D9CE10;
// the running game variant, +0x30 its engine (1 CTF, 2 Slayer ...): multiplayer only (campaign's Marines and Elites
// and its Anniversary graphics were never tried; Tab does nothing in a multiplayer game: classic graphics only)
const uintptr_t RVA_VARIANT = 0x2E9F770;
const uint32_t TAG_BASE = 0x50000000;
const uint8_t SNAPSHOT_PROLOGUE[16] = {0x48, 0x8B, 0xC4, 0x48, 0x89, 0x58, 0x08, 0x48, 0x89, 0x68, 0x10, 0x48, 0x89, 0x70, 0x18, 0x48};
const uint8_t UPDATE_PROLOGUE[16] = {0x48, 0x89, 0x5C, 0x24, 0x10, 0x48, 0x89, 0x6C, 0x24, 0x18, 0x48, 0x89, 0x74, 0x24, 0x20, 0x57};
const uint8_t NODES_PROLOGUE[24] = {0x48, 0x8B, 0xC4, 0x48, 0x89, 0x58, 0x10, 0x48, 0x89, 0x70, 0x18, 0x48, 0x89,
                                    0x78, 0x20, 0x55, 0x41, 0x54, 0x41, 0x55, 0x41, 0x56, 0x41, 0x57};
const uint8_t GC_VETO_PROLOGUE[16] = {0x48, 0x8B, 0xC4, 0x48, 0x89, 0x58, 0x08, 0x48, 0x89, 0x70, 0x18, 0x48, 0x89, 0x78, 0x20, 0x55};
const uint8_t SET_POSITION_PROLOGUE[16] = {0x48, 0x8B, 0xC4, 0x48, 0x89, 0x58, 0x08, 0x48, 0x89, 0x68, 0x10, 0x48, 0x89,
                                          0x70, 0x18, 0x48};
const uint8_t COLLISION_PROLOGUE[16] = {0x48, 0x8B, 0xC4, 0x48, 0x89, 0x58, 0x20, 0x55, 0x56, 0x57, 0x41, 0x54, 0x41,
                                        0x55, 0x41, 0x56};
// collision_test_vector flags: bits 0/1 front / back facing (neither: both), 3 ignore invisible, 5 structure, 6 media,
// 7 objects. Result: +0 hit type (-1 none), +0x14 fraction, +0x18 point, +0x24 plane (normal, d)
const uint64_t COLLIDE_FLAGS = 0x20 | 0x08;
const uint32_t F_DEAD = 0x10000;
const int START_TICKS = 3, MAX_NODES = 64, SLOTS = 24, AWAKE_MAX = 8, CACHE = 2048, RELAX_TICKS = 15;
const int SUB = 10;                                  // substeps a tick (1/300 s)
const float TICK = 1.0f / 30.0f, H = TICK / SUB;
const float GRAVITY_BASE = 1.547f * 3.22f;             // the baseline: 1.547 x CE's (32.2 ft/s^2 in world units of 10 ft); the launcher's slider scales it
float GRAVITY = GRAVITY_BASE;                  // world units (10 ft) a second squared
const float PUSH_SCALE = 0.3f;                       // Halo 2's push strengths, scaled (set by eye, live)
const float MU_STATIC = 0.83f, MU_SLIDE = 0.83f, JOINT_DAMP = 5.0f, SPIN_DAMP = 0.3f, ROLL_DAMP = 8.0f;
// Limb inertia: a body blown through the air
// kept the pose it died in until it hit something (every part had the same velocity). Real limbs trail: the air drags light
// parts harder than the torso (drag acceleration k |v| v, k per body, airborne parts only), an explosion's kick (the corpse
// object's speed jumping) goes into the torso first and reaches the limbs through the joints (LIMB_KICK of it directly),
// and a body that starts out flying (an explosion killed it in the air) starts with its limbs lagging behind the torso.
const float BODY_DRAG[10] = {0.03f, 0.10f, 0.22f, 0.30f, 0.22f, 0.30f, 0.16f, 0.24f, 0.16f, 0.24f};   // torso, head, arms, legs
const float BODY_LAG[10] = {0.0f, 0.5f, 0.7f, 1.0f, 0.7f, 1.0f, 0.6f, 1.0f, 0.6f, 1.0f};              // share of the start lag
const float LIMB_KICK = 0.45f, LIMB_LAG_MAX = 0.7f, LIMB_LAG_FROM = 1.5f, LIMB_LAG_FULL = 7.5f;
const float REST_SPEED = 0.06f;                     // u/s: every part slower for 10 ticks = at rest
const float CREEP_SPEED = 0.9f;                     // u/s: a limb slower than this beside a still torso is creeping, not falling
const int CORE_TICKS = 8;
const float DEG = 3.14159265f / 180.0f;

struct V { float x, y, z; };
inline V operator+(V a, V b) { return {a.x + b.x, a.y + b.y, a.z + b.z}; }
inline V operator-(V a, V b) { return {a.x - b.x, a.y - b.y, a.z - b.z}; }
inline V operator*(V a, float s) { return {a.x * s, a.y * s, a.z * s}; }
inline V operator-(V a) { return {-a.x, -a.y, -a.z}; }
inline float dot(V a, V b) { return a.x * b.x + a.y * b.y + a.z * b.z; }
inline V cross(V a, V b) { return {a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x}; }
inline float len(V a) { return sqrtf(dot(a, a)); }
inline V norm(V a, V fallback = {0, 0, 1}) { float l = len(a); return l > 1e-9f ? a * (1.0f / l) : fallback; }
inline float clampf(float v, float lo, float hi) { return v < lo ? lo : v > hi ? hi : v; }
inline V any_perp(V a) { return norm(cross(a, fabsf(a.x) < 0.9f ? V{1, 0, 0} : V{0, 1, 0})); }

struct Q { float w, x, y, z; };
inline Q qmul(Q a, Q b) {
    return {a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z, a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
            a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x, a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w};
}
inline Q qconj(Q q) { return {q.w, -q.x, -q.y, -q.z}; }
inline Q qnorm(Q q) {
    float l = sqrtf(q.w * q.w + q.x * q.x + q.y * q.y + q.z * q.z);
    return l > 1e-12f ? Q{q.w / l, q.x / l, q.y / l, q.z / l} : Q{1, 0, 0, 0};
}
inline V qrot(Q q, V v) { V u{q.x, q.y, q.z}; V t = cross(u, v) * 2.0f; return v + t * q.w + cross(u, t); }
// q turned by the small rotation vector w (world): q + 0.5 [w, 0] q
inline Q qturn(Q q, V w) {
    Q d = qmul(Q{0, w.x, w.y, w.z}, q);
    return qnorm(Q{q.w + 0.5f * d.w, q.x + 0.5f * d.x, q.y + 0.5f * d.y, q.z + 0.5f * d.z});
}
Q qfrom_axes(V f, V l, V u) {                       // rotation whose columns are f, l, u
    float tr = f.x + l.y + u.z;
    Q q;
    if (tr > 0) { float s = sqrtf(tr + 1) * 2; q = {0.25f * s, (l.z - u.y) / s, (u.x - f.z) / s, (f.y - l.x) / s}; }
    else if (f.x > l.y && f.x > u.z) { float s = sqrtf(1 + f.x - l.y - u.z) * 2; q = {(l.z - u.y) / s, 0.25f * s, (l.x + f.y) / s, (u.x + f.z) / s}; }
    else if (l.y > u.z) { float s = sqrtf(1 + l.y - f.x - u.z) * 2; q = {(u.x - f.z) / s, (l.x + f.y) / s, 0.25f * s, (u.y + l.z) / s}; }
    else { float s = sqrtf(1 + u.z - f.x - l.y) * 2; q = {(f.y - l.x) / s, (u.x + f.z) / s, (u.y + l.z) / s, 0.25f * s}; }
    return qnorm(q);
}
// a body's turn rate from its orientation a tick ago and now
V spin(Q prev, Q now, float dt) {
    Q d = qmul(now, qconj(prev));
    V w{d.x, d.y, d.z};
    return (d.w < 0 ? -w : w) * (2.0f / dt);
}

// --- the cyborg's nodes by name
enum { N_PELVIS, N_SPINE, N_SPINE1, N_NECK, N_LCLAV, N_RCLAV, N_HEAD, N_LUA, N_RUA, N_LFA, N_RFA, N_LHAND, N_RHAND,
       N_LTH, N_RTH, N_LCA, N_RCA, N_LFOOT, N_RFOOT, NN };
const char* const NODE_NAME[NN] = {
    "bip01 pelvis", "bip01 spine", "bip01 spine1", "bip01 neck", "bip01 l clavicle", "bip01 r clavicle", "bip01 head",
    "bip01 l upperarm", "bip01 r upperarm", "bip01 l forearm", "bip01 r forearm", "bip01 l hand", "bip01 r hand",
    "bip01 l thigh", "bip01 r thigh", "bip01 l calf", "bip01 r calf", "bip01 l foot", "bip01 r foot"};

// --- Halo 2's 10 bodies: the node whose frame each takes, its share of the mass, the nodes it carries
enum { B_TORSO, B_HEAD, B_LUA, B_LFA, B_RUA, B_RFA, B_LTH, B_LCA, B_RTH, B_RCA, NB };
const int BODY_NODE[NB] = {N_PELVIS, N_HEAD, N_LUA, N_LFA, N_RUA, N_RFA, N_LTH, N_LCA, N_RTH, N_RCA};
const float BODY_MASS[NB] = {0.46f, 0.07f, 0.03f, 0.025f, 0.03f, 0.025f, 0.12f, 0.06f, 0.12f, 0.06f};
const int NODE_BODY[NN] = {B_TORSO, B_TORSO, B_TORSO, B_TORSO, B_TORSO, B_TORSO, B_HEAD, B_LUA, B_RUA, B_LFA, B_RFA,
                           B_LFA, B_RFA, B_LTH, B_RTH, B_LCA, B_RCA, B_LCA, B_RCA};

// --- joints: ball joints (swing ellipse about a centre, twist), hinges (about the parent's z axis). Limits measured
// from CE's own animations (fit_limits.py; parent-node frame, degrees); Halo 2's twist widths about the death twist
struct Ball { int ref; float c[3], e1[3], y0[3], s1lo, s1hi, s2lo, s2hi, twist; };
struct Hinge { float lo, hi; };
struct Joint { int parent, child; bool hinge; int index; };
const Ball BALL[] = {
    {N_PELVIS, {-0.7300f, 0.6697f, 0.1363f}, {-0.5064f, -0.6639f, 0.5503f}, {0.6483f, 0.7417f, -0.1721f}, -37.8f, 38.0f, -35.7f, 34.2f, 5.0f},    // hip l
    {N_PELVIS, {-0.8979f, 0.4309f, -0.0899f}, {0.4362f, 0.8984f, -0.0509f}, {0.4004f, 0.7147f, -0.5735f}, -43.6f, 61.3f, -30.3f, 31.8f, 5.0f},   // hip r
    {N_LCLAV, {0.1830f, -0.5642f, -0.8051f}, {-0.1409f, -0.8255f, 0.5465f}, {0.3956f, 0.7920f, -0.4651f}, -65.3f, 92.6f, -82.5f, 32.5f, 7.5f},   // shoulder l
    {N_RCLAV, {-0.2032f, -0.9169f, 0.3435f}, {-0.7566f, -0.0756f, -0.6495f}, {0.8167f, 0.0347f, 0.5759f}, -98.6f, 48.8f, -67.6f, 57.1f, 7.5f},  // shoulder r
    {N_NECK, {0.9742f, -0.0799f, 0.2111f}, {0.0913f, 0.9948f, -0.0446f}, {-0.0966f, 0.6977f, 0.7098f}, -25.1f, 47.6f, -29.8f, 26.6f, 20.0f}};    // head
const Hinge HINGE[] = {{-121.8f, -12.8f}, {-121.7f, -17.1f}, {-133.5f, -7.4f}, {-123.9f, -33.0f}};   // knee l, r, elbow l, r
const Joint JOINT[] = {{B_TORSO, B_LTH, false, 0}, {B_TORSO, B_RTH, false, 1}, {B_LTH, B_LCA, true, 0},
                       {B_RTH, B_RCA, true, 1}, {B_TORSO, B_LUA, false, 2}, {B_TORSO, B_RUA, false, 3},
                       {B_LUA, B_LFA, true, 2}, {B_RUA, B_RFA, true, 3}, {B_TORSO, B_HEAD, false, 4}};
const int NJ = sizeof JOINT / sizeof JOINT[0];

// --- collision spheres, made at death from node positions: (body, from node, toward node or -1, how far, radius);
// toward -1 with a distance: along the node's own forward axis
struct SphereDef { int body, node, toward; float t, r; };
const SphereDef SPHERE[] = {
    {B_TORSO, N_PELVIS, -1, 0, 0.065f}, {B_TORSO, N_SPINE1, -1, 0, 0.075f}, {B_TORSO, N_NECK, -1, 0, 0.05f},
    {B_TORSO, N_LUA, -1, 0, 0.045f}, {B_TORSO, N_RUA, -1, 0, 0.045f}, {B_HEAD, N_HEAD, -1, 0.05f, 0.055f},
    {B_LUA, N_LUA, N_LFA, 0.3f, 0.03f}, {B_LUA, N_LUA, N_LFA, 0.85f, 0.03f},
    {B_LFA, N_LFA, N_LHAND, 0.35f, 0.028f}, {B_LFA, N_LHAND, -1, 0.04f, 0.03f},
    {B_RUA, N_RUA, N_RFA, 0.3f, 0.03f}, {B_RUA, N_RUA, N_RFA, 0.85f, 0.03f},
    {B_RFA, N_RFA, N_RHAND, 0.35f, 0.028f}, {B_RFA, N_RHAND, -1, 0.04f, 0.03f},
    {B_LTH, N_LTH, N_LCA, 0.35f, 0.045f}, {B_LTH, N_LTH, N_LCA, 0.9f, 0.04f},
    {B_LCA, N_LCA, N_LFOOT, 0.5f, 0.035f}, {B_LCA, N_LFOOT, -1, 0, 0.035f}, {B_LCA, N_LFOOT, -1, 0.07f, 0.03f},
    {B_RTH, N_RTH, N_RCA, 0.35f, 0.045f}, {B_RTH, N_RTH, N_RCA, 0.9f, 0.04f},
    {B_RCA, N_RCA, N_RFOOT, 0.5f, 0.035f}, {B_RCA, N_RFOOT, -1, 0, 0.035f}, {B_RCA, N_RFOOT, -1, 0.07f, 0.03f}};
const int NS = sizeof SPHERE / sizeof SPHERE[0];

struct Skeleton { uint32_t tag; bool ok; int nodes; int8_t node[NN]; int8_t body[MAX_NODES]; };
Skeleton g_skel[16];

struct Cache { uint32_t handle; int dead_ticks; float m[MAX_NODES][13]; int nodes; };
Cache g_cache[CACHE];

struct Body {
    V x, xp, v, w;                                   // centre of mass, at the substep's start, velocity, turn rate
    Q q, qp;
    float inv_m;
    float iinv[3][3];                                // inverse inertia, body frame
};
struct Contact { V p, n; bool on; };
struct Rag {
    uint32_t handle;
    bool used, awake;
    int still, age, moving, core;                          // moving: ticks since it started or a kick woke it
    uint32_t born;
    const Skeleton* sk;
    Body b[NB];
    V sphere[NS];                                    // body frame
    Contact contact[NS][2];
    V pivot_p[NJ], pivot_c[NJ];                      // joint pivot in the parent's / child's body frame
    Q ref_q[NJ];                                     // ball: the reference node's frame in the parent's body frame
    float twist0[NJ], slack0[NJ], hinge_lo0[NJ], hinge_hi0[NJ], axle0[NJ];
    V obj_v;                                         // the corpse object's last velocity (kicks)
    V psp[NS];                                       // the spheres' world positions a tick ago (the sudden-move diagnostic)
    bool have_psp;
    bool no_touch[NS][NS];                           // sphere pairs that never collide (joint neighbours, touching at death)
    int nodes;
    float local[MAX_NODES][13];                      // each node in its body's frame (scale, axes, position)
    float out[MAX_NODES][13];
};
Rag g_rag[SLOTS];
uint32_t g_tick, g_seed = 0x9E3779B9u;
uint8_t* g_h1;
typedef void(__fastcall* nodes_fn)(uint64_t handle);
typedef char(__fastcall* collide_fn)(uint64_t flags, float* point, float* vector, uint32_t ignore, void* result);
nodes_fn g_nodes_orig;
typedef uint64_t(__fastcall* update_fn)(uint64_t handle);
update_fn g_update_orig;
update_fn g_snapshot_orig;
collide_fn g_collide;
typedef void(__fastcall* set_position_fn)(uint64_t handle, float* position, float* forward, float* up);
set_position_fn g_set_position;

// the launcher's Settings card: "ce_ragdolls" in user\settings.json (two folders up from botcore's DLL; tools/settings.py),
// looked at every 2 s (its time stamp), so the switch changes a running game. No file or key: on. Off: no new bodies
// (the game's death animations); bodies already falling finish
wchar_t g_settings[MAX_PATH];
FILETIME g_settings_time;
bool g_enabled = true;
bool g_limb = true;                                  // limb inertia: part of the ragdolls (the tests turn it off to compare)
bool g_keep = true;                                  // "keep_bodies": dead bodies stay until their player dies again

// the flag "key": true / false in the settings text (a missing key: on)
bool flag_in(const char* text, const char* key, bool missing = true) {
    char quoted[40];
    sprintf_s(quoted, "\"%s\"", key);
    const char* k = strstr(text, quoted);
    if (!k) return missing;
    k = strchr(k + strlen(quoted), ':');
    if (!k) return missing;
    k++;
    while (*k == ' ' || *k == '\t' || *k == '\r' || *k == '\n') k++;
    return *k != 'f';
}

void read_settings() {
    WIN32_FILE_ATTRIBUTE_DATA a;
    if (!g_settings[0]) return;
    if (!GetFileAttributesExW(g_settings, GetFileExInfoStandard, &a)) {
        if (!g_enabled) logf("ce ragdolls: on (no settings file)");
        g_enabled = g_keep = true;
        g_settings_time = FILETIME{};
        return;
    }
    if (!CompareFileTime(&a.ftLastWriteTime, &g_settings_time)) return;
    HANDLE h = CreateFileW(g_settings, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, nullptr,
                           OPEN_EXISTING, 0, nullptr);
    if (h == INVALID_HANDLE_VALUE) return;           // (being replaced: next time)
    char buf[4096] = {};
    DWORD n = 0;
    BOOL ok = ReadFile(h, buf, sizeof buf - 1, &n, nullptr);
    CloseHandle(h);
    if (!ok) return;
    g_settings_time = a.ftLastWriteTime;
    bool on = flag_in(buf, "ce_ragdolls"), keep = flag_in(buf, "keep_bodies");
    if (on != g_enabled) logf("ce ragdolls: %s (user\\settings.json)", on ? "on" : "off");
    if (keep != g_keep) logf("ce keep bodies: %s (user\\settings.json)", keep ? "on" : "off");
    g_enabled = on;
    g_keep = keep;
    float mul = 1.0f;                                // "ragdoll_gravity": a multiple of the baseline (the launcher's slider, 0.5 to 1.5)
    if (const char* k = strstr(buf, "\"ragdoll_gravity\"")) {
        k = strchr(k + 17, ':');
        if (k) mul = clampf((float)atof(k + 1), 0.5f, 1.5f);
    }
    if (fabsf(mul * GRAVITY_BASE - GRAVITY) > 1e-4f) logf("ce ragdoll gravity: %.2f x the baseline", mul);
    GRAVITY = GRAVITY_BASE * mul;
}

// --- dead bodies stay until their player dies again (the garbage collector, FUN_180b3c818, deletes a dead biped once the
// object pool is under pressure unless this veto, FUN_180b394f8, says to keep it). A player's unit handle (player +0x64)
// is empty from the moment it dies, so each tick remembers the unit a player is in; when the unit goes and the biped it
// was is dead, that biped is the player's body, and the body before it is let go.
uint8_t* object_of(uint32_t handle, int* type);
const int MAX_PLAYERS = 16;
uint32_t g_last_unit[MAX_PLAYERS], g_body[MAX_PLAYERS];
typedef char(__fastcall* veto_fn)(uint64_t handle);
veto_fn g_veto_orig;

bool is_dead_biped(uint32_t handle) {
    int type = -1;
    uint8_t* o = object_of(handle, &type);
    return o && type == 0 && (*(uint32_t*)(o + 0x10) & F_DEAD);
}

void track_bodies() {
    uint8_t* hdr = *(uint8_t**)(g_h1 + RVA_PLAYERS);
    if (!hdr) return;
    int32_t rel = *(int32_t*)(hdr + 0x34);
    uint16_t size = *(uint16_t*)(hdr + 0x22);
    int count = *(int16_t*)(hdr + 0x20);
    for (int i = 0; i < MAX_PLAYERS; i++) {
        uint8_t* p = i < count ? hdr + rel + (uintptr_t)i * size : nullptr;
        if (!p || !*(uint16_t*)p) { g_last_unit[i] = g_body[i] = 0; continue; }      // (no player in this slot)
        uint32_t unit = *(uint32_t*)(p + 0x64);
        int type = -1;
        uint8_t* o = unit != 0xFFFFFFFFu ? object_of(unit, &type) : nullptr;
        if (o && type == 0 && !(*(uint32_t*)(o + 0x10) & F_DEAD)) { g_last_unit[i] = unit; continue; }
        if (g_last_unit[i] && is_dead_biped(g_last_unit[i])) { g_body[i] = g_last_unit[i]; g_last_unit[i] = 0; }
        else if (g_body[i] && !object_of(g_body[i], nullptr)) g_body[i] = 0;
    }
}

char __fastcall veto_hook(uint64_t handle) {
    if (g_keep) {
        uint32_t h = (uint32_t)handle;
        for (int i = 0; i < MAX_PLAYERS; i++)
            if (h && (h == g_body[i] || h == g_last_unit[i]) && is_dead_biped(h)) return 1;
    }
    return g_veto_orig(handle);
}

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
inline V mfwd(const float* m) { return {m[1], m[2], m[3]}; }
inline Q mquat(const float* m) { return qfrom_axes({m[1], m[2], m[3]}, {m[4], m[5], m[6]}, {m[7], m[8], m[9]}); }

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
    if (count != nodes || count > MAX_NODES || count < NN) return nullptr;
    uint8_t* hdr = *(uint8_t**)(g_h1 + RVA_TAGS);
    uint8_t* node = hdr + (*(uint32_t*)(model + 0xBC) - TAG_BASE);
    for (int k = 0; k < NN; k++) s->node[k] = -1;
    for (int i = 0; i < count; i++) {
        const char* name = (const char*)(node + i * 0x9C);
        s->body[i] = -1;
        for (int k = 0; k < NN; k++)
            if (!_strnicmp(name, NODE_NAME[k], 32)) { s->node[k] = (int8_t)i; s->body[i] = (int8_t)NODE_BODY[k]; }
    }
    for (int k = 0; k < NN; k++) if (s->node[k] < 0) return nullptr;
    for (int i = 0; i < count; i++) {                // others turn with their nearest named parent
        int k = i, guard = 0;
        while (s->body[k] < 0 && guard++ < MAX_NODES) {
            int parent = *(int16_t*)(node + k * 0x9C + 0x24);
            if (parent < 0 || parent >= count) break;
            k = parent;
        }
        s->body[i] = s->body[k] >= 0 ? s->body[k] : (int8_t)B_TORSO;
    }
    s->nodes = count;
    s->ok = true;
    logf("ce ragdolls: skeleton of biped tag %08x matched (%d nodes)", tag, count);
    return s;
}

// --- rigid body helpers
V iinv_world(const Body& b, V v) {                   // R I^-1 R^T v
    V l = qrot(qconj(b.q), v);
    V r{b.iinv[0][0] * l.x + b.iinv[0][1] * l.y + b.iinv[0][2] * l.z,
        b.iinv[1][0] * l.x + b.iinv[1][1] * l.y + b.iinv[1][2] * l.z,
        b.iinv[2][0] * l.x + b.iinv[2][1] * l.y + b.iinv[2][2] * l.z};
    return qrot(b.q, r);
}
float pos_w(const Body& b, V r, V n) { V rn = cross(r, n); return b.inv_m + dot(rn, iinv_world(b, rn)); }

// move point ra of a (world offset from its centre) by corr against point rb of b (b null: the world)
void apply_pos(Body& a, V ra, Body* b, V rb, V corr) {
    float c = len(corr);
    if (c < 1e-9f) return;
    V n = corr * (1.0f / c);
    float w = pos_w(a, ra, n) + (b ? pos_w(*b, rb, n) : 0);
    if (w < 1e-12f) return;
    V p = n * (c / w);
    a.x = a.x + p * a.inv_m;
    a.q = qturn(a.q, iinv_world(a, cross(ra, p)));
    if (b) {
        b->x = b->x - p * b->inv_m;
        b->q = qturn(b->q, -iinv_world(*b, cross(rb, p)));
    }
}

// turn a by the rotation vector rot against b (b turns the other way, by inverse inertia)
void apply_rot(Body& a, Body& b, V rot) {
    float th = len(rot);
    if (th < 1e-9f) return;
    V n = rot * (1.0f / th);
    float w = dot(n, iinv_world(a, n)) + dot(n, iinv_world(b, n));
    if (w < 1e-12f) return;
    V p = n * (th / w);
    a.q = qturn(a.q, iinv_world(a, p));
    b.q = qturn(b.q, -iinv_world(b, p));
}

// the twist of child axis y about bone axis d against y0 swung from c onto d (all world)
float twist_of(V c, V d, V y0, V y) {
    V k = cross(c, d);
    float s = len(k), co = dot(c, d);
    V ref = y0;
    if (s > 1e-6f) {
        k = k * (1.0f / s);
        ref = y0 * co + cross(k, y0) * s + k * (dot(k, y0) * (1 - co));
    }
    return atan2f(dot(cross(ref, y), d), dot(ref, y));
}

// the swing of d away from centre c, in the ellipse's axes (radians), and the ellipse's measure (1 = on its edge)
void swing_of(const Ball& bl, float slack, V c, V e1, V e2, V d, float* s1, float* s2, float* measure) {
    float a = acosf(clampf(dot(d, c), -1, 1));
    V t = d - c * dot(d, c);
    float tl = len(t);
    V lg = tl > 1e-7f ? t * (a / tl) : V{0, 0, 0};
    *s1 = dot(lg, e1);
    *s2 = dot(lg, e2);
    float ax = (*s1 >= 0 ? bl.s1hi : -bl.s1lo) * DEG * slack, ay = (*s2 >= 0 ? bl.s2hi : -bl.s2lo) * DEG * slack;
    *measure = sqrtf((*s1 / ax) * (*s1 / ax) + (*s2 / ay) * (*s2 / ay));
}

struct Frame { V c, e1, e2, y0; };
Frame ball_frame(const Rag& r, int j) {               // the ball's centre, axes and twist reference, world
    const Ball& bl = BALL[JOINT[j].index];
    Q f = qmul(r.b[JOINT[j].parent].q, r.ref_q[j]);
    Frame fr;
    fr.c = norm(qrot(f, {bl.c[0], bl.c[1], bl.c[2]}));
    fr.e1 = norm(qrot(f, {bl.e1[0], bl.e1[1], bl.e1[2]}));
    fr.e2 = cross(fr.c, fr.e1);
    fr.y0 = norm(qrot(f, {bl.y0[0], bl.y0[1], bl.y0[2]}));
    return fr;
}

float relax(const Rag& r, float at_death, float base) {   // a limit widened at death, back to its own in RELAX_TICKS
    float f = clampf(r.age / (float)RELAX_TICKS, 0, 1);
    return at_death + (base - at_death) * f;
}

void solve_joints(Rag& r) {
    for (int j = 0; j < NJ; j++) {
        const Joint& jt = JOINT[j];
        Body& p = r.b[jt.parent];
        Body& c = r.b[jt.child];
        V rp = qrot(p.q, r.pivot_p[j]), rc = qrot(c.q, r.pivot_c[j]);
        apply_pos(p, rp, &c, rc, (c.x + rc) - (p.x + rp));        // the pivot held together
        V cx = qrot(c.q, {1, 0, 0}), cy = qrot(c.q, {0, 1, 0}), cz = qrot(c.q, {0, 0, 1});
        if (jt.hinge) {
            const Hinge& hg = HINGE[jt.index];
            V px = qrot(p.q, {1, 0, 0}), pz = qrot(p.q, {0, 0, 1});
            float off = acosf(clampf(dot(cz, pz), -1, 1)), allowed = relax(r, r.axle0[j], 0);
            if (off > allowed + 1e-4f) apply_rot(c, p, norm(cross(cz, pz)) * (off - allowed));   // the axle lined up
            cx = qrot(c.q, {1, 0, 0});
            float th = atan2f(dot(cross(px, cx), pz), dot(px, cx));
            float lo = relax(r, r.hinge_lo0[j], hg.lo * DEG), hi = relax(r, r.hinge_hi0[j], hg.hi * DEG);
            float to = clampf(th, lo, hi);
            if (to != th) apply_rot(c, p, pz * (to - th));
            continue;
        }
        const Ball& bl = BALL[jt.index];
        Frame fr = ball_frame(r, j);
        float s1, s2, m, slack = relax(r, r.slack0[j], 1);
        swing_of(bl, slack, fr.c, fr.e1, fr.e2, cx, &s1, &s2, &m);
        if (m > 1) {                                 // back onto the ellipse's edge
            V lg = (fr.e1 * s1 + fr.e2 * s2) * (1.0f / m);
            float a = len(lg);
            V d2 = a > 1e-7f ? fr.c * cosf(a) + lg * (sinf(a) / a) : fr.c;
            V axis = cross(cx, d2);
            float sn = len(axis);
            if (sn > 1e-7f) apply_rot(c, p, axis * (atan2f(sn, dot(cx, d2)) / sn));
            cx = qrot(c.q, {1, 0, 0});
            cy = qrot(c.q, {0, 1, 0});
            fr = ball_frame(r, j);
        }
        float tw = twist_of(fr.c, cx, fr.y0, cy), half = bl.twist * DEG;
        float to = clampf(tw, r.twist0[j] - half, r.twist0[j] + half);
        if (to != tw) apply_rot(c, p, cx * (to - tw));
    }
}

// contacts for the tick: from each sphere along its motion and down, from the torso to it (a part inside a wall)
float g_result[64];
bool ray(V from, V by, V* at, V* n) {
    float pt[3] = {from.x, from.y, from.z}, vec[3] = {by.x, by.y, by.z};
    memset(g_result, 0, sizeof g_result);
    if (!g_collide(COLLIDE_FLAGS, pt, vec, 0xFFFFFFFFu, g_result)) return false;
    if (*(int16_t*)g_result < 0) return false;
    *at = {g_result[6], g_result[7], g_result[8]};
    *n = norm(V{g_result[9], g_result[10], g_result[11]});
    if (dot(*n, by) > 0) *n = -*n;                     // (facing where the ray came from)
    return true;
}

void add_contact(Rag& r, int s, V at, V n) {
    Contact* c = r.contact[s];
    int slot = !c[0].on ? 0 : !c[1].on ? 1 : (dot(c[0].n, n) > 0.95f ? 0 : 1);
    c[slot] = {at, n, true};
}

void gather(Rag& r, bool deep) {
    V torso = r.b[B_TORSO].x;
    for (int s = 0; s < NS; s++) {
        r.contact[s][0].on = r.contact[s][1].on = false;
        const Body& b = r.b[SPHERE[s].body];
        V rr = qrot(b.q, r.sphere[s]);
        V p = b.x + rr;
        float rad = SPHERE[s].r;
        V move = (b.v + cross(b.w, rr)) * TICK + V{0, 0, -GRAVITY * TICK * TICK};
        V at, n;
        float ml = len(move);
        if (ml > 1e-4f && ray(p, move * ((ml + rad + 0.02f) / ml), &at, &n)) add_contact(r, s, at, n);
        float down = rad + 0.06f + (move.z < 0 ? -move.z : 0);
        if (ray(p, V{0, 0, -down}, &at, &n)) add_contact(r, s, at, n);
        if (deep) {
            V to = p - torso;
            float tl = len(to);
            if (tl > 1e-4f && ray(torso, to * ((tl + rad) / tl), &at, &n)) add_contact(r, s, at, n);
        }
    }
}

void step(Rag& r) {
    gather(r, r.age < 2 || (r.age % 10) == 0);
    bool airborne[NB];                              // no ground within reach of any of the part's spheres
    for (int i = 0; i < NB; i++) airborne[i] = true;
    for (int s = 0; s < NS; s++)
        if (r.contact[s][0].on || r.contact[s][1].on) airborne[SPHERE[s].body] = false;
    for (int sub = 0; sub < SUB; sub++) {
        V sp[NS];
        for (int i = 0; i < NB; i++) {
            Body& b = r.b[i];
            b.v.z -= GRAVITY * H;
            b.xp = b.x;
            b.qp = b.q;
            b.x = b.x + b.v * H;
            b.q = qturn(b.q, b.w * H);
        }
        if (g_limb) {                                // (limb inertia) parts drag against each other, not against the air: a
            V cm{0, 0, 0}, dsum{0, 0, 0};              // trailing leg that the air alone slowed made the body a dart (head first, a
            float mt = 0;                              // spiral dive, live Nov 13). Each part is slowed by its speed relative to the
            for (int i = 0; i < NB; i++) { cm = cm + r.b[i].x * BODY_MASS[i]; mt += BODY_MASS[i]; }   // body's centre of mass motion,
            V vcm{0, 0, 0};                            // and what that took from the parts is given back to all (momentum kept)
            for (int i = 0; i < NB; i++) vcm = vcm + r.b[i].v * BODY_MASS[i];
            vcm = vcm * (1.0f / mt);
            V dv[NB];
            for (int i = 0; i < NB; i++) {
                V rel = r.b[i].v - vcm;
                float sp2 = len(rel);
                dv[i] = sp2 > 1e-4f ? rel * (-fminf(BODY_DRAG[i] * sp2 * H, 0.5f)) : V{0, 0, 0};
                dsum = dsum + dv[i] * BODY_MASS[i];
            }
            dsum = dsum * (1.0f / mt);
            for (int i = 0; i < NB; i++) r.b[i].v = r.b[i].v + dv[i] - dsum;
        }
        for (int s = 0; s < NS; s++) { const Body& b = r.b[SPHERE[s].body]; sp[s] = b.xp + qrot(b.qp, r.sphere[s]); }
        solve_joints(r);
        for (int s = 0; s < NS; s++)                 // parts against each other (not joint neighbours, not a pair
            for (int t = s + 1; t < NS; t++) {       // already touching at death)
                if (r.no_touch[s][t]) continue;
                Body& a = r.b[SPHERE[s].body];
                Body& c = r.b[SPHERE[t].body];
                V ra = qrot(a.q, r.sphere[s]), rc = qrot(c.q, r.sphere[t]);
                V d = (a.x + ra) - (c.x + rc);
                float dl = len(d), rr = SPHERE[s].r + SPHERE[t].r;
                if (dl >= rr || dl < 1e-6f) continue;
                apply_pos(a, ra, &c, rc, d * ((rr - dl) / dl));
            }
        bool touching[NS] = {};
        for (int s = 0; s < NS; s++) {
            Body& b = r.b[SPHERE[s].body];
            for (int k = 0; k < 2; k++) {
                const Contact& c = r.contact[s][k];
                if (!c.on) continue;
                V rr = qrot(b.q, r.sphere[s]);
                float depth = SPHERE[s].r - dot(b.x + rr - c.p, c.n);
                if (depth <= 0) continue;
                touching[s] = true;
                apply_pos(b, rr, nullptr, {0, 0, 0}, c.n * depth);
                rr = qrot(b.q, r.sphere[s]);
                V moved = b.x + rr - sp[s];
                V slide = moved - c.n * dot(moved, c.n);
                if (len(slide) < MU_STATIC * depth) apply_pos(b, rr, nullptr, {0, 0, 0}, -slide);   // held by friction
            }
        }
        for (int i = 0; i < NB; i++) {
            Body& b = r.b[i];
            b.v = (b.x - b.xp) * (1.0f / H);
            b.w = spin(b.qp, b.q, H);
        }
        for (int s = 0; s < NS; s++) {               // no bounce, sliding friction
            if (!touching[s]) continue;
            Body& b = r.b[SPHERE[s].body];
            V rr = qrot(b.q, r.sphere[s]);
            for (int k = 0; k < 2; k++) {
                const Contact& c = r.contact[s][k];
                if (!c.on) continue;
                V vp = b.v + cross(b.w, rr);
                float vn = dot(vp, c.n);
                V vt = vp - c.n * vn;
                V dv = c.n * -vn;
                float vtl = len(vt);
                if (vtl > 1e-6f) dv = dv - vt * (fminf(1.0f, MU_SLIDE * (fabsf(vn) + GRAVITY * H) / vtl));
                float dl = len(dv);
                if (dl < 1e-7f) continue;
                V n = dv * (1.0f / dl);
                float w = pos_w(b, rr, n);
                V imp = n * (dl / w);
                b.v = b.v + imp * b.inv_m;
                b.w = b.w + iinv_world(b, cross(rr, imp));
            }
        }
        float jd = 1 - expf(-JOINT_DAMP * H), sd = expf(-SPIN_DAMP * H);
        for (int j = 0; j < NJ; j++) {               // joint friction: the bodies' relative turning damped
            Body& p = r.b[JOINT[j].parent];
            Body& c = r.b[JOINT[j].child];
            V rel = c.w - p.w;
            float rl = len(rel);
            if (rl < 1e-6f) continue;
            V n = rel * (1.0f / rl);
            float w = dot(n, iinv_world(c, n)) + dot(n, iinv_world(p, n));
            V imp = n * (rl * jd / w);
            c.w = c.w - iinv_world(c, imp);
            p.w = p.w + iinv_world(p, imp);
        }
        for (int i = 0; i < NB; i++) {               // (a part on the ground: rolling resistance)
            bool down = false;
            for (int s = 0; s < NS; s++) down |= touching[s] && SPHERE[s].body == i;
            r.b[i].w = r.b[i].w * (down ? sd * expf(-ROLL_DAMP * H) : sd);
        }
    }
    {                                                // diagnostic (Nov 13): a sphere that jumps after the body was still (the limb drop)
        float worst = 0;
        int ws = -1;
        for (int s = 0; s < NS; s++) {
            const Body& b = r.b[SPHERE[s].body];
            V p = b.x + qrot(b.q, r.sphere[s]);
            float d = r.have_psp ? len(p - r.psp[s]) : 0;
            if (d > worst) { worst = d; ws = s; }
            r.psp[s] = p;
        }
        static int logged;
        if (r.have_psp && worst > 0.012f && r.still >= 3 && logged < 60) {
            logged++;
            int cons = 0;
            for (int s = 0; s < NS; s++) cons += r.contact[s][0].on + r.contact[s][1].on;
            logf("ce ragdoll jump: %.3f u at sphere %d (body %d) after %d still ticks, age %d, moving %d, deep %d, %d contacts, awake %d",
                 worst, ws, SPHERE[ws].body, r.still, r.age, r.moving, (int)(r.age < 2 || (r.age % 10) == 0), cons, (int)r.awake);
        }
        r.have_psp = true;
    }
    r.age++;
    r.moving++;
    bool slow = true;                                // every collision sphere (what is seen) under REST_SPEED
    for (int s = 0; s < NS; s++) {
        const Body& b = r.b[SPHERE[s].body];
        if (len(b.v + cross(b.w, qrot(b.q, r.sphere[s]))) > REST_SPEED) slow = false;
    }
    r.still = slow ? r.still + 1 : 0;
    // The limb drop (live, Nov 13): with the body lying still, an arm or leg went on creeping down, 0.02 u a tick for several
    // ticks, long after the rest looked settled (every sphere had to be under REST_SPEED to sleep). The torso and head still,
    // every other part under CREEP_SPEED, for CORE_TICKS ticks puts the body to sleep: a part that is really falling gains
    // speed past CREEP_SPEED within a few ticks, so it never gets there
    bool core = true;
    for (int s = 0; s < NS; s++) {
        const Body& b = r.b[SPHERE[s].body];
        float sp = len(b.v + cross(b.w, qrot(b.q, r.sphere[s])));
        if (sp > CREEP_SPEED || ((SPHERE[s].body == B_TORSO || SPHERE[s].body == B_HEAD) && sp > REST_SPEED)) core = false;
    }
    r.core = core ? r.core + 1 : 0;
    bool drifting = true;                            // (only drifting after 6 s, or 15 s gone: at rest. On real ground
    for (int i = 0; i < NB; i++) drifting &= len(r.b[i].v) < 0.3f;   // half the bodies crept at ~0.14 u/s, live)
    if ((r.still >= 10 && r.age > RELAX_TICKS) || (r.core >= CORE_TICKS && r.age > RELAX_TICKS) || (drifting && r.moving > 180) || r.moving > 450) {
        r.awake = false;
        for (int i = 0; i < NB; i++) r.b[i].v = r.b[i].w = V{0, 0, 0};
    }
}

void pose(Rag& r) {
    for (int n = 0; n < r.nodes; n++) {
        const Body& b = r.b[r.sk->body[n]];
        const float* l = r.local[n];
        float* m = r.out[n];
        V f = qrot(b.q, {l[1], l[2], l[3]}), lf = qrot(b.q, {l[4], l[5], l[6]}), u = qrot(b.q, {l[7], l[8], l[9]});
        V p = b.x + qrot(b.q, {l[10], l[11], l[12]});
        m[0] = l[0];
        m[1] = f.x; m[2] = f.y; m[3] = f.z;
        m[4] = lf.x; m[5] = lf.y; m[6] = lf.z;
        m[7] = u.x; m[8] = u.y; m[9] = u.z;
        m[10] = p.x; m[11] = p.y; m[12] = p.z;
    }
}

void write_pose(Rag& r, uint8_t* o) {
    int n = 0;
    float* m = matrices(o, &n);
    if (m && n == r.nodes) memcpy(m, r.out, sizeof(float) * 13 * n);
}

Rag* rag_of(uint32_t handle) {
    for (Rag& r : g_rag) if (r.used && r.handle == handle) return &r;
    return nullptr;
}

void start(uint32_t handle, uint8_t* o, const Skeleton* sk, float* m, int nodes, const Cache* prev) {
    Rag* r = nullptr;
    for (Rag& k : g_rag) if (!k.used) { r = &k; break; }
    if (!r) { r = &g_rag[0]; for (Rag& k : g_rag) if (k.born < r->born) r = &k; }   // all busy: the oldest one goes
    memset(r, 0, sizeof *r);
    r->handle = handle; r->used = r->awake = true; r->born = g_tick; r->sk = sk; r->nodes = nodes;
    const float* M[NN];
    for (int k = 0; k < NN; k++) M[k] = m + 13 * sk->node[k];
    // collision spheres (world, at death)
    V sw[NS];
    for (int s = 0; s < NS; s++) {
        const SphereDef& d = SPHERE[s];
        V a = mpos(M[d.node]);
        sw[s] = d.toward >= 0 ? a + (mpos(M[d.toward]) - a) * d.t : a + norm(mfwd(M[d.node])) * d.t;
    }
    // bodies: frame of their node, centre of mass = the mean of their spheres, inertia from the spheres
    for (int i = 0; i < NB; i++) {
        Body& b = r->b[i];
        V c{0, 0, 0};
        int n = 0;
        for (int s = 0; s < NS; s++) if (SPHERE[s].body == i) { c = c + sw[s]; n++; }
        b.x = c * (1.0f / n);
        b.q = mquat(M[BODY_NODE[i]]);
        b.inv_m = 1.0f / BODY_MASS[i];
        float I[3][3] = {};
        float mi = BODY_MASS[i] / n;
        for (int s = 0; s < NS; s++) {
            if (SPHERE[s].body != i) continue;
            V l = qrot(qconj(b.q), sw[s] - b.x);
            float rr = SPHERE[s].r, sph = 0.4f * mi * rr * rr, d2 = dot(l, l);
            float lv[3] = {l.x, l.y, l.z};
            for (int a = 0; a < 3; a++)
                for (int c2 = 0; c2 < 3; c2++) I[a][c2] += mi * ((a == c2 ? d2 : 0) - lv[a] * lv[c2]) + (a == c2 ? sph : 0);
        }
        // a part's own thickness (armour, a 0.06 u radius of gyration): spheres along a bone gave a limb next to no
        // inertia about its axis, and contact and hinge corrections spun the calves in place (0.9 rad/s, offline)
        for (int a = 0; a < 3; a++) I[a][a] += BODY_MASS[i] * 0.06f * 0.06f;
        float det = I[0][0] * (I[1][1] * I[2][2] - I[1][2] * I[2][1]) - I[0][1] * (I[1][0] * I[2][2] - I[1][2] * I[2][0]) +
                    I[0][2] * (I[1][0] * I[2][1] - I[1][1] * I[2][0]);
        if (fabsf(det) < 1e-18f) { for (int a = 0; a < 3; a++) I[a][a] += 1e-5f; det = I[0][0] * I[1][1] * I[2][2]; }
        float id = 1.0f / det;
        b.iinv[0][0] = (I[1][1] * I[2][2] - I[1][2] * I[2][1]) * id; b.iinv[0][1] = (I[0][2] * I[2][1] - I[0][1] * I[2][2]) * id;
        b.iinv[0][2] = (I[0][1] * I[1][2] - I[0][2] * I[1][1]) * id; b.iinv[1][0] = (I[1][2] * I[2][0] - I[1][0] * I[2][2]) * id;
        b.iinv[1][1] = (I[0][0] * I[2][2] - I[0][2] * I[2][0]) * id; b.iinv[1][2] = (I[0][2] * I[1][0] - I[0][0] * I[1][2]) * id;
        b.iinv[2][0] = (I[1][0] * I[2][1] - I[1][1] * I[2][0]) * id; b.iinv[2][1] = (I[0][1] * I[2][0] - I[0][0] * I[2][1]) * id;
        b.iinv[2][2] = (I[0][0] * I[1][1] - I[0][1] * I[1][0]) * id;
        // its motion over the last tick (the death animation, and the corpse's own flight)
        if (prev) {
            const float* pm = prev->m[sk->node[BODY_NODE[i]]];
            Q pq = mquat(pm);
            V node_local = qrot(qconj(b.q), mpos(M[BODY_NODE[i]]) - b.x);
            V px = mpos(pm) - qrot(pq, node_local);
            b.v = (b.x - px) * (1.0f / TICK);
            b.w = spin(pq, b.q, TICK);
            if (len(b.v) > 20) b.v = norm(b.v) * 20;
            if (len(b.w) > 25) b.w = norm(b.w) * 25;
        }
    }
    for (int s = 0; s < NS; s++) {
        const Body& b = r->b[SPHERE[s].body];
        r->sphere[s] = qrot(qconj(b.q), sw[s] - b.x);
    }
    for (int s = 0; s < NS; s++)
        for (int t = s + 1; t < NS; t++) {
            int a = SPHERE[s].body, c = SPHERE[t].body;
            bool joined = a == c;
            for (int j = 0; j < NJ; j++)
                joined |= (JOINT[j].parent == a && JOINT[j].child == c) || (JOINT[j].parent == c && JOINT[j].child == a);
            r->no_touch[s][t] = joined || len(sw[s] - sw[t]) < SPHERE[s].r + SPHERE[t].r;
        }
    for (int n = 0; n < nodes; n++) {
        const Body& b = r->b[sk->body[n]];
        const float* src = m + 13 * n;
        float* l = r->local[n];
        Q iq = qconj(b.q);
        V f = qrot(iq, mfwd(src)), lf = qrot(iq, {src[4], src[5], src[6]}), u = qrot(iq, {src[7], src[8], src[9]});
        V p = qrot(iq, mpos(src) - b.x);
        l[0] = src[0];
        l[1] = f.x; l[2] = f.y; l[3] = f.z; l[4] = lf.x; l[5] = lf.y; l[6] = lf.z; l[7] = u.x; l[8] = u.y; l[9] = u.z;
        l[10] = p.x; l[11] = p.y; l[12] = p.z;
    }
    // joints: pivots (the child node's origin) in both bodies; limits widened to the pose it died in
    for (int j = 0; j < NJ; j++) {
        const Joint& jt = JOINT[j];
        Body& p = r->b[jt.parent];
        Body& c = r->b[jt.child];
        V piv = mpos(M[BODY_NODE[jt.child]]);
        r->pivot_p[j] = qrot(qconj(p.q), piv - p.x);
        r->pivot_c[j] = qrot(qconj(c.q), piv - c.x);
        V cx = qrot(c.q, {1, 0, 0}), cy = qrot(c.q, {0, 1, 0}), cz = qrot(c.q, {0, 0, 1});
        if (jt.hinge) {
            const Hinge& hg = HINGE[jt.index];
            V px = qrot(p.q, {1, 0, 0}), pz = qrot(p.q, {0, 0, 1});
            r->axle0[j] = acosf(clampf(dot(cz, pz), -1, 1));
            float th = atan2f(dot(cross(px, cx), pz), dot(px, cx));
            r->hinge_lo0[j] = fminf(hg.lo * DEG, th - 2 * DEG);
            r->hinge_hi0[j] = fmaxf(hg.hi * DEG, th + 2 * DEG);
            continue;
        }
        const Ball& bl = BALL[jt.index];
        r->ref_q[j] = qmul(qconj(p.q), mquat(M[bl.ref]));
        Frame fr = ball_frame(*r, j);
        float s1, s2, ms;
        swing_of(bl, 1, fr.c, fr.e1, fr.e2, cx, &s1, &s2, &ms);
        r->slack0[j] = ms > 1 ? ms * 1.02f : 1;
        r->twist0[j] = twist_of(fr.c, cx, fr.y0, cy);
    }
    if (g_limb) {                                    // (limb inertia) a body that starts out flying: its limbs trail
        V vt = r->b[B_TORSO].v;
        float sp = len(vt);
        if (sp > LIMB_LAG_FROM) {
            float lag = clampf((sp - LIMB_LAG_FROM) / (LIMB_LAG_FULL - LIMB_LAG_FROM), 0, 1) * LIMB_LAG_MAX;
            for (int i = 1; i < NB; i++) r->b[i].v = r->b[i].v - vt * (lag * BODY_LAG[i]);
        }
    }
    // the push (Halo 2: min(0.7, the biped's) x (1.5 + 1.75 r) along the hit, bodies higher up harder so the body
    // topples, an upward part 0.75 + 0.75 r): along the torso's own motion (the death animation picked from the hit's
    // side), else backward; x PUSH_SCALE
    V dir = r->b[B_TORSO].v;
    dir.z = 0;
    if (len(dir) < 0.1f) dir = -qrot(r->b[B_TORSO].q, {0, 1, 0});
    dir.z = 0;
    dir = norm(dir, {1, 0, 0});
    float strength = PUSH_SCALE * 0.7f * (1.5f + 1.75f * rnd());
    V pop{0, 0, PUSH_SCALE * (0.75f + 0.75f * rnd())};
    float zlo = 1e9f, zhi = -1e9f;
    for (int i = 0; i < NB; i++) { zlo = fminf(zlo, r->b[i].x.z); zhi = fmaxf(zhi, r->b[i].x.z); }
    // Halo 2 pushes higher bodies harder so a standing body topples. A body already flying (an explosion threw it) is
    // pushed the same all over: the gradient turned it head first into a spiral dive in the air (live Nov 13)
    float flying = clampf((len(r->b[B_TORSO].v) - LIMB_LAG_FROM) / 4.0f, 0, 1);
    for (int i = 0; i < NB; i++) {
        float h = (r->b[i].x.z - zlo) / (zhi - zlo + 1e-4f);
        float w = 0.35f + 0.65f * h;
        r->b[i].v = r->b[i].v + dir * (strength * (w + (1.0f - w) * flying)) + pop;
    }
    r->obj_v = *(V*)(o + 0x24);
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
        if (c.handle != (uint32_t)handle) { c.handle = (uint32_t)handle; c.dead_ticks = -1; c.nodes = 0; }
        bool dead = (*(uint32_t*)(o + 0x10) & F_DEAD) != 0;
        if (dead && c.dead_ticks >= 0 && ++c.dead_ticks >= START_TICKS     // (dead_ticks -1: never seen alive)
            && *(int32_t*)(g_h1 + RVA_VARIANT + 0x30) > 0 && g_collide && g_enabled) {
            start((uint32_t)handle, o, sk, m, nodes, c.nodes == nodes ? &c : nullptr);
            c.handle = 0;
            return;
        }
        if (!dead) c.dead_ticks = 0;
        memcpy(c.m, m, sizeof(float) * 13 * nodes);
        c.nodes = nodes;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
    }
}

// The pose must be the LAST thing written to a ragdolled body's node matrices in a tick. The object's own update
// (FUN_180b3a06c) runs the game's per-type callbacks (a dead biped's limbs settle there: live Nov 13, the limbs sank and
// came back a second later) around the node build, and a corpse at rest skips the build the nodes_hook sits on. So the
// whole update is hooked, and the pose written once more after it.
uint64_t __fastcall update_hook(uint64_t handle) {
    uint64_t ret = g_update_orig(handle);
    __try {
        if (Rag* r = rag_of((uint32_t)handle)) {
            int type = -1;
            uint8_t* o = object_of((uint32_t)handle, &type);
            if (o && type == 0) write_pose(*r, o);
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
    }
    return ret;
}

// What is drawn is not the node matrices but a per-object snapshot of them (FUN_180b3af10 -> FUN_180ba8414 memcpys the
// nodes, position and axes into a 0xD4C record the renderer interpolates). The node build ends by jumping into it, so
// when the game rebuilt a corpse's nodes (its own dead pose, limbs slumping over the ground) the snapshot took that,
// before the nodes_hook wrote the ragdoll's: the "limb drop" (live, Nov 13: a bot's head and arm sank for ~0.6 s 1.5 s
// after death and came back; the node matrices themselves were the ragdoll's at every tick). The pose goes in first
uint64_t __fastcall snapshot_hook(uint64_t handle) {
    __try {
        if (Rag* r = rag_of((uint32_t)handle)) {
            int type = -1;
            uint8_t* o = object_of((uint32_t)handle, &type);
            if (o && type == 0) write_pose(*r, o);
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
    }
    return g_snapshot_orig(handle);
}

}  // namespace

// botcore's tick hook (start of each Halo CE tick): step every awake body, write every body's pose
void ce_ragdoll_tick() {
    if (!g_nodes_orig) return;
    if (g_tick++ % 60 == 0) read_settings();
    if (g_tick % 150 == 0) {                         // (every 5 s: how many ragdolls there are, for the limb drop hunt)
        int used = 0, awake = 0;
        for (Rag& r : g_rag) { used += r.used; awake += r.used && r.awake; }
        static int shown;
        if (used && shown < 120) { shown++; logf("ce ragdolls: %d bodies, %d awake", used, awake); }
    }
    __try {
        track_bodies();
        int awake = 0;
        for (Rag& r : g_rag) awake += r.used && r.awake;
        for (Rag& r : g_rag) {
            if (!r.used) continue;
            int type = -1;
            uint8_t* o = object_of(r.handle, &type);
            int nodes = 0;
            if (!o || type != 0 || !matrices(o, &nodes) || nodes != r.nodes) {
                static int released;                 // (why a body stopped being a ragdoll: the limb drop hunt, Nov 13)
                if (released < 40) { released++; logf("ce ragdoll released: age %d, object %d, type %d, nodes %d (was %d), awake %d", r.age, o != nullptr, type, nodes, r.nodes, (int)r.awake); }
                r.used = false;
                continue;
            }
            V ov = *(V*)(o + 0x24);                  // a kick to the corpse (its speed jumps): the body takes it
            V dv = (ov - r.obj_v) * (1.0f / TICK);
            if (len(ov) > len(r.obj_v) + 0.02f && len(ov) > 0.05f) {
                static int kicks;
                if (kicks < 40) { kicks++; logf("ce ragdoll kick: %.2f u/s, age %d, awake %d", len(dv), r.age, (int)r.awake); }
                for (int i = 0; i < NB; i++) r.b[i].v = r.b[i].v + dv * (g_limb && i ? LIMB_KICK : 1.0f);   // (limb inertia: the torso takes the blast)
                r.moving = 0;                    // (its rest clocks start again: a kicked old body tumbles)
                if (!r.awake) { r.awake = true; r.still = 0; awake++; }
            }
            r.obj_v = ov;
            if (r.awake && awake > AWAKE_MAX) {       // too many moving: the oldest stop where they are
                Rag* oldest = &r;
                for (Rag& k : g_rag) if (k.used && k.awake && k.born < oldest->born) oldest = &k;
                oldest->awake = false;
                awake--;
            }
            if (r.awake) { step(r); pose(r); }
            // the corpse object (what the game culls by: a 0.42 u sphere about it, and the map area it is filed in)
            // kept under the body: bodies ended 1-6 u from it and vanished as they settled (live, Nov 13). The
            // game's own setter, so the object is filed in the map where it now is; its velocity zeroed (a kick
            // from the game shows as new velocity next tick)
            V lo{1e9f, 1e9f, 1e9f}, hi{-1e9f, -1e9f, -1e9f};
            for (int s = 0; s < NS; s++) {
                const Body& b = r.b[SPHERE[s].body];
                V p = b.x + qrot(b.q, r.sphere[s]);
                lo = {fminf(lo.x, p.x), fminf(lo.y, p.y), fminf(lo.z, p.z - SPHERE[s].r)};
                hi = {fmaxf(hi.x, p.x), fmaxf(hi.y, p.y), fmaxf(hi.z, p.z)};
            }
            V at{(lo.x + hi.x) * 0.5f, (lo.y + hi.y) * 0.5f, lo.z};
            if (g_set_position && len(at - *(V*)(o + 0x18)) > 0.02f) {
                float pos[3] = {at.x, at.y, at.z};
                g_set_position(r.handle, pos, nullptr, nullptr);
                *(V*)(o + 0x24) = V{0, 0, 0};
                r.obj_v = V{0, 0, 0};
            }
            write_pose(r, o);                        // (last: object_set_position rebuilds and moves the nodes too)
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        for (Rag& r : g_rag) r.used = false;
        logf("ce ragdolls: fault in the solver: bodies dropped");
    }
}

// installed with botcore's other halo1 hooks (enabled by their MH_EnableHook(MH_ALL_HOOKS)); false: left off
bool ce_ragdoll_install(uint8_t* h1) {
    if (g_h1) { MH_RemoveHook(g_h1 + RVA_NODE_MATRICES); MH_RemoveHook(g_h1 + RVA_GC_VETO); MH_RemoveHook(g_h1 + RVA_OBJECT_UPDATE); MH_RemoveHook(g_h1 + RVA_SNAPSHOT); }
    g_nodes_orig = nullptr;
    g_collide = nullptr;
    g_set_position = nullptr;
    memset(g_last_unit, 0, sizeof g_last_unit);
    memset(g_body, 0, sizeof g_body);
    for (Rag& r : g_rag) r.used = false;
    memset(g_cache, 0, sizeof g_cache);
    memset(g_skel, 0, sizeof g_skel);
    g_h1 = h1;
    if (memcmp(h1 + RVA_NODE_MATRICES, NODES_PROLOGUE, sizeof NODES_PROLOGUE) ||
        memcmp(h1 + RVA_COLLISION_TEST, COLLISION_PROLOGUE, sizeof COLLISION_PROLOGUE) ||
        memcmp(h1 + RVA_SET_POSITION, SET_POSITION_PROLOGUE, sizeof SET_POSITION_PROLOGUE) ||
        memcmp(h1 + RVA_GC_VETO, GC_VETO_PROLOGUE, sizeof GC_VETO_PROLOGUE) ||
        memcmp(h1 + RVA_OBJECT_UPDATE, UPDATE_PROLOGUE, sizeof UPDATE_PROLOGUE) ||
        memcmp(h1 + RVA_SNAPSHOT, SNAPSHOT_PROLOGUE, sizeof SNAPSHOT_PROLOGUE)) {
        logf("ce ragdolls: not the MCC 1.3528 build decoded: off");
        return false;
    }
    g_collide = (collide_fn)(h1 + RVA_COLLISION_TEST);
    g_set_position = (set_position_fn)(h1 + RVA_SET_POSITION);
    if (MH_CreateHook(h1 + RVA_GC_VETO, (void*)&veto_hook, (void**)&g_veto_orig) != MH_OK ||
        MH_CreateHook(h1 + RVA_OBJECT_UPDATE, (void*)&update_hook, (void**)&g_update_orig) != MH_OK ||
        MH_CreateHook(h1 + RVA_SNAPSHOT, (void*)&snapshot_hook, (void**)&g_snapshot_orig) != MH_OK ||
        MH_CreateHook(h1 + RVA_NODE_MATRICES, (void*)&nodes_hook, (void**)&g_nodes_orig) != MH_OK) {
        g_nodes_orig = nullptr;
        logf("ce ragdolls: hook failed");
        return false;
    }
    return true;
}

// botcore's folder (native\bin): the launcher's settings are in ..\..\user\settings.json from there
void ce_ragdoll_folder(const wchar_t* dll_dir) {
    swprintf_s(g_settings, L"%s..\\..\\user\\settings.json", dll_dir);
    read_settings();
}
