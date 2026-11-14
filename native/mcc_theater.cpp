// mcc_theater.cpp: MCC's Theater for Halo: CE and Halo 2 Classic (docs/THEATER_RE.md).
//
// MCC scans each game's user content (Temporary\UserContent\<game>\GameType|Map|Movie, and the games' autosave films)
// in FUN_14047b300; for each game and content type it asks FUN_1404834ac(content type, game): CE (0) and H2C (1) get
// nothing but game types (types 1-3 refused). Films (type 2) are let through for both, so MCC reads their Movie
// folders and asks the game's data access for each film's metadata (halo2: h2.cpp, halo1: ce_film.cpp).
#include <windows.h>
#include <stdint.h>
#include <string.h>
#include "third_party/minhook/include/MinHook.h"

void logf(const char* fmt, ...);
void h2_film_meta_ensure();                       // h2.cpp
void ce_film_meta_ensure();                       // ce_film.cpp

namespace {
const uintptr_t RVA_CONTENT_ALLOWED = 0x4834ac;   // bool (content type 0 game type / 1 map / 2 film / 3 image, game)
const uint8_t CONTENT_PROLOGUE[15] = {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74, 0x24, 0x10, 0x57, 0x48, 0x83, 0xEC, 0x20};
typedef char(__fastcall* allowed_fn)(uint32_t type, int game);
allowed_fn g_allowed_orig;

char __fastcall allowed_hook(uint32_t type, int game) {
    if (type == 2 && (game == 0 || game == 1)) return 1;     // films for Halo: CE and Halo 2 Classic
    return g_allowed_orig(type, game);
}

// MCC's content scan (FUN_14047b300): the games' film metadata answers go in first (a game DLL reloaded since)
const uintptr_t RVA_SCAN = 0x47b300;
const uint8_t SCAN_PROLOGUE[12] = {0x48, 0x8B, 0xC4, 0x55, 0x41, 0x54, 0x41, 0x55, 0x41, 0x56, 0x41, 0x57};
typedef uint8_t(__fastcall* scan_fn)();
scan_fn g_scan_orig;
uint8_t __fastcall scan_hook() {
    __try { h2_film_meta_ensure(); ce_film_meta_ensure(); } __except (EXCEPTION_EXECUTE_HANDLER) {}
    return g_scan_orig();
}
}  // namespace

// once, at botcore's start (MinHook initialized); enabled with the rest
void mcc_theater_install() {
    uint8_t* exe = (uint8_t*)GetModuleHandleW(nullptr);
    __try {
        if (memcmp(exe + RVA_CONTENT_ALLOWED, CONTENT_PROLOGUE, sizeof CONTENT_PROLOGUE)) {
            logf("theater: not the MCC 1.3528 build decoded: CE / H2C films not offered");
            return;
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) { return; }
    if (MH_CreateHook(exe + RVA_CONTENT_ALLOWED, (void*)&allowed_hook, (void**)&g_allowed_orig) != MH_OK ||
        MH_EnableHook(exe + RVA_CONTENT_ALLOWED) != MH_OK) {
        logf("theater: hook failed");
        return;
    }
    logf("theater: Halo: CE and Halo 2 Classic films offered");
    __try {
        if (!memcmp(exe + RVA_SCAN, SCAN_PROLOGUE, sizeof SCAN_PROLOGUE) &&
            MH_CreateHook(exe + RVA_SCAN, (void*)&scan_hook, (void**)&g_scan_orig) == MH_OK && MH_EnableHook(exe + RVA_SCAN) == MH_OK)
            logf("theater: content scan hooked");
        else logf("theater: content scan not hooked");
    } __except (EXCEPTION_EXECUTE_HANDLER) {}
}
