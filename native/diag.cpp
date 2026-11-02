// diag.dll: temporary instrumentation (MCC 1.3528 halo1.dll). Logs the pickup checks for one
// player: examine-nearby-item (+0xAD4E28) and inside it can-use-weapon (+0xB09624),
// should-autopick (+0xAD4D84) and add-weapon-to-inventory (+0xB08F3C), with results.
// The player index to watch is read from diag_player.txt next to the DLL.
#include <windows.h>
#include <stdio.h>
#include <share.h>
#include <stdint.h>
#include "third_party/minhook/include/MinHook.h"

static FILE* g_log;
static uint8_t* g_h1;
static int g_watch = -1;
static int g_inside = -1;          // player index while inside examine for the watched player
static int g_lines;

typedef void(__fastcall* examine_fn)(uint64_t player, uint32_t item);
typedef char(__fastcall* two_fn)(uint64_t a, uint32_t b);
typedef char(__fastcall* add_fn)(uint64_t unit, uint32_t weapon, uint32_t mode);
static examine_fn o_examine;
static two_fn o_can_use, o_autopick;
static add_fn o_add;

static void logf(const char* fmt, ...) {
    if (!g_log || g_lines > 4000) return;
    va_list a; va_start(a, fmt); vfprintf(g_log, fmt, a); va_end(a);
    fputc('\n', g_log); fflush(g_log); g_lines++;
}

static void __fastcall h_examine(uint64_t player, uint32_t item) {
    bool watch = (int)(player & 0xFFFF) == g_watch;
    if (watch) { g_inside = g_watch; logf("examine player %llx item %08x", player, item); }
    o_examine(player, item);
    if (watch) g_inside = -1;
}
static char __fastcall h_can_use(uint64_t unit, uint32_t weapon) {
    char r = o_can_use(unit, weapon);
    if (g_inside >= 0) logf("  can_use unit %08llx weapon %08x -> %d", unit, weapon, r);
    return r;
}
static char __fastcall h_autopick(uint64_t unit, uint32_t weapon) {
    char r = o_autopick(unit, weapon);
    if (g_inside >= 0) logf("  should_autopick unit %08llx weapon %08x -> %d", unit, weapon, r);
    return r;
}
static char __fastcall h_add(uint64_t unit, uint32_t weapon, uint32_t mode) {
    char r = o_add(unit, weapon, mode);
    if (g_inside >= 0) logf("  add_to_inventory unit %08llx weapon %08x mode %u -> %d", unit, weapon, mode, r);
    return r;
}

static DWORD WINAPI main_thread(LPVOID self) {
    wchar_t path[MAX_PATH];
    GetModuleFileNameW((HMODULE)self, path, MAX_PATH);
    wchar_t* slash = wcsrchr(path, L'\\') + 1;
    wcscpy_s(slash, 64, L"diag_player.txt");
    FILE* f = _wfopen(path, L"r");
    if (f) { fscanf_s(f, "%d", &g_watch); fclose(f); }
    wcscpy_s(slash, 64, L"diag.log");
    g_log = _wfsopen(path, L"w", _SH_DENYNO);
    g_h1 = (uint8_t*)GetModuleHandleW(L"halo1.dll");
    if (!g_h1) { logf("no halo1"); return 0; }
    MH_Initialize();
    bool ok = MH_CreateHook(g_h1 + 0xAD4E28, (void*)&h_examine, (void**)&o_examine) == MH_OK &&
              MH_CreateHook(g_h1 + 0xB09624, (void*)&h_can_use, (void**)&o_can_use) == MH_OK &&
              MH_CreateHook(g_h1 + 0xAD4D84, (void*)&h_autopick, (void**)&o_autopick) == MH_OK &&
              MH_CreateHook(g_h1 + 0xB08F3C, (void*)&h_add, (void**)&o_add) == MH_OK &&
              MH_EnableHook(MH_ALL_HOOKS) == MH_OK;
    logf("diag hooks %s, watching player %d", ok ? "on" : "FAILED", g_watch);
    return 0;
}

BOOL APIENTRY DllMain(HMODULE mod, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(mod);
        CloseHandle(CreateThread(nullptr, 0, main_thread, mod, 0, nullptr));
    }
    return TRUE;
}
