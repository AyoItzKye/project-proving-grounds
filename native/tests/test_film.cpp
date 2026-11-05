// native/film.cpp: a match's bots recorded and replayed in its Theater film, found by any copy of the mod (the shared
// folder) and in a copy's old logs\films. Built and run by tools/test_native_film.py with a scratch folder argument.
#include "../film.cpp"
#include <stdlib.h>
#include <stdarg.h>

hb_shared* g_shm;
void logf(const char*, ...) {}
static wchar_t g_shared[MAX_PATH], g_old[MAX_PATH];
void film_dir(wchar_t* out) { wcscpy_s(out, MAX_PATH, g_shared); CreateDirectoryW(out, nullptr); }
void film_old_dir(wchar_t* out) { wcscpy_s(out, MAX_PATH, g_old); }

static int fails = 0;
static void want(const char* what, bool ok) { if (!ok) { printf("FAIL %s\n", what); fails++; } }

static const uint64_t KEY = 0x0d4e877beed46b42ull;
static const uint32_t TICKS = 120;

// the bots' input at a tick: bot 0 is player 3 from tick 10, it walks and turns
static void live_input(uint32_t t) {
    for (int i = 0; i < HB_MAX_PLAYERS; i++) g_shm->bot_player_index[i] = -1;
    memset(g_shm->actions, 0, sizeof g_shm->actions);
    if (t >= 10) {
        g_shm->bot_player_index[0] = 3;
        g_shm->actions[0] = hb_action{ 1.0f, 0.0f, 0.01f * (float)(t / 7), 0.0f, (t % 30 < 5) ? HB_BTN_FIRE : 0u, t / 7 + 1 };
    }
}

static void record(uint64_t key) {
    for (uint32_t t = 1; t <= TICKS; t++) { live_input(t); want("record tick", film_tick(key, t, false, 1u << 26) != nullptr); }
    film_end();
}

// a film: every tick gives back what the match gave the game at that tick
static bool replays(uint64_t key) {
    bool ok = true;
    for (uint32_t t = 1; t <= TICKS; t++) {
        live_input(t);
        film_frame want_fr; memcpy(want_fr.index, g_shm->bot_player_index, sizeof want_fr.index);
        memcpy(want_fr.act, g_shm->actions, sizeof want_fr.act);
        memset(g_shm->bot_player_index, 0, sizeof g_shm->bot_player_index);    // (a film's own shared memory)
        const film_frame* fr = film_tick(key, t, true, 1u << 26);
        if (!fr || memcmp(fr, &want_fr, sizeof want_fr)) { ok = false; break; }
    }
    film_end();
    return ok;
}

int main(int argc, char** argv) {
    if (argc < 2) { printf("usage: test_film <scratch folder>\n"); return 2; }
    g_shm = (hb_shared*)calloc(1, sizeof(hb_shared));
    wchar_t root[MAX_PATH]; swprintf_s(root, L"%hs", argv[1]);
    wchar_t copy_a[MAX_PATH], copy_b[MAX_PATH];
    swprintf_s(g_shared, L"%s\\shared", root);
    swprintf_s(copy_a, L"%s\\repo_logs_films", root); CreateDirectoryW(copy_a, nullptr);
    swprintf_s(copy_b, L"%s\\install_logs_films", root); CreateDirectoryW(copy_b, nullptr);

    // 1. the working repo's botcore records a Reach match; the install's botcore plays its film (tonight's case)
    wcscpy_s(g_old, copy_a);
    record(KEY);
    wcscpy_s(g_old, copy_b);
    want("a film recorded by another copy has its bots", replays(KEY));
    // 2. Restart Film: the same film again from tick 1
    want("the film again", replays(KEY));
    // 3. a match recorded before the shared folder, in this copy's logs\films
    wchar_t from[MAX_PATH], to[MAX_PATH];
    swprintf_s(from, L"%s\\%016llx.hbf", g_shared, (unsigned long long)KEY);
    swprintf_s(to, L"%s\\%016llx.hbf", copy_b, (unsigned long long)KEY);
    want("move", MoveFileExW(from, to, MOVEFILE_REPLACE_EXISTING) != 0);
    want("an old recording in logs\\films has its bots", replays(KEY));
    // 4. a film of no recorded match: no bots, nothing made up
    const film_frame* fr = film_tick(KEY + 1, 1, true, 1u << 26);
    bool none = fr != nullptr;
    for (int i = 0; fr && i < HB_MAX_PLAYERS; i++) none = none && fr->index[i] == -1;
    want("no recording: no bots", none);
    film_end();
    // 5. a new recording goes in the shared folder, not a copy's logs\films
    wcscpy_s(g_old, copy_a);
    record(KEY + 2);
    swprintf_s(from, L"%s\\%016llx.hbf", g_shared, (unsigned long long)(KEY + 2));
    swprintf_s(to, L"%s\\%016llx.hbf", copy_a, (unsigned long long)(KEY + 2));
    want("recorded in the shared folder", GetFileAttributesW(from) != INVALID_FILE_ATTRIBUTES
                                          && GetFileAttributesW(to) == INVALID_FILE_ATTRIBUTES);
    if (fails) return 1;
    printf("film OK\n");
    return 0;
}
