// test_ragdoll.cpp: native/ce_ragdoll.cpp's solver, offline. Built and run by tools/test_native_ragdoll.py.
// A live CE cyborg pose (test_ragdoll_pose.h) dies over a flat floor (z = 0) next to a wall (x = WALL), with the game's
// collision test stood in for by those two planes. Checks: nothing non-finite; a body dropped still comes to rest
// lying on the floor (no node under it), asleep within 4 s and not moving after; every joint inside its limits at rest
// (swing ellipse, hinge range, twist width, pivots together); one thrown up at 6 u/s keeps its momentum (rises at least
// 0.6 of a free throw's height) and lands; one thrown at the wall stops at it. Exit 0 and "ragdoll OK", else FAIL lines.
#include "../ce_ragdoll.cpp"
#include <stdio.h>
#include "test_ragdoll_pose.h"

void logf(const char*, ...) {}
MH_STATUS WINAPI MH_CreateHook(LPVOID, LPVOID, LPVOID*) { return MH_OK; }
MH_STATUS WINAPI MH_RemoveHook(LPVOID) { return MH_OK; }

static const float WALL = 1.2f;
static int g_fail;
static float g_furthest = -1e9f;               // the furthest +x any node reached (the wall test)
#define CHECK(c, ...) do { if (!(c)) { printf("FAIL: "); printf(__VA_ARGS__); printf("\n"); g_fail++; } } while (0)

static V g_floor{0, 0, 1};                      // the floor through the origin (tilted for the slope test)

// the floor and the wall x = WALL (facing -x), as collision_test_vector reports them
static char __fastcall fake_collide(uint64_t, float* p, float* v, uint32_t, void* result) {
    float best = 2;
    V at{}, n{};
    float f0 = dot(g_floor, {p[0], p[1], p[2]}), f1 = dot(g_floor, {p[0] + v[0], p[1] + v[1], p[2] + v[2]});
    if (f0 >= 0 && f1 < 0) { float t = f0 / (f0 - f1); if (t < best) { best = t; n = g_floor; } }
    if (p[0] <= WALL && p[0] + v[0] > WALL) { float t = (WALL - p[0]) / v[0]; if (t < best) { best = t; n = {-1, 0, 0}; } }
    if (best > 1) return 0;
    at = {p[0] + v[0] * best, p[1] + v[1] * best, p[2] + v[2] * best};
    float* r = (float*)result;
    *(int16_t*)r = 2;
    r[5] = best;
    r[6] = at.x; r[7] = at.y; r[8] = at.z;
    r[9] = n.x; r[10] = n.y; r[11] = n.z; r[12] = -dot(n, at);
    return 1;
}

static Skeleton make_skeleton() {
    static const int CE_INDEX[NN] = {0, 3, 6, 9, 7, 10, 12, 13, 14, 15, 16, 17, 18, 1, 2, 4, 5, 8, 11};
    Skeleton s{};
    s.tag = 1; s.ok = true; s.nodes = 19;
    for (int k = 0; k < NN; k++) { s.node[k] = (int8_t)CE_INDEX[k]; s.body[CE_INDEX[k]] = (int8_t)NODE_BODY[k]; }
    return s;
}

static bool finite_all(const Rag& r) {
    for (int n = 0; n < r.nodes; n++) for (int k = 0; k < 13; k++) if (!isfinite(r.out[n][k])) return false;
    return true;
}

// the deepest overlap of two parts that should collide (u)
static float overlap(const Rag& r) {
    float worst = 0;
    for (int s = 0; s < NS; s++)
        for (int t = s + 1; t < NS; t++) {
            if (r.no_touch[s][t]) continue;
            const Body& a = r.b[SPHERE[s].body];
            const Body& c = r.b[SPHERE[t].body];
            float d = len((a.x + qrot(a.q, r.sphere[s])) - (c.x + qrot(c.q, r.sphere[t])));
            worst = fmaxf(worst, SPHERE[s].r + SPHERE[t].r - d);
        }
    return worst;
}

// the joints' state against their limits: worst swing measure, worst hinge overshoot, worst twist overshoot, pivot gap
static void limits(Rag& r, float* swing, float* hinge, float* twist, float* gap) {
    *swing = *hinge = *twist = *gap = 0;
    for (int j = 0; j < NJ; j++) {
        const Joint& jt = JOINT[j];
        Body& p = r.b[jt.parent];
        Body& c = r.b[jt.child];
        V rp = qrot(p.q, r.pivot_p[j]), rc = qrot(c.q, r.pivot_c[j]);
        *gap = fmaxf(*gap, len((c.x + rc) - (p.x + rp)));
        V cx = qrot(c.q, {1, 0, 0}), cy = qrot(c.q, {0, 1, 0});
        if (jt.hinge) {
            V px = qrot(p.q, {1, 0, 0}), pz = qrot(p.q, {0, 0, 1});
            float th = atan2f(dot(cross(px, cx), pz), dot(px, cx));
            float lo = fminf(HINGE[jt.index].lo * DEG, r.hinge_lo0[j]), hi = fmaxf(HINGE[jt.index].hi * DEG, r.hinge_hi0[j]);
            lo = r.age >= RELAX_TICKS ? HINGE[jt.index].lo * DEG : lo;
            hi = r.age >= RELAX_TICKS ? HINGE[jt.index].hi * DEG : hi;
            *hinge = fmaxf(*hinge, fmaxf(lo - th, th - hi) / DEG);
            continue;
        }
        Frame fr = ball_frame(r, j);
        float s1, s2, m;
        swing_of(BALL[jt.index], 1, fr.c, fr.e1, fr.e2, cx, &s1, &s2, &m);
        *swing = fmaxf(*swing, m);
        float tw = twist_of(fr.c, cx, fr.y0, cy);
        *twist = fmaxf(*twist, (fabsf(tw - r.twist0[j]) - BALL[jt.index].twist * DEG) / DEG);
    }
}

// one death from the pose, its parts given velocity v (u/s) on top of the push; ticks until asleep or `ticks`
static Rag& die(V v, int ticks, float* top, int* slept_at) {
    static Skeleton sk = make_skeleton();
    static uint8_t object[0x200];
    static float m[19][13];
    memcpy(m, POSE, sizeof m);
    Rag& r = g_rag[0];
    memset(&r, 0, sizeof r);
    start(1, object, &sk, &m[0][0], 19, nullptr);
    for (int i = 0; i < NB; i++) r.b[i].v = r.b[i].v + v;
    *top = -1e9f;
    *slept_at = -1;
    for (int t = 0; t < ticks; t++) {
        if (r.awake) { step(r); pose(r); }
        else if (*slept_at < 0) *slept_at = t;
        for (int i = 0; i < NB; i++) *top = fmaxf(*top, r.b[i].x.z);
        for (int n = 0; n < r.nodes; n++) g_furthest = fmaxf(g_furthest, r.out[n][10]);
    }
    return r;
}

int main() {
    g_collide = &fake_collide;
    float top;
    int slept;
    // 1. dropped where it stands
    Rag& r = die({0, 0, 0}, 120, &top, &slept);
    CHECK(finite_all(r), "non-finite node matrix (drop)");
    CHECK(slept >= 0, "not at rest within 4 s (drop)");
    float lowest = 1e9f, highest = -1e9f;
    for (int n = 0; n < r.nodes; n++) { lowest = fminf(lowest, r.out[n][12]); highest = fmaxf(highest, r.out[n][12]); }
    CHECK(lowest > -0.01f, "a node under the floor at rest: z %.3f", lowest);
    CHECK(highest < 0.3f, "not lying down at rest: highest node z %.3f", highest);
    float sw, hg, tw, gap;
    limits(r, &sw, &hg, &tw, &gap);
    CHECK(sw < 1.05f, "a ball joint outside its swing limit at rest: %.2f of the ellipse", sw);
    CHECK(hg < 3.0f, "a hinge %.1f deg past its range at rest", hg);
    CHECK(tw < 3.0f, "a twist %.1f deg past its width at rest", tw);
    CHECK(gap < 0.01f, "a joint pulled apart at rest: %.3f u", gap);
    CHECK(overlap(r) < 0.015f, "two parts %.3f u inside each other at rest", overlap(r));
    float before[19][13];
    memcpy(before, r.out, sizeof before);
    for (int t = 0; t < 30; t++) if (r.awake) { step(r); pose(r); }
    float drift = 0;
    for (int n = 0; n < 19; n++) for (int k = 10; k < 13; k++) drift = fmaxf(drift, fabsf(r.out[n][k] - before[n][k]));
    CHECK(drift < 1e-4f, "moving while down: %.4f u in 1 s", drift);
    if (r.awake)
        for (int t = 0; t < 12; t++) {
            step(r);
            float mv = 0, mw = 0;
            int bv = 0, bw = 0;
            for (int i = 0; i < NB; i++) {
                if (len(r.b[i].v) > mv) { mv = len(r.b[i].v); bv = i; }
                if (len(r.b[i].w) > mw) { mw = len(r.b[i].w); bw = i; }
            }
            printf("  still moving: tick %d max v %.3f (body %d) max w %.3f (body %d) still %d\n", t, mv, bv, mw, bw, r.still);
        }
    printf("drop: at rest after %d ticks, lowest %.3f highest %.3f, swing %.2f hinge %.1f twist %.1f gap %.4f\n", slept,
           lowest, highest, sw, hg, tw, gap);
    // 2. thrown up: keeps its momentum, lands
    Rag& u = die({0, 0, 6}, 240, &top, &slept);
    float free_top = 0.3f + 36 / (2 * GRAVITY);
    CHECK(finite_all(u), "non-finite node matrix (thrown up)");
    CHECK(top > 0.6f * free_top, "thrown up 6 u/s: rose to %.2f, a free throw %.2f", top, free_top);
    CHECK(slept >= 0, "thrown up: not at rest within 8 s");
    lowest = 1e9f;
    for (int n = 0; n < u.nodes; n++) lowest = fminf(lowest, u.out[n][12]);
    CHECK(lowest > -0.01f, "thrown up: a node under the floor after landing: z %.3f", lowest);
    printf("thrown up: top %.2f (free %.2f), at rest after %d ticks\n", top, free_top, slept);
    // 3. thrown at the wall
    g_furthest = -1e9f;
    Rag& w = die({5, 0, 1}, 150, &top, &slept);
    CHECK(finite_all(w), "non-finite node matrix (wall)");
    float rest_x = -1e9f;
    for (int n = 0; n < w.nodes; n++) rest_x = fmaxf(rest_x, w.out[n][10]);
    CHECK(g_furthest < WALL + 0.05f, "thrown at the wall: a node went %.3f past it", g_furthest - WALL);
    CHECK(rest_x < WALL + 0.005f, "thrown at the wall: a node %.3f inside it at rest", rest_x - WALL);
    CHECK(g_furthest > WALL - 0.15f, "thrown at the wall at 5 u/s: never reached it (furthest node %.3f)", g_furthest);
    printf("thrown at the wall: furthest node %.3f (wall %.2f), at rest after %d ticks\n", g_furthest, WALL, slept);
    // 4. dropped on a 20 deg slope: comes to rest (no creeping down it), nothing inside the slope or itself
    g_floor = norm(V{sinf(20 * DEG), 0, cosf(20 * DEG)});
    Rag& sl = die({0, 0, 0}, 240, &top, &slept);
    CHECK(finite_all(sl), "non-finite node matrix (slope)");
    CHECK(slept >= 0, "on a 20 deg slope: not at rest within 8 s");
    float under = 1e9f;
    for (int n = 0; n < sl.nodes; n++) under = fminf(under, dot(g_floor, {sl.out[n][10], sl.out[n][11], sl.out[n][12]}));
    memcpy(before, sl.out, sizeof before);
    for (int t = 0; t < 30; t++) if (sl.awake) { step(sl); pose(sl); }
    drift = 0;
    for (int n = 0; n < 19; n++) for (int k = 10; k < 13; k++) drift = fmaxf(drift, fabsf(sl.out[n][k] - before[n][k]));
    CHECK(under > -0.01f, "on a slope: a node %.3f inside it", -under);
    CHECK(drift < 1e-4f, "on a slope: creeping %.4f u in 1 s at rest", drift);
    CHECK(overlap(sl) < 0.015f, "on a slope: two parts %.3f u inside each other", overlap(sl));
    printf("slope 20 deg: at rest after %d ticks, lowest over it %.3f, overlap %.3f\n", slept, under, overlap(sl));
    g_floor = V{0, 0, 1};
    // 5. the launcher's switch: user\settings.json two folders up from botcore's; no file = on
    wchar_t tmp[MAX_PATH], dir[MAX_PATH], user[MAX_PATH], file[MAX_PATH];
    GetTempPathW(MAX_PATH, tmp);
    swprintf_s(dir, L"%sppg_rag_%lu\\native\\bin\\", tmp, GetCurrentProcessId());
    swprintf_s(user, L"%sppg_rag_%lu\\user", tmp, GetCurrentProcessId());
    swprintf_s(file, L"%s\\settings.json", user);
    ce_ragdoll_folder(dir);
    CHECK(g_enabled, "no settings file: ragdolls should be on");
    wchar_t base[MAX_PATH];
    swprintf_s(base, L"%sppg_rag_%lu", tmp, GetCurrentProcessId());
    CreateDirectoryW(base, nullptr);
    CreateDirectoryW(user, nullptr);
    for (int on = 0; on < 2; on++) {
        FILE* f = nullptr;
        _wfopen_s(&f, file, L"w");
        if (!f) { CHECK(false, "could not write the test settings file"); break; }
        fprintf(f, "{\n \"ce_ragdolls\": %s\n}", on ? "true" : "false");
        fclose(f);
        Sleep(20);
        read_settings();
        if (g_enabled != (on == 1)) {
            WIN32_FILE_ATTRIBUTE_DATA a;
            printf("  reader path %ls exists %d, file %ls\n", g_settings,
                   (int)GetFileAttributesExW(g_settings, GetFileExInfoStandard, &a), file);
        }
        CHECK(g_enabled == (on == 1), "settings file \"ce_ragdolls\": %s read as %s", on ? "true" : "false",
              g_enabled ? "on" : "off");
    }
    DeleteFileW(file);
    if (g_fail) return 1;
    printf("ragdoll OK\n");
    return 0;
}
