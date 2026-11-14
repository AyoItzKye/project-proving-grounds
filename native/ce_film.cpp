// ce_film.cpp: Theater for Halo: CE, the recorder (docs/THEATER_RE.md).
//
// halo1.dll has Halo 3's simulation layer, but MCC runs it in a mode (DAT_181b7b630 set) where each tick's simulation
// update carries almost nothing (live Nov 13: 19 of 0xCC00 bytes ever non-zero). Every player's input comes through
// the action dequeue botcore hooks (RVA 0xB66AF8: 16 actions of 0x30 bytes in live-player order, the bots' already
// written by fill_bot_actions). A film is that stream: [u32 tick][u16 bytes][u32 seeds[2]][the actions, trailing empty
// slots cut]. The seeds are halo1's two random number seeds (+0x2EA74F4, +0x2EA74F8: every inlined random step reads one
// of them, 240 sites), outside the game state and moved between ticks by the frame rate, so a film without them spawned
// players in other places than the match did (film32, Nov 13: player 0 at x 31.3 one run, 7.2 the next); version 3
// films (before) have no seeds.
//
// Files: <films>\ce\<date-time>.cefilm, the newest KEEP kept. Header: "PPGCEFILM3\0\0", u32 version, u64 time recorded,
// u32 block size, MCC's launch block of the match (map, variant, players; film pointer +0x2BF20 cleared), then the ticks.
#include <windows.h>
#include <time.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
#include <math.h>
#include "theater.h"
#include "third_party/minhook/include/MinHook.h"

void logf(const char* fmt, ...);
void ce_ragdoll_reset();                      // ce_ragdoll.cpp
float ce_ray_clear(const float from[3], const float by[3]);   // ce_ragdoll.cpp: the world's clear share of a ray
void film_dir(wchar_t* out);                  // botcore.cpp: %LOCALAPPDATA%\ProjectProvingGrounds\films

namespace {

const int KEEP = 25;
const uintptr_t RVA_LAUNCH = 0x2b406c0;          // MCC's launch block in halo1 (DAT_182b406c0, the same layout as halo2's)
const uint32_t LAUNCH_SIZE = 0x2bf30;
const uintptr_t RVA_SEEDS = 0x2ea74f4;           // halo1's two random seeds (u32 each), outside the game state
uint8_t* g_h1;
uint64_t g_key;                                  // FNV-1a of the launch block: the film key film.cpp files the bots under
wchar_t g_path[MAX_PATH];                        // the recording's file
FILE* g_out;
uint32_t g_ticks;
uint64_t g_bytes;

void prune(const wchar_t* dir) {
    wchar_t pat[MAX_PATH], names[64][40], p[MAX_PATH];
    swprintf_s(pat, L"%s\\*.cefilm", dir);
    int n = 0;
    WIN32_FIND_DATAW fd;
    HANDLE h = FindFirstFileW(pat, &fd);
    if (h == INVALID_HANDLE_VALUE) return;
    do { if (n < 64 && wcslen(fd.cFileName) < 40) wcscpy_s(names[n++], fd.cFileName); } while (FindNextFileW(h, &fd));
    FindClose(h);
    qsort(names, n, sizeof names[0], [](const void* x, const void* y) { return wcscmp((const wchar_t*)x, (const wchar_t*)y); });
    for (int i = 0; i + KEEP < n; i++) { swprintf_s(p, L"%s\\%s", dir, names[i]); DeleteFileW(p); }
}

void open_film() {
    wchar_t dir[MAX_PATH], path[MAX_PATH];
    film_dir(dir);
    wcscat_s(dir, L"\\ce");
    CreateDirectoryW(dir, nullptr);
    prune(dir);
    SYSTEMTIME t;
    GetLocalTime(&t);
    swprintf_s(path, L"%s\\%04d%02d%02d-%02d%02d%02d.cefilm", dir, t.wYear, t.wMonth, t.wDay, t.wHour, t.wMinute, t.wSecond);
    g_out = _wfopen(path, L"wb");
    g_ticks = 0;
    g_bytes = 0;
    if (!g_out) { logf("ce films: could not write %ls", path); return; }
    static const char MAGIC[12] = "PPGCEFILM3";
    uint32_t version = 4;                             // (4: each tick also has the two random seeds)
    fwrite(MAGIC, 1, sizeof MAGIC, g_out);
    fwrite(&version, 4, 1, g_out);
    uint64_t now = (uint64_t)time(nullptr);
    fwrite(&now, 8, 1, g_out);
    uint32_t size = LAUNCH_SIZE;
    fwrite(&size, 4, 1, g_out);
    static uint8_t block[LAUNCH_SIZE];
    __try { memcpy(block, g_h1 + RVA_LAUNCH, LAUNCH_SIZE); } __except (EXCEPTION_EXECUTE_HANDLER) { memset(block, 0, sizeof block); }
    memset(block + 0x2BF20, 0, 8);                    // (the film pointer: never a film's own)
    fwrite(block, 1, LAUNCH_SIZE, g_out);
    char scen[64] = {};                               // the map's scenario path (halo1+0x2B22F70, live Nov 13)
    __try { memcpy(scen, g_h1 + 0x2b22f70, 63); } __except (EXCEPTION_EXECUTE_HANDLER) {}
    fwrite(scen, 1, sizeof scen, g_out);
    uint32_t ticks = 0;                               // (the tick count, written at the end)
    fwrite(&ticks, 4, 1, g_out);
    g_key = 1469598103934665603ull;                   // the film key (film.cpp: the bots' commands): FNV-1a of the block
    for (uint32_t i = 0; i < LAUNCH_SIZE; i++) { g_key ^= block[i]; g_key *= 1099511628211ull; }
    wcscpy_s(g_path, path);
    logf("ce films: recording %ls", path);
}

// the CE map names MCC shows, by scenario
const wchar_t* map_title(const char* scen) {
    static const struct { const char* s; const wchar_t* t; } M[] = {
        {"beavercreek", L"Battle Creek"}, {"bloodgulch", L"Blood Gulch"}, {"boardingaction", L"Boarding Action"},
        {"carousel", L"Derelict"}, {"chillout", L"Chill Out"}, {"damnation", L"Damnation"}, {"dangercanyon", L"Danger Canyon"},
        {"deathisland", L"Death Island"}, {"gephyrophobia", L"Gephyrophobia"}, {"hangemhigh", L"Hang 'Em High"},
        {"icefields", L"Ice Fields"}, {"infinity", L"Infinity"}, {"longest", L"Longest"}, {"prisoner", L"Prisoner"},
        {"putput", L"Chiron TL-34"}, {"ratrace", L"Rat Race"}, {"sidewinder", L"Sidewinder"}, {"timberland", L"Timberland"},
        {"wizard", L"Wizard"}};
    const char* last = strrchr(scen, '\\');
    last = last ? last + 1 : scen;
    for (auto& m : M) if (!_stricmp(last, m.s)) return m.t;
    static wchar_t other[64];
    swprintf_s(other, L"%hs", last);
    return other;
}

// --- MCC's Theater: the film's metadata (Halo 3's 20 getters, as h2.cpp's), from the .mov header
struct CeFilmMeta {
    void** vt;
    uint64_t when;
    uint32_t ticks;
    uint8_t block[0x400];                         // the launch block's head: map block +0x14, author +0xF0, variant +0x300
    wchar_t title[64], desc[128];
    uint8_t zero[64];
};
void __fastcall cm_free(CeFilmMeta* m) { free(m); }
const wchar_t* __fastcall cm_title(CeFilmMeta* m) { return m->title; }
const wchar_t* __fastcall cm_desc(CeFilmMeta* m) { return m->desc; }
uint64_t __fastcall cm_author(CeFilmMeta* m) { return *(uint64_t*)(m->block + 0xF0); }
uint64_t __fastcall cm_date(CeFilmMeta* m) { return m->when; }
uint32_t __fastcall cm_length(CeFilmMeta* m) { return m->ticks / 30; }
uint16_t __fastcall cm_map_short(CeFilmMeta*) { return 0; }
uint8_t __fastcall cm_flag(CeFilmMeta*) { return 1; }
uint8_t __fastcall cm_flag2(CeFilmMeta*, uint32_t* a, uint8_t* b) { if (a) *a = 0xFFFFFFFFu; if (b) *b = 0; return 0; }
const char* __fastcall cm_build(CeFilmMeta*) { return "untracked version"; }
int __fastcall cm_kind(CeFilmMeta*) { return 0; }
int __fastcall cm_mode(CeFilmMeta*) { return 3; }
const void* __fastcall cm_static(CeFilmMeta* m) { return m->zero; }
int __fastcall cm_minus1(CeFilmMeta*) { return -1; }
const void* __fastcall cm_block15(CeFilmMeta* m) { return m->zero; }
const void* __fastcall cm_map_block(CeFilmMeta* m) { return m->block + 0x14; }   // {map id, 0x88880000, 0, 0}
uint8_t __fastcall cm_blob(CeFilmMeta*, void** p, uint64_t* n) { if (p) *p = nullptr; if (n) *n = 0; return 0; }
void __fastcall cm_fill(CeFilmMeta* m, uint8_t* out) {
    if (!out) return;
    out[0] = (uint8_t)(out[0] | 8);
    out[10] = 30;
    *(uint32_t*)(out + 0xC) = 3;
    memcpy(out + 0x14, m->block + 0x14, 16);
    memset(out + 0x24, 0, 16);
    *(uint16_t*)(out + 0x3C) = 0;
}
void* g_cm_vt[20] = {
    (void*)&cm_free, (void*)&cm_title, (void*)&cm_desc, (void*)&cm_author, (void*)&cm_date, (void*)&cm_length,
    (void*)&cm_map_short, (void*)&cm_flag, (void*)&cm_flag2, (void*)&cm_build, (void*)&cm_kind, (void*)&cm_mode,
    (void*)&cm_static, (void*)&cm_static, (void*)&cm_minus1, (void*)&cm_block15, (void*)&cm_map_block,
    (void*)&cm_blob, (void*)&cm_blob, (void*)&cm_fill};
const size_t HDR = 12 + 4 + 8 + 4;              // magic, version, time, block size; then the block, scenario[64], ticks

void* __fastcall ce_film_meta(void*, const uint8_t* d, uint32_t size) {
    if (!d || size < HDR + LAUNCH_SIZE + 64 + 4 || memcmp(d, "PPGCEFILM3", 10)) return nullptr;
    CeFilmMeta* m = (CeFilmMeta*)calloc(1, sizeof(CeFilmMeta));
    if (!m) return nullptr;
    m->vt = g_cm_vt;
    m->when = *(const uint64_t*)(d + 16);
    memcpy(m->block, d + HDR, sizeof m->block);
    const char* scen = (const char*)(d + HDR + LAUNCH_SIZE);
    m->ticks = *(const uint32_t*)(d + HDR + LAUNCH_SIZE + 64);
    wcsncpy_s(m->title, (const wchar_t*)(m->block + 0x300), 63);
    __time64_t tt = (__time64_t)m->when;
    struct tm lt;
    wchar_t when[64] = L"";
    if (!_localtime64_s(&lt, &tt)) wcsftime(when, 64, L"%A %B %d, %Y %H:%M:%S", &lt);
    const wchar_t* gt = m->title[0] == L'$' ? m->title + 1 : m->title;
    swprintf_s(m->desc, L"%s on %s, %s", gt, map_title(scen), when);
    if (m->desc[0] >= L'a' && m->desc[0] <= L'z') m->desc[0] -= 32;
    return m;
}

// --- playing a film: MCC's Theater launch puts the .mov's path at the launch block's film pointer (+0x2BF20), which
// MCC hands halo1 through FUN_1800939d0(engine, interface, params), which copies them into the block (live Nov 13:
// FUN_1800be590 is not on that path). The film's own block goes in instead (MCC's tail +0x2BF00.. kept: its pointers),
// so halo1 starts the same game as a normal one (same map, variant, players; film pointer clear), and each tick the
// recorded actions go in place of everyone's input (dequeue hook)
FILE* g_in;
bool g_playing;
uint32_t g_version;                              // the playing film's (3: no seeds in its ticks)
uint32_t g_reseeds;                              // ticks whose seeds the film had to put back (a measure of drift)
bool g_over;                                     // the film's input has ended (everyone stands)
bool g_ended;                                    // the film's game is ending (End Film, or 3 s after its input)
uint32_t g_length;                               // the film's ticks (its header)
long g_first;                                    // the file offset of its first tick
void snaps_free();
void local_back();                               // (the local player slot back: theater first person)
const uintptr_t RVA_GET_LAUNCH = 0x939d0;
const uint8_t GET_LAUNCH_PROLOGUE[11] = {0x40, 0x53, 0x56, 0x57, 0x48, 0x81, 0xEC, 0x50, 0x02, 0x00, 0x00};
typedef uint64_t(__fastcall* get_launch_fn)(void* engine, void* iface, uint8_t* params);
get_launch_fn g_get_launch_orig;
uint64_t __fastcall get_launch_hook(void* engine, void* iface, uint8_t* params) {
    __try {
        const char* film = params ? *(const char**)(params + 0x2BF20) : nullptr;
        if (film && !IsBadReadPtr(film, 4)) {
            FILE* f = nullptr;
            if (fopen_s(&f, film, "rb") == 0 && f) {
                char magic[12] = {};
                uint32_t ver = 0, size = 0;
                uint64_t when = 0;
                fread(magic, 1, 12, f); fread(&ver, 4, 1, f); fread(&when, 8, 1, f); fread(&size, 4, 1, f);
                static uint8_t block[LAUNCH_SIZE];
                if (!memcmp(magic, "PPGCEFILM3", 10) && size == LAUNCH_SIZE && fread(block, 1, LAUNCH_SIZE, f) == LAUNCH_SIZE) {
                    fseek(f, 64, SEEK_CUR);               // (scenario), the tick count: the ticks follow
                    g_length = 0;
                    fread(&g_length, 4, 1, f);
                    if (g_out) { fclose(g_out); g_out = nullptr; }
                    if (g_in) fclose(g_in);
                    g_in = f;
                    g_first = ftell(f);
                    g_version = ver;
                    g_reseeds = 0;
                    g_playing = true;
                    g_over = g_ended = false;
                    snaps_free();
                    g_ticks = 0;
                    g_key = 1469598103934665603ull;
                    for (uint32_t i = 0; i < LAUNCH_SIZE; i++) { g_key ^= block[i]; g_key *= 1099511628211ull; }
                    memcpy(block + 0x2BF00, params + 0x2BF00, LAUNCH_SIZE - 0x2BF00);   // (MCC's own tail)
                    memset(block + 0x2BF20, 0, 8);                                     // (no film: a game)
                    logf("ce films: MCC's Theater plays %s", film);
                    return g_get_launch_orig(engine, iface, block);
                }
                fclose(f);
            }
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) { logf("ce films: fault taking the film launch"); }
    return g_get_launch_orig(engine, iface, params);
}

void patch_meta() {
    void** slot = (void**)(g_h1 + 0x1899668 + 7 * 8);
    __try {
        if (*slot == (void*)&ce_film_meta) return;
        if (*slot != (void*)(g_h1 + 0x4cdd0)) { logf("ce films: data access slot 7 is not the decoded build's"); return; }
        DWORD old;
        if (!VirtualProtect(slot, 8, PAGE_READWRITE, &old)) return;
        *slot = (void*)&ce_film_meta;
        VirtualProtect(slot, 8, old, &old);
        logf("ce films: film metadata answered by botcore");
    } __except (EXCEPTION_EXECUTE_HANDLER) {}
}

// --- the Theater's controls (theater.cpp): halo1's own scripted camera, its game speed, and seeking by game states.
// The camera: camera_control (FUN_180B1524C, the script function) puts every local player's director on the scripted
// camera (FUN_180BE4124), which each frame reads the globals at halo1+0x1B87A20: mode 0 a camera at a point (or at an
// offset from an object, +0x34), mode 2 an object's first person view (FUN_180C525F8). Writing the director's function
// pointer from outside (Nov 13) left one frozen frame: camera_control also sets the cinematic flag and each director's
// blend, so it is called, never copied
#pragma pack(push, 1)
struct ce_director {
    uint8_t on, apply;
    int16_t mode;                                 // a word (FUN_180BE4124: movsx word): -1 none, 0 point, 1 animation, 2 first person, 3 orbit
    int16_t point, pad1;
    int32_t until;                                // a transition's end (game tick); a camera at once: now
    float pos[3], fwd[3], up[3], fov;
    uint32_t unit;                                // mode 0: pos is an offset from this object (-1: a world point)
};
#pragma pack(pop)
static_assert(sizeof(ce_director) == 0x38, "halo1+0x1B87A20..0x1B87A58");
const uintptr_t RVA_DIRECTOR = 0x1b87a20, RVA_CAMERA_CONTROL = 0xb1524c, RVA_TIME = 0x2e9fd68;
const uintptr_t RVA_PLAYERS = 0x1C40480, RVA_OBJECTS = 0x1C42248, RVA_POOL = 0x2D9CDF8, RVA_END_GAME = 0x2e9fdfc;
const uint8_t CAMERA_CONTROL_PROLOGUE[16] = {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x6C, 0x24, 0x10, 0x48, 0x89, 0x74, 0x24, 0x18, 0x57};
const uint32_t F_DEAD = 0x10000;                  // object +0x10 (ce_ragdoll.cpp)
bool g_cam;                                       // camera_control on
bool g_eject;                                     // End Film pressed: the game ends at the next game state step
uint32_t g_body[16];                              // each player's last body (a dead one's: the corpse)
float g_speed = 1;

uint8_t* player_at(int i) {
    uint8_t* hdr = *(uint8_t**)(g_h1 + RVA_PLAYERS);
    if (!hdr || i < 0 || i >= *(int16_t*)(hdr + 0x20)) return nullptr;
    uint8_t* p = hdr + *(int32_t*)(hdr + 0x34) + (uintptr_t)i * *(uint16_t*)(hdr + 0x22);
    return *(uint16_t*)p ? p : nullptr;
}

uint8_t* object_at(uint32_t handle) {
    uint8_t* hdr = *(uint8_t**)(g_h1 + RVA_OBJECTS);
    if (!hdr || handle == 0xFFFFFFFFu || !handle) return nullptr;
    uint32_t i = handle & 0xFFFF;
    if ((int)i >= *(int16_t*)(hdr + 0x20)) return nullptr;
    uint8_t* e = hdr + *(int32_t*)(hdr + 0x34) + i * 12;
    if (*(uint16_t*)e != (handle >> 16) || *(int32_t*)(e + 8) == -1) return nullptr;
    return *(uint8_t**)(g_h1 + RVA_POOL) + 0x34 + *(int32_t*)(e + 8);
}

// the player's body: its unit, or once it died, that unit's corpse while it lasts
uint32_t body_of(int i) {
    uint8_t* p = player_at(i);
    uint32_t unit = p ? *(uint32_t*)(p + 0x64) : 0xFFFFFFFFu;
    if (object_at(unit)) g_body[i] = unit;
    return i >= 0 && i < 16 && object_at(g_body[i]) ? g_body[i] : 0xFFFFFFFFu;
}

void camera_control(bool on) {
    // (on: again whenever local player 0's director is off the scripted camera: the map's start put it back after
    // our first call, film27)
    if (g_cam == on && (!on || *(void**)(g_h1 + 0x2d9b970) == (void*)(g_h1 + 0xbe4124))) return;
    if (memcmp(g_h1 + RVA_CAMERA_CONTROL, CAMERA_CONTROL_PROLOGUE, sizeof CAMERA_CONTROL_PROLOGUE)) {
        static bool said;
        if (!said) { said = true; logf("ce theater: camera_control not the decoded build: the game's camera stays"); }
        return;
    }
    ((void(__fastcall*)(char))(g_h1 + RVA_CAMERA_CONTROL))(on ? 1 : 0);
    g_cam = on;
}

void end_game(const char* why) {
    static const uint8_t WON[12] = {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x6C, 0x24, 0x10, 0x48, 0x89};
    g_ended = true;
    __try {
        local_back();
        camera_control(false);
        if (memcmp(g_h1 + 0xac3854, WON, sizeof WON)) { logf("ce films: game end not the decoded build"); return; }
        ((void(__fastcall*)())(g_h1 + 0xac3854))();   // game_won (FUN_180AC3854): its results, then MCC goes on
        logf("ce films: %s: game ended", why);
    } __except (EXCEPTION_EXECUTE_HANDLER) { logf("ce films: fault ending the film's game"); }
}

bool th_playing() { return g_playing && !g_ended && g_h1; }
uint32_t th_now() { return g_ticks; }
uint32_t th_length() { return g_length; }

void th_players(th_player out[16]) {
    memset(out, 0, sizeof(th_player) * 16);
    __try {
        for (int i = 0; i < 16; i++) {
            uint8_t* p = player_at(i);
            if (!p) continue;
            out[i].used = true;
            wcsncpy_s(out[i].name, (const wchar_t*)(p + 0x20), 15);
            out[i].team = *(int32_t*)(p + 0x4C);
            uint8_t* o = object_at(*(uint32_t*)(p + 0x64));
            out[i].alive = o && !(*(uint32_t*)(o + 0x10) & F_DEAD);
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {}
}

bool th_focus(int player, float pos[3], float fwd[3]) {
    __try {
        uint8_t* o = object_at(body_of(player));
        if (!o) return false;
        memcpy(pos, o + 0x18, 12);                // object +0x18 position, +0x30 forward
        memcpy(fwd, o + 0x30, 12);
        return true;
    } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}

// First person is the game's own camera (FUN_180C5263C: the player's gun and HUD), with local player 0's control
// ([halo1+0x2D8FE70] + 0x170: its unit, +0x17C yaw, +0x180 pitch) pointed at the followed unit and that unit's aim
// (object +0x21C, the vector the game's first person camera of a unit reads, FUN_180C525F8), every frame just before
// the directors run (FUN_180B14380, after the frame's ticks, before the frame is drawn). The scripted camera's own
// first person (mode 2) has neither gun nor HUD. The viewer's input never reaches the game in a film, so the control's
// facing is free to set; the unit goes back to the player's own when the view leaves first person
const uintptr_t RVA_PLAYER_CONTROL = 0x2d8fe70, RVA_LOCAL_PLAYERS = 0x2ea2d90, RVA_DIRECTOR_UPDATE = 0xb14380;
const uint8_t DIRECTOR_UPDATE_PROLOGUE[16] = {0x48, 0x8B, 0xC4, 0x48, 0x89, 0x58, 0x10, 0x48, 0x89, 0x70, 0x18, 0x55, 0x57, 0x41, 0x54, 0x41};
volatile uint32_t g_fp_unit = 0xFFFFFFFFu;        // the local view on this unit (the game's camera); none: ours
bool g_lent;                                      // local player 0's control holds another unit
// The HUD (FUN_180C504C4) and the first person gun (FUN_180B2A2C4) belong to the player in local player 0's slot
// ([halo1+0x2EA2D90] + 0xB8, a player handle). While the view is another player's eyes that slot holds them from the
// directors (end of the frame's game update) to the drawing, and the real one goes back at the start of the next
// frame's update (frame_ticks_hook) and before any game state step, so no tick and no kept state ever sees it
uint32_t g_real_local = 0xFFFFFFFFu;             // the slot's own player while it holds another
typedef void(__fastcall* director_update_fn)(float dt);
director_update_fn g_director_update_orig;

void local_back() {
    if (g_real_local == 0xFFFFFFFFu) return;
    uint8_t* lp = *(uint8_t**)(g_h1 + RVA_LOCAL_PLAYERS);
    if (lp) *(uint32_t*)(lp + 0xb8) = g_real_local;
    g_real_local = 0xFFFFFFFFu;
}

void fp_apply() {
    local_back();
    uint8_t* pc = *(uint8_t**)(g_h1 + RVA_PLAYER_CONTROL);
    if (!pc) return;
    uint32_t u = g_fp_unit;
    uint8_t* o = u != 0xFFFFFFFFu && g_playing && !g_ended ? object_at(u) : nullptr;
    if (o) {
        const float* a = (const float*)(o + 0x21c);
        float yaw = atan2f(a[1], a[0]), z = a[2] > 1 ? 1 : a[2] < -1 ? -1 : a[2];
        if (yaw < 0) yaw += 6.2831853f;
        *(uint32_t*)(pc + 0x170) = u;
        *(float*)(pc + 0x17c) = yaw;
        *(float*)(pc + 0x180) = asinf(z);
        g_lent = true;
        uint8_t* lp = *(uint8_t**)(g_h1 + RVA_LOCAL_PLAYERS);
        for (int i = 0; lp && i < 16; i++) {          // the followed unit's player into the local slot
            uint8_t* p = player_at(i);
            if (!p || *(uint32_t*)(p + 0x64) != u) continue;
            uint32_t h = ((uint32_t)*(uint16_t*)p << 16) | (uint32_t)i, own = *(uint32_t*)(lp + 0xb8);
            if (h != own) { g_real_local = own; *(uint32_t*)(lp + 0xb8) = h; }
            break;
        }
    } else if (g_lent) {                              // (back to the player's own unit)
        uint8_t* lp = *(uint8_t**)(g_h1 + RVA_LOCAL_PLAYERS);
        uint8_t* p = lp ? player_at(*(int32_t*)(lp + 0xb8) & 0xFFFF) : nullptr;
        if (p) *(uint32_t*)(pc + 0x170) = *(uint32_t*)(p + 0x64);
        g_lent = false;
    }
}

// The orbit camera (theater.cpp's offset from the followed body) stops short of the world between the body and it, as
// Halo 3's does (film33: behind a player at a wall the camera stood in the rock). Here, on the game thread, with the
// bodies' collision test (ce_ragdoll.cpp), just before the directors read it
volatile float g_orbit_off[3];
volatile float g_free_want[3], g_free_at[3];    // the free camera: where theater.cpp wants it, where it is (the orbit's too)
volatile bool g_free_on;                          // the free camera is up
volatile uint32_t g_orbit_unit = 0xFFFFFFFFu;

void orbit_apply() {
    uint32_t u = g_orbit_unit;
    ce_director* d = (ce_director*)(g_h1 + RVA_DIRECTOR);
    uint8_t* o = u != 0xFFFFFFFFu && g_cam && d->mode == 0 && d->unit == u ? object_at(u) : nullptr;
    if (!o) return;
    const float* at = (const float*)(o + 0x18);
    float off[3] = {g_orbit_off[0], g_orbit_off[1], g_orbit_off[2]};
    float from[3] = {at[0], at[1], at[2] + TH_LOOK_AT}, by[3] = {off[0], off[1], off[2] - TH_LOOK_AT};
    float t = ce_ray_clear(from, by), k = t < 1 ? fmaxf(0.08f, t - 0.1f) : 1;
    d->pos[0] = by[0] * k;
    d->pos[1] = by[1] * k;
    d->pos[2] = by[2] * k + TH_LOOK_AT;
    for (int i = 0; i < 3; i++) g_free_at[i] = from[i] + by[i] * k;   // (where it is: a free camera starts there)
}

// The free camera stops at the map's walls, floors and ceilings and slides along them (it flew through them, Nov 13;
// Halo 3's flying camera does not): each frame it moves from where it was
// toward where theater.cpp wants it, one axis at a time, each step stopping 0.05 u short of the world

void free_apply() {
    ce_director* d = (ce_director*)(g_h1 + RVA_DIRECTOR);
    if (!g_free_on || !g_cam || d->mode != 0 || d->unit != 0xFFFFFFFFu) return;
    float at[3] = {g_free_at[0], g_free_at[1], g_free_at[2]};
    const float MARGIN = 0.05f;
    for (int k = 0; k < 3; k++) {
        float step = g_free_want[k] - at[k];
        if (fabsf(step) < 1e-5f) continue;
        float sign = step > 0 ? 1.0f : -1.0f, by[3] = {0, 0, 0};
        by[k] = step + sign * MARGIN;                 // (the margin is part of the ray)
        float t = ce_ray_clear(at, by);
        if (t >= 1) { at[k] += step; continue; }
        float moved = by[k] * t - sign * MARGIN;      // up to the wall, less the margin, never backward
        if (moved * sign > 0) at[k] += moved;
    }
    for (int k = 0; k < 3; k++) { g_free_at[k] = at[k]; d->pos[k] = at[k]; }
}

void __fastcall director_update_hook(float dt) {
    __try { if (g_playing || g_lent) fp_apply(); if (g_playing) { orbit_apply(); free_apply(); } } __except (EXCEPTION_EXECUTE_HANDLER) {}
    g_director_update_orig(dt);
}

void th_camera(int mode, int player, const float pos[3], float yaw, float pitch, float fov) {
    __try {
        if (mode == TH_GAME || !th_playing()) { g_fp_unit = 0xFFFFFFFFu; g_free_on = false; camera_control(false); return; }
        uint32_t body = player >= 0 ? body_of(player) : 0xFFFFFFFFu;
        if (mode == TH_FIRST && body != 0xFFFFFFFFu && g_director_update_orig) {
            g_fp_unit = body;
            g_free_on = false;
            camera_control(false);
            return;
        }
        g_fp_unit = 0xFFFFFFFFu;
        camera_control(true);
        if (!g_cam) return;
        ce_director* d = (ce_director*)(g_h1 + RVA_DIRECTOR);
        if (mode == TH_FIRST && body != 0xFFFFFFFFu) {    // (no director hook: the scripted camera's eyes)
            if (d->mode != 2 || d->unit != body) { d->unit = body; d->mode = 2; d->apply = 1; }
            return;
        }
        if (mode == TH_THIRD && body == 0xFFFFFFFFu) return;
        uint8_t* tg = *(uint8_t**)(g_h1 + RVA_TIME);
        float cy = cosf(yaw), sy = sinf(yaw), cp = cosf(pitch), sp = sinf(pitch);
        float f[3] = {cy * cp, sy * cp, sp}, u[3] = {-cy * sp, -sy * sp, cp};
        if (mode == TH_THIRD) {                        // (the director hook pulls it in front of walls)
            memcpy((void*)g_orbit_off, pos, 12);
            g_orbit_unit = body;
            g_free_on = false;
        } else {                                       // (free: the director hook moves it, stopping at walls)
            g_orbit_unit = 0xFFFFFFFFu;
            if (!g_free_on) { memcpy((void*)g_free_at, pos, 12); memcpy(d->pos, pos, 12); }
            memcpy((void*)g_free_want, pos, 12);
            g_free_on = true;
        }
        memcpy(d->fwd, f, 12);
        memcpy(d->up, u, 12);
        d->fov = fov;
        d->until = tg ? *(int32_t*)(tg + 0xc) : 0;
        d->unit = mode == TH_THIRD ? body : 0xFFFFFFFFu;
        if (d->mode != 0) { d->mode = 0; d->apply = 1; }
    } __except (EXCEPTION_EXECUTE_HANDLER) {}
}

// --- seeking: halo1's whole game state is one block ([halo1+0x2B259C0], 0x5C0000 bytes; core_save writes it to
// core.bin, core_load puts it back between FUN_180BE8A28 and FUN_180BE8A64, both in the main loop's game state step
// FUN_180AC2830). A film keeps one every 10 s as it plays (its empty 4 KB pages left out), each with the film's place:
// a seek back puts the last one before the target back, then the film runs fast to the target; a seek ahead just runs
// fast. (Halo 3's own Theater goes back the same way: from its last state, forward)
const uintptr_t RVA_STATE = 0x2b259c0, RVA_STATE_OPS = 0xac2830, RVA_LOAD_BEFORE = 0xbe8a28, RVA_LOAD_AFTER = 0xbe8a64;
const uint32_t STATE_SIZE = 0x5c0000, PAGE = 4096, PAGES = STATE_SIZE / PAGE;
const uint8_t STATE_OPS_PROLOGUE[10] = {0x48, 0x89, 0x5C, 0x24, 0x08, 0x57, 0x48, 0x83, 0xEC, 0x20};
const uint32_t SNAP_EVERY = 300, FIRST_SNAP = 30, NONE = 0xFFFFFFFFu;
const float SEEK_SPEED = 12.0f;
struct snap { uint32_t tick; long at; uint8_t used[PAGES]; uint8_t* data; };
snap* g_snaps[1024];                              // by tick / SNAP_EVERY
volatile uint32_t g_seek_to = NONE;              // a seek asked for (theater.cpp)
uint32_t g_ff_to = NONE;                         // running fast to this tick
typedef uint64_t(__fastcall* state_ops_fn)();
state_ops_fn g_state_ops_orig;

void snaps_free() {
    for (snap*& s : g_snaps) if (s) { free(s->data); free(s); s = nullptr; }
    g_seek_to = g_ff_to = NONE;
}

void snap_take(const uint8_t* state, uint32_t k) {
    snap* s = (snap*)calloc(1, sizeof(snap));
    if (!s) return;
    uint32_t n = 0;
    for (uint32_t p = 0; p < PAGES; p++) {
        const uint64_t* q = (const uint64_t*)(state + p * PAGE);
        uint64_t any = 0;
        for (uint32_t w = 0; w < PAGE / 8 && !any; w++) any |= q[w];
        s->used[p] = any != 0;
        n += s->used[p];
    }
    s->data = (uint8_t*)malloc((size_t)n * PAGE);
    if (!s->data) { free(s); return; }
    for (uint32_t p = 0, j = 0; p < PAGES; p++)
        if (s->used[p]) memcpy(s->data + (size_t)j++ * PAGE, state + p * PAGE, PAGE);
    s->tick = g_ticks;
    s->at = ftell(g_in);
    g_snaps[k] = s;
    static int said;
    if (said++ < 3) logf("ce theater: game state kept at tick %u (%u of %u pages)", g_ticks, n, PAGES);
}

void snap_put(uint8_t* state, const snap* s) {
    ((void(__fastcall*)())(g_h1 + RVA_LOAD_BEFORE))();
    for (uint32_t p = 0, j = 0; p < PAGES; p++) {
        if (s->used[p]) memcpy(state + p * PAGE, s->data + (size_t)j++ * PAGE, PAGE);
        else memset(state + p * PAGE, 0, PAGE);
    }
    ((void(__fastcall*)())(g_h1 + RVA_LOAD_AFTER))();
    fseek(g_in, s->at, SEEK_SET);
    g_ticks = s->tick;
    g_over = false;
    ce_ragdoll_reset();
}

uint64_t __fastcall state_ops_hook() {
    __try { local_back(); } __except (EXCEPTION_EXECUTE_HANDLER) {}
    if (g_playing && g_eject && !g_ended) { g_eject = false; end_game("End Film"); }
    uint64_t r = g_state_ops_orig();
    if (!g_playing || g_ended || (r & 0xFF) || !g_in) return r;
    __try {
        uint8_t* state = *(uint8_t**)(g_h1 + RVA_STATE);
        uint8_t* tg = *(uint8_t**)(g_h1 + RVA_TIME);
        if (!state || !tg) return r;
        uint32_t to = g_seek_to;
        if (to != NONE) {
            g_seek_to = NONE;
            snap* best = nullptr;                 // the last state at or before the target (none: the first one)
            for (snap* s : g_snaps) if (s && s->tick <= to && (!best || s->tick > best->tick)) best = s;
            if (!best) for (snap* s : g_snaps) if (s && (!best || s->tick < best->tick)) best = s;
            if (best && (to < g_ticks || best->tick > g_ticks)) {
                uint32_t from = g_ticks;
                snap_put(state, best);
                logf("ce theater: seek %u -> %u: game state of tick %u", from, to, best->tick);
            }
            g_ff_to = g_ticks < to ? to : NONE;
        }
        if (g_ff_to != NONE && (g_ticks >= g_ff_to || g_over)) g_ff_to = NONE;
        // (not before 1 s: tick 1's state had no local player yet, and putting it back crashed halo1 reading player
        // 0xFFFF, FUN_180AA0E68, a rewind Nov 13)
        uint32_t k = g_ticks / SNAP_EVERY;
        if (g_ticks >= FIRST_SNAP && k < 1024 && !g_snaps[k] && !g_over) snap_take(state, k);
    } __except (EXCEPTION_EXECUTE_HANDLER) { logf("ce theater: fault in the game state step"); }
    return r;
}

// --- speed: MCC runs halo1 as a network host (halo1+0x2B236E0 = 2), where the game speed is fixed at 1
// (FUN_180AB1060), so game_speed does nothing (film27: ticks went on at 30 a second at 0). How many ticks a frame runs
// comes from FUN_180AB07D8(frame seconds, peek) in game_frame (FUN_180AB0D10); a film scales it: 0 paused (the
// directors still update every frame, so the camera moves), E 4x, a seek 12x. A seek asked for while paused gets one
// tick (the game state step runs between ticks)
const uintptr_t RVA_FRAME_TICKS = 0xab07d8;
const uint8_t FRAME_TICKS_PROLOGUE[16] = {0x48, 0x8B, 0xC4, 0x48, 0x89, 0x58, 0x10, 0x48, 0x89, 0x68, 0x18, 0x48, 0x89, 0x70, 0x20, 0x57};
typedef int(__fastcall* frame_ticks_fn)(float dt, char peek);
frame_ticks_fn g_frame_ticks_orig;
float g_tick_debt;

int __fastcall frame_ticks_hook(float dt, char peek) {
    if (!peek) __try { local_back(); } __except (EXCEPTION_EXECUTE_HANDLER) {}   // (the frame's update starts: the real local player)
    int n = g_frame_ticks_orig(dt, peek);
    if (!g_playing || g_ended || peek) return n;
    float s = g_ff_to != NONE ? SEEK_SPEED : g_speed;
    // paused: the time since the last tick (time globals +0x20, what the drawing blends the last two ticks by) held
    // where the pause began; it kept running round 0..1/30 s and paused players shook between two places (Nov 13)
    static bool held;
    static float hold;
    __try {
        float* since = (float*)(*(uint8_t**)(g_h1 + RVA_TIME) + 0x20);
        if (s <= 0 && g_seek_to == NONE) { if (!held) { hold = *since; held = true; } *since = hold; }
        else held = false;
    } __except (EXCEPTION_EXECUTE_HANDLER) {}
    if (g_seek_to != NONE && s <= 0) return 1;
    if (s == 1.0f || n <= 0) return n;
    g_tick_debt += n * s;
    int k = (int)g_tick_debt;
    g_tick_debt -= k;
    return k;
}

void th_speed(float s) { g_speed = s; }
void th_seek(uint32_t tick) { g_seek_to = tick; }
bool th_seeking() { return g_seek_to != NONE || g_ff_to != NONE; }
void th_eject() { g_eject = true; }

// the free camera where it stopped (walls), for theater.cpp to move on from
void th_where(float pos[3]) { if (g_free_on || g_orbit_unit != 0xFFFFFFFFu) for (int k = 0; k < 3; k++) pos[k] = g_free_at[k]; }

const th_backend THEATER = {th_playing, th_now, th_length, th_players, th_focus, th_camera, th_speed, th_seek, th_seeking, th_eject, th_where, TH_LOOK_AT};

}  // namespace

const th_backend* ce_theater() { return &THEATER; }

// ce_ragdoll.cpp's snapshot hook: the unit whose eyes the Theater looks through (its body and guns are not drawn:
// the game hides only its own local player's), or -1
uint32_t ce_theater_eyes() { return g_playing && !g_ended ? g_fp_unit : 0xFFFFFFFFu; }

// MCC's content scan (mcc_theater.cpp) calls this first
void ce_film_meta_ensure() { if (g_h1) patch_meta(); }

// botcore's dequeue hook. Live: after the bots' actions went in, this tick's input of every player is recorded. A film:
// the recorded actions replace them (true: the actions were replaced)
bool ce_film_actions(uint32_t tick, uint8_t* actions, size_t size) {
    uint32_t* seeds = (uint32_t*)(g_h1 + RVA_SEEDS);
    if (g_playing) {
        __try {
            uint32_t t = 0, s[2];
            uint16_t len = 0;
            long at = g_in ? ftell(g_in) : 0;
            if (g_over || !g_in || fread(&t, 4, 1, g_in) != 1 || fread(&len, 2, 1, g_in) != 1 || len > size ||
                (g_version >= 4 && fread(s, 4, 2, g_in) != 2)) {
                if (!g_over) { g_over = true; logf("ce films: the film's input ends at tick %u", g_ticks); }
                if (g_in) fseek(g_in, at, SEEK_SET);  // (where a seek back finds it)
                memset(actions, 0, size);             // (past the end: everyone stands)
                return true;
            }
            memset(actions, 0, size);
            fread(actions, 1, len, g_in);
            if (g_version >= 4) {                     // the match's random numbers from here on
                if (seeds[0] != s[0] || seeds[1] != s[1]) g_reseeds++;
                seeds[0] = s[0];
                seeds[1] = s[1];
            }
            g_ticks++;
        } __except (EXCEPTION_EXECUTE_HANDLER) {}
        return true;
    }
    if (!g_out) open_film();
    if (!g_out) return false;
    size_t n = size;
    while (n && !actions[n - 1]) n--;                 // (the empty slots after the last live player)
    uint16_t len = (uint16_t)n;
    fwrite(&tick, 4, 1, g_out);
    fwrite(&len, 2, 1, g_out);
    fwrite(seeds, 4, 2, g_out);
    fwrite(actions, 1, n, g_out);
    g_ticks++;
    g_bytes += 14 + n;
    if ((g_ticks % 1800) == 0) { fflush(g_out); logf("ce films: %u ticks, %llu bytes", g_ticks, (unsigned long long)g_bytes); }
    return false;
}

// botcore's tick hook, on the game thread: the debug positions every 5 s (seeks and replays compare them). (It used to
// end the game 3 s after the film's input with game_won; the Theater now holds the last frame)
void ce_film_tick_end() {
    if (g_playing && !g_ended && g_ticks % 150 == 0) __try {   // (the same tick after a seek must show the same places)
        static uint32_t said;
        if (said++ < 200) {
            char line[256];
            int n = snprintf(line, sizeof line, "ce theater: tick %u", g_ticks);
            for (int i = 0; i < 4; i++) {
                uint8_t* p = player_at(i);
                uint8_t* o = p ? object_at(*(uint32_t*)(p + 0x64)) : nullptr;
                if (o) n += snprintf(line + n, sizeof line - n, " p%d %.3f,%.3f,%.3f", i, ((float*)(o + 0x18))[0], ((float*)(o + 0x18))[1], ((float*)(o + 0x18))[2]);
            }
            logf("%s", line);
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {}
    // (the film's end no longer ends its game: the Theater pauses on the last frame, Nov 13; End Film ends it)
}

// the film's key and its own tick (both the same in a match and in its film), for film.cpp's bot commands; 0: none
uint64_t ce_film_key() { return (g_out || g_playing) ? g_key : 0; }
uint32_t ce_film_tick() { return g_ticks; }
bool ce_film_playing() { return g_playing; }

// back in the menus: the film ends (a recording is closed, its tick count written, and a copy put where MCC's Theater
// looks: Temporary\UserContent\Halo1\Movie\asq_<map>_<id>_<time>.mov)
void ce_film_end() {
    if (g_playing) {
        g_playing = false;
        if (g_in) { fclose(g_in); g_in = nullptr; }
        snaps_free();
        if (g_cam) {                                  // (left by MCC's Quit: the map is gone, so only the flags)
            __try { **(uint8_t**)(g_h1 + 0x1c410d8) = 0; ((ce_director*)(g_h1 + RVA_DIRECTOR))->on = 0; } __except (EXCEPTION_EXECUTE_HANDLER) {}
            g_cam = false;
        }
        g_eject = false;
        g_fp_unit = 0xFFFFFFFFu;
        g_lent = false;
        g_real_local = 0xFFFFFFFFu;                   // (the map is gone: its next game makes its own)
        memset(g_body, 0, sizeof g_body);
        logf("ce films: film over (%u ticks the recorded random seeds differed from the game's)", g_reseeds);
        return;
    }
    if (!g_out) return;
    fseek(g_out, (long)(HDR + LAUNCH_SIZE + 64), SEEK_SET);
    fwrite(&g_ticks, 4, 1, g_out);
    fclose(g_out);
    g_out = nullptr;
    logf("ce films: film closed, %u ticks, %llu bytes", g_ticks, (unsigned long long)g_bytes);
    if (g_ticks < 300) return;                        // (under 10 s: not worth a Theater entry)
    wchar_t home[MAX_PATH], movie[MAX_PATH], mov[MAX_PATH];
    if (!GetEnvironmentVariableW(L"USERPROFILE", home, MAX_PATH)) return;
    swprintf_s(movie, L"%s\\AppData\\LocalLow\\MCC\\Temporary\\UserContent\\Halo1", home);
    CreateDirectoryW(movie, nullptr);
    wcscat_s(movie, L"\\Movie");
    CreateDirectoryW(movie, nullptr);
    char scen[64] = {};
    FILE* f = _wfopen(g_path, L"rb");
    if (f) { fseek(f, (long)(HDR + LAUNCH_SIZE), SEEK_SET); fread(scen, 1, 63, f); fclose(f); }
    const char* last = strrchr(scen, '\\');
    char shortmap[8] = {};
    strncpy_s(shortmap, last ? last + 1 : "film", 7);
    swprintf_s(mov, L"%s\\asq_%hs_%08X_%08X.mov", movie, shortmap, GetTickCount(), (DWORD)time(nullptr));
    if (CopyFileW(g_path, mov, TRUE)) logf("ce films: for the Theater %ls", mov);
    else logf("ce films: could not put the film in the Theater (%lu)", GetLastError());
}

bool ce_film_install(uint8_t* h1) {
    ce_film_end();
    if (g_h1 && g_get_launch_orig) MH_RemoveHook(g_h1 + RVA_GET_LAUNCH);
    if (g_h1 && g_state_ops_orig) MH_RemoveHook(g_h1 + RVA_STATE_OPS);
    if (g_h1 && g_frame_ticks_orig) MH_RemoveHook(g_h1 + RVA_FRAME_TICKS);
    if (g_h1 && g_director_update_orig) MH_RemoveHook(g_h1 + RVA_DIRECTOR_UPDATE);
    g_h1 = h1;
    g_get_launch_orig = nullptr;
    g_state_ops_orig = nullptr;
    g_frame_ticks_orig = nullptr;
    g_director_update_orig = nullptr;
    patch_meta();
    __try {                                           // (the Theater's seeking and speed; without them a film still plays)
        if (memcmp(h1 + RVA_STATE_OPS, STATE_OPS_PROLOGUE, sizeof STATE_OPS_PROLOGUE)) logf("ce theater: game state step not the decoded build: no seeking");
        else if (MH_CreateHook(h1 + RVA_STATE_OPS, (void*)&state_ops_hook, (void**)&g_state_ops_orig) != MH_OK) logf("ce theater: game state hook failed");
        if (memcmp(h1 + RVA_FRAME_TICKS, FRAME_TICKS_PROLOGUE, sizeof FRAME_TICKS_PROLOGUE)) logf("ce theater: frame ticks not the decoded build: no pause or fast forward");
        else if (MH_CreateHook(h1 + RVA_FRAME_TICKS, (void*)&frame_ticks_hook, (void**)&g_frame_ticks_orig) != MH_OK) logf("ce theater: frame ticks hook failed");
        if (memcmp(h1 + RVA_DIRECTOR_UPDATE, DIRECTOR_UPDATE_PROLOGUE, sizeof DIRECTOR_UPDATE_PROLOGUE)) logf("ce theater: director update not the decoded build: first person without HUD");
        else if (MH_CreateHook(h1 + RVA_DIRECTOR_UPDATE, (void*)&director_update_hook, (void**)&g_director_update_orig) != MH_OK) { g_director_update_orig = nullptr; logf("ce theater: director update hook failed"); }
    } __except (EXCEPTION_EXECUTE_HANDLER) {}
    __try {
        if (memcmp(h1 + RVA_GET_LAUNCH, GET_LAUNCH_PROLOGUE, sizeof GET_LAUNCH_PROLOGUE)) { logf("ce films: launch not the decoded build: no playing films"); return true; }
    } __except (EXCEPTION_EXECUTE_HANDLER) { return true; }
    if (MH_CreateHook(h1 + RVA_GET_LAUNCH, (void*)&get_launch_hook, (void**)&g_get_launch_orig) != MH_OK) logf("ce films: launch hook failed");
    return true;
}
