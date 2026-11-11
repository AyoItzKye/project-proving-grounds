// spawnhook.cpp: Reach's multiplayer spawn check and respawn handler, hooked so bots respawn in Invasion and Firefight
// (reach.cpp hr_bot_solo_spawn, hr_bot_spawn_point).
//
// FUN_1800ffabc(player) (ghidra/hr_spawnchk.c) is the spawn check of the players update's spawn loop
// (ghidra/hr_players_update.c): player index into the 0x490 players, the respawn time +0x1BC. Before it answers,
// hr_bot_solo_spawn clears a bot's co-op spawning byte, so it never waits for a choice it cannot make (it spawns on
// time, then reach.cpp hr_spawn_moves moves it to the spawn the brain picked).
// FUN_18004633c(player) (ghidra/hr_respawn_tick.c) is the per-player respawn handler the players update runs for each
// player after the spawn loop: before it, hr_bot_spawn_point gives a dead Firefight bot the spawn point the person's
// death screen gives him.
// On whenever haloreach.dll is loaded, and only over the functions' own first bytes (MCC 1.3528's haloreach.dll; another
// build is left alone and logged once).
// GitHub #22, the person heard every bot's respawn countdown beep (Reach, ODST, Halo 3). The respawn handler (Reach
// FUN_18004633c, ODST FUN_1800fe0bc, Halo 3 FUN_1800e3e74) beeps at 3, 2 and 1 s left and on the last tick with a
// 2D interface sound (Reach FUN_1800bada8, ODST FUN_180185ca4, Halo 3 FUN_180158244, the same code as ODST's) for a
// player whose machine is this one (Reach
// FUN_1800532d8, ODST FUN_180108044: player +0x14 machine identifier against the local machine's). A bot carries the
// host's machine (reach.cpp hr_add_bot, odst.cpp od_add_bot: its shots do damage only so), so each of its countdowns
// beeped on the person's speakers. While a bot's respawn handler runs, the interface sound plays nothing; a person's
// own countdown is untouched.
#include <windows.h>
#include <string.h>
#include "shared.h"
#include "third_party/minhook/include/MinHook.h"

extern hb_shared* g_shm;
void logf(const char* fmt, ...);
void hr_bot_solo_spawn(uint32_t player);
void hr_bot_spawn_point(uint32_t player);

typedef char(__fastcall* should_spawn_fn)(uint32_t player);
typedef uint64_t(__fastcall* respawn_tick_fn)(uint32_t player);
static should_spawn_fn o_hr_should_spawn;
static respawn_tick_fn o_hr_respawn_tick;
static const uint8_t HR_SHOULD_SPAWN_HEAD[8] = { 0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74 };
static const uint8_t HR_RESPAWN_TICK_HEAD[8] = { 0x48, 0x8B, 0xC4, 0x48, 0x89, 0x58, 0x08, 0x48 };
typedef void(__fastcall* hr_ui_sound_fn)(uint32_t sound, float volume, char flag);   // (ecx, xmm1, r8b)
typedef void(__fastcall* od_respawn_tick_fn)(uint32_t player);
typedef void(__fastcall* od_ui_sound_fn)(uint32_t sound, float volume);              // (ecx, xmm1)
static hr_ui_sound_fn o_hr_ui_sound;
static od_respawn_tick_fn o_od_respawn_tick;
static od_ui_sound_fn o_od_ui_sound;
static od_respawn_tick_fn o_h3_respawn_tick;    // Halo 3's are ODST's functions (the same engine)
static od_ui_sound_fn o_h3_ui_sound;
static const uint8_t HR_UI_SOUND_HEAD[8] = { 0x48, 0x8B, 0xC4, 0x48, 0x89, 0x58, 0x18, 0x48 };
static const uint8_t OD_RESPAWN_TICK_HEAD[8] = { 0x89, 0x4C, 0x24, 0x08, 0x55, 0x53, 0x56, 0x57 };
static const uint8_t OD_UI_SOUND_HEAD[8] = { 0x40, 0x55, 0x48, 0x8D, 0x6C, 0x24, 0xA9, 0x48 };
static thread_local bool t_bot_tick;            // a bot's respawn handler is running (game thread)
static volatile long g_muted[3];                // bot countdown sounds muted: Reach, ODST, Halo 3 (logged: proof without a speaker)

static void muted(int game) {
    static const char* names[3] = { "Reach", "ODST", "Halo 3" };
    long n = InterlockedIncrement(&g_muted[game]);
    if (n == 1 || n % 20 == 0) logf("spawnhook: %s: %ld bot respawn countdown sounds muted", names[game], n);
}

static bool is_bot(uint32_t player) {
    int index = player & 0xFFFF;
    for (int i = 0; i < HB_MAX_PLAYERS; i++) if (g_shm->bot_player_index[i] == index) return true;
    return false;
}

static char __fastcall h_hr_should_spawn(uint32_t player) {
    hr_bot_solo_spawn(player);
    return o_hr_should_spawn(player);
}

static uint64_t __fastcall h_hr_respawn_tick(uint32_t player) {
    hr_bot_spawn_point(player);
    t_bot_tick = is_bot(player);
    uint64_t r = o_hr_respawn_tick(player);
    t_bot_tick = false;
    return r;
}

static void __fastcall h_hr_ui_sound(uint32_t sound, float volume, char flag) {
    if (!t_bot_tick) o_hr_ui_sound(sound, volume, flag);
    else muted(0);
}

static void __fastcall h_od_respawn_tick(uint32_t player) {
    t_bot_tick = is_bot(player);
    o_od_respawn_tick(player);
    t_bot_tick = false;
}

static void __fastcall h_od_ui_sound(uint32_t sound, float volume) {
    if (!t_bot_tick) o_od_ui_sound(sound, volume);
    else muted(1);
}

static void __fastcall h_h3_respawn_tick(uint32_t player) {
    t_bot_tick = is_bot(player);
    o_h3_respawn_tick(player);
    t_bot_tick = false;
}

static void __fastcall h_h3_ui_sound(uint32_t sound, float volume) {
    if (!t_bot_tick) o_h3_ui_sound(sound, volume);
    else muted(2);
}

static bool same(const uint8_t* at, const uint8_t* bytes, size_t n) {
    __try { return !memcmp(at, bytes, n); } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}

// A hook is made once and only ever enabled / disabled, never removed: MinHook frees a removed hook's
// trampoline, and a game thread inside the hook at that moment would jump into freed memory. A module reloaded at
// the same address has its own bytes back: disable (MinHook writes the original bytes, the same) and enable again.
struct made_hook { uint8_t* at; void* tramp; };
struct game_hook {
    const wchar_t* dll; const char* name; uintptr_t rva; const uint8_t* head; void* detour; void** orig;
    made_hook made[16];             // every address the hook was created at (the DLL may load elsewhere next time)
    uint8_t* at;                    // where it is on now
    uint8_t bytes[5];               // the jump it wrote, to see a reloaded module
    bool refused;
};
static game_hook g_hooks[] = {
    { L"haloreach.dll", "spawn check", 0xFFABC, HR_SHOULD_SPAWN_HEAD, (void*)&h_hr_should_spawn, (void**)&o_hr_should_spawn },
    { L"haloreach.dll", "respawn handler", 0x4633C, HR_RESPAWN_TICK_HEAD, (void*)&h_hr_respawn_tick, (void**)&o_hr_respawn_tick },
    { L"haloreach.dll", "interface sound", 0xBADA8, HR_UI_SOUND_HEAD, (void*)&h_hr_ui_sound, (void**)&o_hr_ui_sound },
    { L"halo3odst.dll", "respawn handler", 0xFE0BC, OD_RESPAWN_TICK_HEAD, (void*)&h_od_respawn_tick, (void**)&o_od_respawn_tick },
    { L"halo3odst.dll", "interface sound", 0x185CA4, OD_UI_SOUND_HEAD, (void*)&h_od_ui_sound, (void**)&o_od_ui_sound },
    { L"halo3.dll", "respawn handler", 0xE3E74, OD_RESPAWN_TICK_HEAD, (void*)&h_h3_respawn_tick, (void**)&o_h3_respawn_tick },
    { L"halo3.dll", "interface sound", 0x158244, OD_UI_SOUND_HEAD, (void*)&h_h3_ui_sound, (void**)&o_h3_ui_sound },
};

static void watch_one(game_hook& k, uint8_t* mod) {
    uint8_t* at = mod ? mod + k.rva : nullptr;
    if (at && at == k.at && same(at, k.bytes, 5)) return;            // on, as wanted
    if (!at) { k.at = nullptr; return; }
    made_hook* h = nullptr;
    for (made_hook& m : k.made) if (m.at == at) h = &m;
    if (!h && !same(at, k.head, 8)) {
        if (!k.refused) logf("spawnhook: %ls+0x%llx (%s) is not the expected function: no hook",
                             k.dll, (unsigned long long)k.rva, k.name);
        k.refused = true;
        return;
    }
    if (!h) {
        void* tramp = nullptr;
        for (made_hook& m : k.made) if (!m.at) { h = &m; break; }
        if (!h || MH_CreateHook(at, k.detour, &tramp) != MH_OK) {
            logf("spawnhook: %s hook at %p failed", k.name, at);
            return;
        }
        h->at = at; h->tramp = tramp;
    }
    *k.orig = h->tramp;
    MH_DisableHook(at);
    if (MH_EnableHook(at) != MH_OK) { logf("spawnhook: %s hook at %p not enabled", k.name, at); return; }
    k.at = at;
    memcpy(k.bytes, at, 5);
    logf("spawnhook: %ls %s hooked at %p", k.dll, k.name, at);
}

// botcore's main loop: keep each hook on while its DLL is loaded, following it through unload / reload
void spawnhook_watch() {
    if (!g_shm) return;
    for (game_hook& k : g_hooks) watch_one(k, (uint8_t*)GetModuleHandleW(k.dll));
}
