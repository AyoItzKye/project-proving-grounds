// h2.cpp: Halo 2 Classic (halo2.dll, MCC 1.3528) player bots, the CE plan on H2 (docs/H2-01).
// - players update FUN_1806a3910(actions): actions +8 = bitmask of players with an action this
//   tick, +0x100 + index * 0x60 = each player's 0x60-byte action; validated, then applied with
//   unit_control FUN_1808f5800. We hook it (game thread, every tick): run the brain's commands,
//   copy player 0's action for the debug view, write each driven bot's action, call the original.
// - player creation: FUN_18069d2c0(index, config) = player_new_at_index; config +0 valid, +1 "no
//   machine", +2 controller (0xFFFF), +4 (-1), +8 machine id, +0x10 player id, +0x18 the 0x84-byte
//   player configuration (name first), cloned from player 0 (player +0xC0).
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <wchar.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#include <intrin.h>
#include "shared.h"
#include "film.h"
#include "third_party/minhook/include/MinHook.h"

extern hb_shared* g_shm;
void logf(const char* fmt, ...);
void report_note_bot(int index, const wchar_t* name, const wchar_t* tag, int team, const wchar_t* clan,
                     const uint16_t* emblem);   // report.cpp
void bot_service_tag(const wchar_t* name, wchar_t tag[4]);                                                // report.cpp

static uint8_t* g_h2;
static uint8_t g_h2_patch[5];
static const uintptr_t H2_PLAYERS_UPDATE = 0x6A3910, H2_PLAYER_NEW_AT = 0x69D2C0, H2_PLAYERS_PTR = 0xE80A28;
static const size_t H2_PLAYER_SIZE = 0x224, H2_ACTION = 0x60;
typedef void(__fastcall* players_update_fn)(uint8_t* actions);
typedef uint32_t(__fastcall* player_new_at_fn)(int index, uint8_t* config);
static players_update_fn o_update;

static uint8_t* h2_player(int index) {
    uint8_t* hdr = *(uint8_t**)(g_h2 + H2_PLAYERS_PTR);
    if (!hdr || index < 0 || index >= *(int32_t*)(hdr + 0x20)) return nullptr;
    int64_t rel = *(int64_t*)(hdr + 0x48);
    return rel ? hdr + rel + (size_t)index * H2_PLAYER_SIZE : nullptr;
}
static bool h2_live(int index) { uint8_t* p = h2_player(index); return p && *(uint16_t*)p != 0; }

// objects: headers [halo2+0x18B7398] (12 bytes: +0 salt, +3 type, +8 offset), pool at
// ([halo2+0x18B7360] + 0x57) & ~0xF. Object +0x14 parent, +0x64 position; unit +0x224 weapon set
// identifier, +0x226 primary / +0x227 secondary weapon index (the action's +0x24..+0x27 layout).
static const uintptr_t H2_OBJ_HEADERS = 0x18B7398, H2_OBJ_POOL = 0x18B7360;
static uint8_t* h2_object(uint32_t handle) {
    uint8_t* hdr = *(uint8_t**)(g_h2 + H2_OBJ_HEADERS);
    if (!hdr || handle == 0xFFFFFFFFu || (int)(handle & 0xFFFF) >= *(int32_t*)(hdr + 0x20)) return nullptr;
    uint8_t* e = hdr + *(int64_t*)(hdr + 0x48) + (size_t)(handle & 0xFFFF) * 12;
    if (*(uint16_t*)e != handle >> 16) return nullptr;
    return (uint8_t*)((*(uintptr_t*)(g_h2 + H2_OBJ_POOL) + 0x57) & ~(uintptr_t)0xF) + *(int32_t*)(e + 8);
}

// the loose weapon (type 2, no parent) nearest the unit within 1.5 units: what a human gets the
// "hold E to pick up" prompt for. ponytail: linear scan of the object table, only while E is held
static uint32_t h2_pickup_target(uint8_t* unit) {
    uint8_t* hdr = *(uint8_t**)(g_h2 + H2_OBJ_HEADERS);
    if (!hdr) return 0xFFFFFFFFu;
    int n = *(int32_t*)(hdr + 0x20);
    uint8_t* ents = hdr + *(int64_t*)(hdr + 0x48);
    const float* p = (const float*)(unit + 0x64);
    uint32_t best = 0xFFFFFFFFu;
    float bd = 1.5f * 1.5f;
    for (int i = 0; i < n; i++) {
        uint8_t* e = ents + (size_t)i * 12;
        if (!*(uint16_t*)e || e[3] != 2) continue;
        uint32_t h = (uint32_t)*(uint16_t*)e << 16 | (uint32_t)i;
        uint8_t* o = h2_object(h);
        if (!o || *(uint32_t*)(o + 0x14) != 0xFFFFFFFFu) continue;
        const float* q = (const float*)(o + 0x64);
        float d = (q[0] - p[0]) * (q[0] - p[0]) + (q[1] - p[1]) * (q[1] - p[1]) + (q[2] - p[2]) * (q[2] - p[2]);
        if (d < bd) { bd = d; best = h; }
    }
    return best;
}

// boarding: near a vehicle a player's action carries interaction type 5 (+0x2C), the seat (+0x2E) and the vehicle
// (+0x30), and Use takes that seat (a person's recorded play, Nov 7, Coagulation / Containment: every boarding, the
// Scorpion's, Banshee's and Spectre's driver seat 0, the Spectre's passengers 1 and 2, its gun seat 0 of its own
// vehicle object riding on the Spectre). A bot's was always empty: Halo 2 bots stood by vehicles and never got in.
// The vehicle (type 1) nearest the unit within 3 u, or with turret the gun (a vehicle with a parent) on the nearest
// vehicle, measured at that vehicle (a child's place is its offset). ponytail: linear scan, only while Use is held
static uint32_t h2_near_vehicle(uint8_t* unit, bool turret) {
    uint8_t* hdr = *(uint8_t**)(g_h2 + H2_OBJ_HEADERS);
    if (!hdr) return 0xFFFFFFFFu;
    int n = *(int32_t*)(hdr + 0x20);
    uint8_t* ents = hdr + *(int64_t*)(hdr + 0x48);
    const float* p = (const float*)(unit + 0x64);
    uint32_t best = 0xFFFFFFFFu;
    float bd = 3.0f * 3.0f;
    for (int i = 0; i < n; i++) {
        uint8_t* e = ents + (size_t)i * 12;
        if (!*(uint16_t*)e || e[3] != 1) continue;
        uint32_t h = (uint32_t)*(uint16_t*)e << 16 | (uint32_t)i;
        uint8_t* o = h2_object(h);
        if (!o) continue;
        uint32_t parent = *(uint32_t*)(o + 0x14);
        if ((parent != 0xFFFFFFFFu) != turret) continue;
        uint8_t* at = turret ? h2_object(parent) : o;
        if (!at) continue;
        const float* q = (const float*)(at + 0x64);
        float dx = q[0] - p[0], dy = q[1] - p[1], dz = q[2] - p[2], d = dx * dx + dy * dy;
        if (d < bd && dz > -2.0f && dz < 2.5f) { bd = d; best = h; }
    }
    return best;
}

// a bot on foot holding Use with a seat asked for (shared.h HB_SEAT_SHIFT): that seat of the nearest vehicle (or of
// the gun on it: HB_BTN_TURRET) as its interaction
static void h2_board(uint8_t* act, uint8_t* unit, uint32_t b) {
    int seat = hb_seat(b);
    if (!(b & HB_BTN_ACTION) || seat < 0 || *(uint32_t*)(unit + 0x14) != 0xFFFFFFFFu) return;
    uint32_t veh = h2_near_vehicle(unit, (b & HB_BTN_TURRET) != 0);
    if (veh == 0xFFFFFFFFu) return;
    *(int16_t*)(act + 0x2C) = 5;
    *(int16_t*)(act + 0x2E) = (int16_t)seat;
    *(uint32_t*)(act + 0x30) = veh;
}

static int h2_free_slot() {
    for (int i = 0; i < HB_MAX_PLAYERS; i++) if (g_shm->bot_player_index[i] < 0) return i;
    return -1;
}

static int64_t h2_add_bot(int arg) {
    uint8_t* me = h2_player(0);
    int slot = h2_free_slot();
    if (!me || slot < 0) return -2;
    int index = -1;
    for (int i = 1; i < HB_MAX_PLAYERS; i++) if (h2_player(i) && !h2_live(i)) { index = i; break; }
    if (index < 0) return -3;
    uint8_t cfg[0x18 + 0x84] = {};
    cfg[0] = 1;                                  // valid
    // Tests: "no machine" (arg bit 16) and an unknown machine both ended the match within seconds
    // (the session counts the player as gone; one player left wins). Default now: a second local
    // player on the host's own machine, like split screen (controller and user index 1..3).
    cfg[1] = (arg >> 16) & 1;
    if (arg & (1 << 17)) {
        *(uint64_t*)(cfg + 8) = 0xB07B07B0B07B07B0ull;     // unknown machine (old test)
    } else {
        *(uint64_t*)(cfg + 8) = *(uint64_t*)(me + 0x14);    // the host's machine identifier
        int local = 1 + slot % 3;
        *(uint16_t*)(cfg + 2) = (uint16_t)local;           // controller index
        *(int32_t*)(cfg + 4) = local;                       // user index
    }
    *(uint16_t*)(cfg + 2) = 0xFFFF;
    *(int32_t*)(cfg + 4) = -1;
    *(uint64_t*)(cfg + 0x10) = 0xB07B07B000000000ull | (uint64_t)index;   // a player identifier
    memcpy(cfg + 0x18, me + 0xC0, 0x84);         // player 0's configuration (looks, team...)
    int team = (arg >> 8) & 0xFF;                // 0xFF = keep player 0's
    if (team != 0xFF) cfg[0x18 + 0x7C] = (uint8_t)team;    // configuration +0x7C: team (testing)
    wchar_t* name = (wchar_t*)(cfg + 0x18);
    wmemset(name, 0, 16);
    if (g_shm->cmd_name[0]) { wcsncpy_s(name, 16, g_shm->cmd_name, 15); g_shm->cmd_name[0] = 0; }
    else swprintf_s(name, 16, L"Bot %d", slot + 1);
    hb_apply_look(g_shm, 2, cfg, sizeof cfg);   // its own species and colours (brain/looks.py)
    // what MCC shows for it (name, tags, emblem: report.cpp), before MCC first looks the new player up
    wchar_t tag[4];                              // its service tag, configuration +0x68 (the scoreboard's tag column
    bot_service_tag(name, tag);                  // in Halo 2 classic)
    memcpy(cfg + 0x68, tag, 8);
    report_note_bot(index, name, tag, team != 0xFF ? team : -1, g_shm->cmd_clan, g_shm->cmd_emblem);
    uint32_t h = ((player_new_at_fn)(g_h2 + H2_PLAYER_NEW_AT))(index, cfg);
    if (h != 0xFFFFFFFFu) {
        g_shm->actions[slot].seq = 0;
        g_shm->bot_player_index[slot] = index;
    }
    logf("h2 add_bot index %d -> %08x", index, h);
    return (int64_t)h;
}

static void h2_run_command() {
    // only commands marked for Halo 2 (cmd_arg bit 24): a CE brain's ADD_BOT must never reach
    // an H2 match (adding a player ends it, docs/H2-01)
    if (g_shm->cmd_seq == g_shm->cmd_done_seq || !(g_shm->cmd_arg & (1 << 24))) return;
    g_shm->cmd_fault = 0;
    __try {
        if (g_shm->cmd == HB_CMD_ADD_BOT) g_shm->cmd_result = h2_add_bot(g_shm->cmd_arg);
        else g_shm->cmd_result = -1;
    } __except (EXCEPTION_EXECUTE_HANDLER) { g_shm->cmd_fault = 1; g_shm->cmd_result = -1; }
    g_shm->cmd_done_seq = g_shm->cmd_seq;
}

extern uint32_t g_playback;                      // botcore.cpp: a film is running (no brain, no bots)
static void h2_theater_end();                    // (below: the Theater's camera and speed back when a film ends)
static void h2_theater_install(uint8_t* h2);     // (below: its hooks)
static char g_th2_path[MAX_PATH];                // the film MCC's Theater launched
static uint32_t g_th2_over_tick;                 // its game over's world tick (halo2's board from there; 0 not known)
static void h2_film_over_read();                 // (below: from the film's header, 0x1818)
static void h2_film_over();                      // (below: the board came up: kept, and the Theater goes back before it)
static void h2_theater_tick();                   // (below: a skip back's reopening, on the game thread)

// Opening a film from inside a running game, on the game thread, as the debug script function film_play did
// (FUN_1806f9f50 -> FUN_1806f6d80(path)): <films>\h2_play_now.txt holds the path (UTF-8, one shot)
void film_dir(wchar_t* out);
static void h2_play_now() {
    static char path[MAX_PATH];
    wchar_t dir[MAX_PATH], f[MAX_PATH];
    film_dir(dir);
    swprintf_s(f, L"%s\\h2_play_now.txt", dir);
    FILE* fp = _wfopen(f, L"rb");
    if (!fp) return;
    size_t n = fread(path, 1, sizeof path - 1, fp);
    fclose(fp);
    DeleteFileW(f);
    while (n && (path[n - 1] == '\n' || path[n - 1] == '\r' || path[n - 1] == ' ')) n--;
    path[n] = 0;
    typedef void(__fastcall* open_fn)(const char*);
    typedef void(__fastcall* close_fn)();
    __try {
        // the game being left was recording: finish its film first (closing it later, at its end, reset the film
        // state the opened film needs: live, the film closed as it opened), and record nothing while a film plays
        // (the film's own game would start a new recording over it); film_record comes back when it ends (h_update)
        *(volatile uint8_t*)(g_h2 + 0x18a4320) = 0;
        if (*(volatile uint8_t*)(g_h2 + 0x18a4333)) { ((close_fn)(g_h2 + 0x6f6a80))(); *(volatile uint8_t*)(g_h2 + 0x18a4333) = 0; }
        logf("h2 films: opening %s from the running game", path);
        ((open_fn)(g_h2 + 0x6f6d80))(path);
        logf("h2 films: film state now %d", *(volatile int32_t*)(g_h2 + 0x15f4d54));
    } __except (EXCEPTION_EXECUTE_HANDLER) { logf("h2 films: fault opening the film"); }
}

static void __fastcall h_update(uint8_t* actions) {
    if (g_shm) {
        // a film playing (halo2's film state DAT_1815f4d54 == 1): its players are the film's, so no brain and no bots
        // (live Nov 13: the brain started on the menus giving way and added a bot into a film's game). Set before
        // game = 2, which lets botcore's main loop start the brain
        // The film holds each tick's simulation update, built before this hook writes the bots' actions, so a film
        // replays the person's input but not the bots'. As in Reach / Halo 3 (film.cpp): the bots' commands and
        // input are recorded beside it, keyed by the game options (the active options DAT_180e80a78, +8 up to the
        // playback type at +0x2C2: the same block the film's header carries), at the simulation's update tick
        // (world [DAT_1818a4338] +0x34, FUN_1808671e0), and a film replays them at the same ticks
        const film_frame* fr = nullptr;
        uint32_t tick = 0;
        __try {
            g_playback = *(volatile int32_t*)(g_h2 + 0x15f4d54) == 1;
            uint8_t* opts = *(uint8_t**)(g_h2 + 0xe80a78);
            uint8_t* world = *(uint8_t**)(g_h2 + 0x18a4338);
            if (opts && world) {
                tick = *(uint32_t*)(world + 0x34);
                fr = film_tick(film_hash(opts + 8, 0x2C2 - 8), tick, g_playback != 0, 1u << 24);
            }
        } __except (EXCEPTION_EXECUTE_HANDLER) { fr = nullptr; }
        g_shm->game_tick++;
        if ((g_shm->game_tick % 30) == 0) h2_play_now();     // a film asked for from a running game (Bungie's film_play)
        if (g_playback && *(volatile uint8_t*)(g_h2 + 0x1e8ce73)) { *(volatile uint8_t*)(g_h2 + 0x1e8ce73) = 0; logf("h2 films: the film's first tick"); }
        static bool was_playing;                              // a film over: games record again
        if (was_playing && !g_playback) { *(volatile uint8_t*)(g_h2 + 0x18a4320) = 1; h2_theater_end(); logf("h2 films: film over, recording again"); }
        was_playing = g_playback != 0;
        g_shm->game = 2;
        h2_run_command();
        if (fr) while (film_more(tick)) h2_run_command();      // a film: this tick's other commands
        __try {
            if (*(uint32_t*)(actions + 8) & 1) {        // player 0 has an action: copy it for the debug view
                memcpy(g_shm->dbg_action, actions + 0x100, H2_ACTION);
                g_shm->dbg_seq++;
            }
            for (int i = 0; i < HB_MAX_PLAYERS; i++) {
                int index = fr ? fr->index[i] : g_shm->bot_player_index[i];   // (film.cpp: this tick's input, frozen)
                const hb_action& a = fr ? fr->act[i] : g_shm->actions[i];
                if (index < 0 || !a.seq || !h2_live(index)) continue;
                uint8_t* act = actions + 0x100 + (size_t)index * H2_ACTION;
                // decoded from player 0's action (tools/h2_action_probe.py): +0 button flags
                // (jump 0x6, fire 0x008C0100), +8 yaw, +0xC pitch, +0x10 throttle forward, +0x14
                // throttle left, +0x18/+0x1C triggers, +0x20 low bits action (0x3); the rest
                // (weapon and grenade slots...) comes from player 0's action as a template
                if (g_shm->h2_raw_valid) memcpy(act, g_shm->h2_raw_action, H2_ACTION);
                else if (*(uint32_t*)(actions + 8) & 1) memcpy(act, actions + 0x100, H2_ACTION);
                // the action's own fields (network decoder FUN_1808abf70, docs/H2-01): +0x24 weapon
                // set, +0x26/+0x27 primary/secondary weapon index, +0x28 grenade index, +0x2A
                // zoom, +0x2C interaction type, +0x2E pickup flags / seat, +0x30 interaction
                // object, +0x34 melee target, +0x38.. aim assist. Player 0's must not leak in (its
                // melee target was often this very bot).
                uint8_t* unit = h2_object(*(uint32_t*)(h2_player(index) + 0x2C));
                memset(act + 0x2C, 0, 4);
                memset(act + 0x30, 0xFF, 0x14);
                // the rest of the aim assist (+0x50 flags, +0x54 / +0x58 weights): the player's, with its target
                // (+0x38) cleared above, fails the action check (FUN_1807586b0 in the players update) and the bot's
                // last action replays (as Halo 3: ghidra/h2_aim_gate.c)
                memset(act + 0x44, 0, 0x18);
                // the red reticle's target (shared.h hb_target), where the action's network decoder carries a player's
                // (FUN_1808abf70 / FUN_1807583d0, ghidra/h2_actdec.c, h2_aimdec.c): +0x34 "melee-target-unit", the
                // autoaim block +0x38 "target-object", +0x3C "model-target", +0x40 "target-player", +0x50 flags,
                // +0x54 "primary-autoaim-level". As Halo 3's (live: no bot sword lunged until it was set). The values
                // a player's input writes are not seen live in Halo 2 yet (INFERRED: H3's, level 1.0)
                int tgt = hb_target(a.buttons);
                if (tgt >= 0 && tgt < HB_MAX_PLAYERS && h2_live(tgt)) {
                    uint32_t th = *(uint32_t*)(h2_player(tgt) + 0x2C);
                    if (th != 0xFFFFFFFFu && h2_object(th)) {
                        *(uint32_t*)(act + 0x34) = th;
                        *(uint32_t*)(act + 0x38) = th;
                        *(float*)(act + 0x54) = 1.0f;
                    }
                }
                hb_set_zoom(2, act, H2_ACTION, a.buttons);          // the scope level it wants (-1 none)
                // the bot's own weapon set, from the field Halo 2's unit control (FUN_1808f5800, ghidra/h2_unit_input.c)
                // checks and the game's own input copies (unit +0x228); +0x224 let a switch through only by chance
                if (unit) memcpy(act + 0x24, unit + 0x228, 4);
                int want = (int)((a.buttons >> HB_WEAPON_SHIFT) & 7) - 1;
                if (want >= 0) act[0x26] = (uint8_t)want;           // switch weapons
                uint32_t b = a.buttons, flags = 0;
                static uint32_t prev[HB_MAX_PLAYERS];
                if (b & HB_BTN_JUMP) flags |= 0x6;
                // fire: 0x008C0000 while held, 0x100 only on the press (the weapon fires on the
                // press edge; a constant 0x100 fired once, verified with projectile counts). Seated, the two triggers
                // are apart (a person's recorded play, Nov 7): left click +0x00 0x00040100 and +0x18 1.0, right click
                // +0x00 0x00892000 and +0x1C 1.0, the second the Ghost's / Spectre's / Banshee's / Wraith's boost and
                // the Scorpion driver's machine gun (HB_BTN_FIRE2); on foot fire pulls both (both guns dual-wielded)
                bool seated = unit && *(uint32_t*)(unit + 0x14) != 0xFFFFFFFFu;
                bool fire = (b & HB_BTN_FIRE) != 0, fire2 = seated ? (b & HB_BTN_FIRE2) != 0 : fire;
                if (fire) flags |= (seated ? 0x00040000u : 0x008C0000u) | ((prev[i] & HB_BTN_FIRE) ? 0 : 0x100);
                if (seated && fire2) flags |= 0x00892000u;
                prev[i] = b;
                *(uint32_t*)act = flags;
                *(float*)(act + 0x08) = a.yaw;
                *(float*)(act + 0x0C) = a.pitch;
                *(float*)(act + 0x10) = a.forward;
                *(float*)(act + 0x14) = a.strafe;
                *(float*)(act + 0x18) = fire ? 1.0f : 0.0f;
                *(float*)(act + 0x1C) = fire2 ? 1.0f : 0.0f;
                // action flags +0x20: a human's E is 0x301 on the press tick, 0x201 held, then
                // 0x41FE03 once held long ("hold E to pick up"). The bot sends the long hold plus
                // the weapon at its feet as interaction (type 1 = weapon pickup): verified, the bot
                // took the sniper on Lockout. Taps (reload) keep the low bits only.
                uint32_t w20 = *(uint32_t*)(act + 0x20) & 0xFF000000u;
                if (b & HB_BTN_ACTION) {
                    *(uint32_t*)(act + 0x20) = w20 | 0x0041FE03u;
                    uint32_t target = unit && hb_use_picks_up(b) && *(uint32_t*)(unit + 0x14) == 0xFFFFFFFFu
                                      ? h2_pickup_target(unit) : 0xFFFFFFFFu;   // on foot, no seat asked
                    if (target != 0xFFFFFFFFu) {
                        *(int16_t*)(act + 0x2C) = 1;
                        *(uint32_t*)(act + 0x30) = target;
                    } else if (unit) {
                        h2_board(act, unit, b);
                    }
                } else {
                    // (seated, a person's idle flags are 0 (or 0x41FE00 after a hold), never 0x400200, Use held:
                    // recorded Nov 7. With it every bot was put out of a Ghost 0.5 s after getting in)
                    *(uint32_t*)(act + 0x20) = w20 | (seated ? 0u : 0x00400200u);
                }
                // reload: the player's R sets bits 0 and 21 here (tools/decode_buttons.py reload=r); bit 21 alone
                // reloads nothing (tools/reload_probe.py h2: 0 of 7). Set natively, not through the button table: the
                // table clears its mask every tick, and bit 0 is also the action bit written just above
                if (b & HB_BTN_RELOAD) *(uint32_t*)(act + 0x20) |= 0x00200001u;
                static uint32_t map_prev[HB_MAX_PLAYERS];      // v8 decoded buttons (shared.h)
                hb_apply_buttons(g_shm, 2, act, H2_ACTION, b, map_prev[i]);
                map_prev[i] = b;
                *(uint32_t*)(actions + 8) |= 1u << index;
            }
        } __except (EXCEPTION_EXECUTE_HANDLER) { g_shm->cmd_fault = 2; }
    }
    o_update(actions);
}

// Ragdolls in every Halo 2 Classic game, however many players (a player's request; the separate "Halo 2 Ragdolls" mod,
// Oct 29, is part of the bot mod now). halo2.dll (MCC 1.3528) gives a dead body its ragdoll only while 8 or fewer players are in the
// game: its ragdoll budget check (RVA 0x6A5BB0) jumps to "no ragdoll" at 9 or more (cmp esi, 8 / jge, the jump at RVA
// 0x6A5BFA); bodies froze in their death pose in a 16-player game. The jump becomes two NOPs, in memory only, after the
// ten bytes there are checked against the decoded build's (any other MCC build: nothing is written). The game's own limit
// of 2 bodies moving at once (3 forced) stays. As one 16-bit store: a thread running the check sees the old jump or the
// NOPs, never half of each.
static void h2_ragdolls(uint8_t* h2) {
    static const uint8_t STOCK[10] = {0x83, 0xFE, 0x08, 0x48, 0x8B, 0x74, 0x24, 0x50, 0x7D, 0x39};
    static const uint8_t DONE[10] = {0x83, 0xFE, 0x08, 0x48, 0x8B, 0x74, 0x24, 0x50, 0x90, 0x90};
    uint8_t* p = h2 + 0x6A5BF2;
    __try {
        if (!memcmp(p, DONE, sizeof DONE)) { logf("h2 ragdolls: already on at halo2 %p", h2); return; }
        if (memcmp(p, STOCK, sizeof STOCK)) { logf("h2 ragdolls: not the MCC 1.3528 build decoded: left alone"); return; }
        DWORD old;
        if (!VirtualProtect(p + 8, 2, PAGE_EXECUTE_READWRITE, &old)) { logf("h2 ragdolls: could not unprotect (%lu)", GetLastError()); return; }
        *(volatile uint16_t*)(p + 8) = 0x9090;
        VirtualProtect(p + 8, 2, old, &old);
        FlushInstructionCache(GetCurrentProcess(), p + 8, 2);
        logf("h2 ragdolls: on at any player count (halo2 %p)", h2);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        logf("h2 ragdolls: unreadable at halo2 %p", h2);
    }
}

// Theater for Halo 2 Classic (docs/THEATER_RE.md): halo2.dll still has Halo 2's film recorder. When a game starts it
// records the whole game (every tick's simulation update) to saved_films\lastfilmHOST if the byte DAT_1818a4320 (the
// debug global film_record, nothing in the game sets it) is on. The two reads of it (cmp byte ptr [rip+..], dh at RVA
// 0x8664c7 and 0x8666a2) are checked against the decoded build first; any other MCC build: left alone.
static void h2_film_record(uint8_t* h2) {
    static const uint8_t READ1[6] = {0x38, 0x35, 0x53, 0xDE, 0x03, 0x01}, READ2[6] = {0x38, 0x35, 0x78, 0xDC, 0x03, 0x01};
    __try {
        if (memcmp(h2 + 0x8664c7, READ1, 6) || memcmp(h2 + 0x8666a2, READ2, 6)) { logf("h2 films: not the MCC 1.3528 build decoded: off"); return; }
        *(volatile uint8_t*)(h2 + 0x18a4320) = 1;
        logf("h2 films: recording every game (halo2 %p)", h2);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        logf("h2 films: unreadable at halo2 %p", h2);
    }
}

// Playing a film (docs/THEATER_RE.md): MCC starts a Halo 2 Classic game through halo2's launch FUN_180039050, which
// plays a film instead when the pointer at its launch parameters (DAT_181a840a0) + 180000 is set (state 3 ->
// FUN_1806f6d80(path)); MCC fills it only for titles with a Theater. A film chosen to play (the path, UTF-8, in
// <films>\h2_play.txt, one shot) goes into that slot as the launch starts.
typedef void(__fastcall* h2_launch_fn)();
static h2_launch_fn o_launch;
static char g_film_path[MAX_PATH];
void film_dir(wchar_t* out);
static void __fastcall h_launch() {
    __try {
        uint8_t* p = g_h2 + 0x1a840a0;
        void* fp0 = *(void**)(p + 180000);
        logf("h2 films: launch (interface %d, flags %02x, mode %d, film slot %p '%.80s')", *(void**)(g_h2 + 0x1e8ce68) != nullptr,
             p[0], *(int32_t*)(p + 0xc), fp0, fp0 && !IsBadReadPtr(fp0, 2) ? (const char*)fp0 : "");
        if (fp0 && !IsBadReadPtr(fp0, 2) && ((const char*)fp0)[1] == 0) logf("h2 films: film slot is UTF-16: '%.80ls'", (const wchar_t*)fp0);
        if (fp0 && !IsBadReadPtr(fp0, 2) && ((const char*)fp0)[1] != 0) strncpy_s(g_th2_path, (const char*)fp0, _TRUNCATE);   // (the Theater's skip back reopens it)
        h2_film_over_read();
    } __except (EXCEPTION_EXECUTE_HANDLER) {}
    __try {
        wchar_t dir[MAX_PATH], f[MAX_PATH];
        film_dir(dir);
        swprintf_s(f, L"%s\\h2_play.txt", dir);
        FILE* fp = _wfopen(f, L"rb");
        if (fp) {
            size_t n = fread(g_film_path, 1, sizeof g_film_path - 1, fp);
            fclose(fp);
            DeleteFileW(f);
            while (n && (g_film_path[n - 1] == '\n' || g_film_path[n - 1] == '\r' || g_film_path[n - 1] == ' ')) n--;
            g_film_path[n] = 0;
            uint8_t** slot = (uint8_t**)(g_h2 + 0x1a840a0 + 180000);
            if (n && *(void**)(g_h2 + 0x1e8ce68) && !*slot) {
                *slot = (uint8_t*)g_film_path;
                logf("h2 films: this launch plays %s", g_film_path);
            } else {
                logf("h2 films: could not put the film in this launch (%zu chars, interface %d, slot %p)", n,
                     *(void**)(g_h2 + 0x1e8ce68) != nullptr, *slot);
            }
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        logf("h2 films: fault reading the film to play");
    }
    o_launch();
}

// Background recording: every finished game's film is saved_films\lastfilm.film in MCC's Halo2 temporary folder, and
// the next game's overwrites it (as Halo 3's autosave). Each new one is copied to <films>\h2c\<date-time>.film; the
// newest KEEP_FILMS stay
static void h2_keep_films() {
    static DWORD last_look;
    static FILETIME seen;
    if (GetTickCount() - last_look < 2000) return;
    last_look = GetTickCount();
    wchar_t home[MAX_PATH], src[MAX_PATH], dir[MAX_PATH], dst[MAX_PATH];
    if (!GetEnvironmentVariableW(L"USERPROFILE", home, MAX_PATH)) return;
    swprintf_s(src, L"%s\\AppData\\LocalLow\\MCC\\Temporary\\Halo2\\saved_films\\lastfilm.film", home);
    WIN32_FILE_ATTRIBUTE_DATA a;
    if (!GetFileAttributesExW(src, GetFileExInfoStandard, &a) || a.nFileSizeLow <= 0x1858) return;
    if (!seen.dwLowDateTime && !seen.dwHighDateTime) { seen = a.ftLastWriteTime; return; }   // (one from before botcore)
    if (!CompareFileTime(&a.ftLastWriteTime, &seen)) return;
    seen = a.ftLastWriteTime;
    film_dir(dir);
    wcscat_s(dir, L"\\h2c");
    CreateDirectoryW(dir, nullptr);
    SYSTEMTIME t;
    GetLocalTime(&t);
    swprintf_s(dst, L"%s\\%04d%02d%02d-%02d%02d%02d.film", dir, t.wYear, t.wMonth, t.wDay, t.wHour, t.wMinute, t.wSecond);
    if (!CopyFileW(src, dst, TRUE)) { logf("h2 films: could not keep the film (%lu)", GetLastError()); return; }
    logf("h2 films: kept %ls (%lu bytes)", dst, a.nFileSizeLow);
    // and where MCC's Theater looks for a game's films: Temporary\UserContent\Halo2\Movie\asq_<map>_<id>_<time>.mov (as
    // Halo 3's), the map from the film's game options (scenario path at file +8 +0xA8, UTF-16)
    {
        wchar_t movie[MAX_PATH], scen[64] = L"", map[16] = L"film";
        swprintf_s(movie, L"%s\\AppData\\LocalLow\\MCC\\Temporary\\UserContent\\Halo2\\Movie", home);
        CreateDirectoryW(movie, nullptr);
        FILE* fp = _wfopen(dst, L"rb");
        if (fp) { fseek(fp, 8 + 0xA8, SEEK_SET); fread(scen, 2, 63, fp); fclose(fp); scen[63] = 0; }
        const wchar_t* last = wcsrchr(scen, L'\\');
        if (last && last[1]) { wcsncpy_s(map, last + 1, 7); }
        wchar_t mov[MAX_PATH];
        swprintf_s(mov, L"%s\\asq_%s_%08X_%08X.mov", movie, map, GetTickCount() ^ (DWORD)(uintptr_t)&t, (DWORD)time(nullptr));
        if (CopyFileW(dst, mov, TRUE)) {
            // the time it was recorded, for the Theater's date (the options' +0x18 is not it), in the header's unused
            // bytes at 0x1810 (zero in every film written; halo2's film opener does not read them)
            FILE* w = _wfopen(mov, L"r+b");
            if (w) { uint64_t now = (uint64_t)time(nullptr); fseek(w, 0x1810, SEEK_SET); fwrite(&now, 8, 1, w); fclose(w); }
            logf("h2 films: for the Theater %ls", mov);
        } else {
            logf("h2 films: could not put the film in the Theater (%lu): %ls", GetLastError(), mov);
        }
    }
    const int KEEP_FILMS = 25;                       // the oldest beyond these go (names sort by date)
    wchar_t pat[MAX_PATH], names[64][32];
    swprintf_s(pat, L"%s\\*.film", dir);
    int n = 0;
    WIN32_FIND_DATAW fd;
    HANDLE h = FindFirstFileW(pat, &fd);
    if (h == INVALID_HANDLE_VALUE) return;
    do { if (n < 64 && wcslen(fd.cFileName) < 32) wcscpy_s(names[n++], fd.cFileName); } while (FindNextFileW(h, &fd));
    FindClose(h);
    qsort(names, n, sizeof names[0], [](const void* x, const void* y) { return wcscmp((const wchar_t*)x, (const wchar_t*)y); });
    for (int i = 0; i + KEEP_FILMS < n; i++) {
        swprintf_s(dst, L"%s\\%s", dir, names[i]);
        DeleteFileW(dst);
    }
}

// Starting a game (FUN_180034e40(game options 0x1800 or null)): the film opener asks for the film's game (its options
// with the playback type at +0x2BA = 1), but a launch from the lobby then asks again with the lobby's options and the
// film's request is lost (live Nov 13: a normal game ran, playback type 0, the film sat at its header). While a film is
// open (state 1), every start is the film's
typedef void(__fastcall* h2_start_fn)(uint8_t* options);
static h2_start_fn o_start;
static uint8_t g_film_opts[0x1800];
static void __fastcall h_start(uint8_t* options) {
    __try {
        uint8_t* film = g_h2 + 0x15f4d60;
        static int calls;
        if (calls++ < 20) logf("h2 films: game start (options %p, playback %d, film state %d)", options,
                               options ? *(int16_t*)(options + 0x2BA) : -1, *(volatile int32_t*)(g_h2 + 0x15f4d54));
        if (*(volatile int32_t*)(g_h2 + 0x15f4d54) == 1 && options) {
            // The request is queued and halo2's main loop starts it between ticks (FUN_180034ed0 -> FUN_180035030), but
            // under MCC (its interface DAT_181e8ce68) the loop drops it unless DAT_181e8ce73 is set (the lobby's game
            // ran instead, live). Starting it at once from inside a tick stopped the new simulation before its first
            // tick (live). So the flag is set and the queued start runs at its proper time; it is cleared once the
            // film's first tick runs (h_update)
            *(volatile uint8_t*)(g_h2 + 0x1e8ce73) = 1;
            logf("h2 films: the film's game queued");
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) { logf("h2 films: fault starting the film's game"); }
    o_start(options);
}

// MCC reads each game's films through the game's data access object (exported CreateDataAccess): slot 7 makes a film's
// metadata from its bytes (halo3: FUN_1800e00e0). halo2's (vtable RVA 0xbe2038) answers nothing there. Probe: does MCC
// ask halo2 at all (a .mov in UserContent\Halo2\Movie)? Logged, still nothing returned
// The metadata object MCC gets back: the same 20 getters as Halo 3's film metadata (halo3 vtable 0x18076b080, decoded
// from its getters: logs/tmp/film/h3_md.c), filled from the H2C film's header (0x1858 bytes: u32 build, u32, the game
// options 0x1800 at +8: tick rate +0x8, date +0x18, map block {map id, 0, 0x88880000, 0} at +0x90 (Halo 3's at its
// +0x2dc: 79 Construct, 86 Sandtrap; H2C Lockout 44), scenario path +0xA8, variant name key +0x2C8 ("$slayer"),
// the author's xuid +0xACC; the tick count at file +0x180C)
struct H2FilmMeta {
    void** vt;
    uint8_t hdr[0x1858];
    wchar_t title[64], desc[128];
    uint8_t zero[64];
};
static int g_meta_log;
#define MLOG(name) do { if (g_meta_log < 120) { g_meta_log++; logf("h2 films: metadata " name); } } while (0)
static void __fastcall fm_free(H2FilmMeta* m) { MLOG("free"); if (m) free(m); }
static const wchar_t* __fastcall fm_title(H2FilmMeta* m) { MLOG("title"); return m->title; }
static const wchar_t* __fastcall fm_desc(H2FilmMeta* m) { MLOG("description"); return m->desc; }
static uint64_t __fastcall fm_author(H2FilmMeta* m) { MLOG("author"); return *(uint64_t*)(m->hdr + 8 + 0xACC); }
static uint64_t __fastcall fm_date(H2FilmMeta* m) {
    MLOG("date");
    uint64_t t = *(uint64_t*)(m->hdr + 0x1810);          // (stamped when kept: h2_keep_films)
    return t ? t : *(uint32_t*)(m->hdr + 8 + 0x18);
}
static uint32_t __fastcall fm_length(H2FilmMeta* m) {
    MLOG("length");
    int rate = *(int32_t*)(m->hdr + 8 + 0x8);
    return (uint32_t)(*(int32_t*)(m->hdr + 0x180C) / (rate > 0 ? rate : 60));
}
static uint16_t __fastcall fm_map_short(H2FilmMeta*) { MLOG("map id (short)"); return 0; }
static uint8_t __fastcall fm_flag(H2FilmMeta*) { MLOG("flag 0x19c"); return 1; }
static uint8_t __fastcall fm_flag2(H2FilmMeta*, uint32_t* a, uint8_t* b) {
    MLOG("flag2"); if (a) *a = 0xFFFFFFFFu; if (b) *b = 0; return 0;
}
static const char* __fastcall fm_build(H2FilmMeta*) { MLOG("build"); return "untracked version"; }
static int __fastcall fm_kind(H2FilmMeta*) { MLOG("kind 0x1c0"); return 0; }
static int __fastcall fm_mode(H2FilmMeta*) { MLOG("mode 0x2b0"); return 3; }
static const void* __fastcall fm_static(H2FilmMeta* m) { MLOG("static 12/13"); return m->zero; }
static int __fastcall fm_minus1(H2FilmMeta*) { MLOG("slot 14"); return -1; }
static const void* __fastcall fm_block15(H2FilmMeta* m) { MLOG("block 0x2cc"); return m->zero; }
static const void* __fastcall fm_map_block(H2FilmMeta* m) { MLOG("map block 0x2dc"); return m->hdr + 8 + 0x90; }
static uint8_t __fastcall fm_blob(H2FilmMeta*, void** p, uint64_t* n) { MLOG("blob 17/18"); if (p) *p = nullptr; if (n) *n = 0; return 0; }
static void __fastcall fm_fill(H2FilmMeta* m, uint8_t* out) {
    MLOG("fill 19");
    if (!out) return;
    out[0] = (uint8_t)((out[0] & ~8) | 8);
    out[10] = (uint8_t)*(int32_t*)(m->hdr + 8 + 0x8);
    *(uint32_t*)(out + 0xC) = 3;
    memcpy(out + 0x14, m->hdr + 8 + 0x90, 16);
    memset(out + 0x24, 0, 16);
    *(uint16_t*)(out + 0x3C) = 0;
}
static void* g_fm_vt[20] = {
    (void*)&fm_free, (void*)&fm_title, (void*)&fm_desc, (void*)&fm_author, (void*)&fm_date, (void*)&fm_length,
    (void*)&fm_map_short, (void*)&fm_flag, (void*)&fm_flag2, (void*)&fm_build, (void*)&fm_kind, (void*)&fm_mode,
    (void*)&fm_static, (void*)&fm_static, (void*)&fm_minus1, (void*)&fm_block15, (void*)&fm_map_block,
    (void*)&fm_blob, (void*)&fm_blob, (void*)&fm_fill};

static void* __fastcall h2_film_meta(void* self, const uint8_t* data, uint32_t size) {
    static int calls;
    if (calls++ < 20) logf("h2 films: MCC asks for a film's metadata (%u bytes)", size);
    if (!data || size < 0x1858) return nullptr;
    H2FilmMeta* m = (H2FilmMeta*)calloc(1, sizeof(H2FilmMeta));
    if (!m) return nullptr;
    m->vt = g_fm_vt;
    memcpy(m->hdr, data, sizeof m->hdr);
    const uint8_t* opt = m->hdr + 8;
    wcsncpy_s(m->title, (const wchar_t*)(opt + 0x2C8), 63);           // the variant's name key ("$slayer")
    wchar_t map[48] = L"";
    const wchar_t* scen = (const wchar_t*)(opt + 0xA8);
    const wchar_t* last = wcsrchr(scen, L'\\');
    wcsncpy_s(map, last ? last + 1 : scen, 47);
    if (map[0] >= L'a' && map[0] <= L'z') map[0] -= 32;
    __time64_t tt = *(uint64_t*)(m->hdr + 0x1810) ? (__time64_t)*(uint64_t*)(m->hdr + 0x1810) : *(uint32_t*)(opt + 0x18);
    struct tm lt;
    wchar_t when[64] = L"";
    if (!_localtime64_s(&lt, &tt)) wcsftime(when, 64, L"%A %B %d, %Y %H:%M:%S", &lt);
    const wchar_t* gt = m->title[0] == L'$' ? m->title + 1 : m->title;
    swprintf_s(m->desc, L"%s on %s, %s", gt, map, when);
    if (m->desc[0] >= L'a' && m->desc[0] <= L'z') m->desc[0] -= 32;
    return m;
}
static void h2_film_meta_patch(uint8_t* h2) {
    void** slot = (void**)(h2 + 0xbe2038 + 7 * 8);
    __try {
        if (*slot == (void*)&h2_film_meta) return;               // (already: mcc_theater.cpp asks before each scan)
        if (*slot != (void*)(h2 + 0x30ce0)) { logf("h2 films: data access slot 7 is not the decoded build's"); return; }
        DWORD old;
        if (!VirtualProtect(slot, 8, PAGE_READWRITE, &old)) return;
        *slot = (void*)&h2_film_meta;
        VirtualProtect(slot, 8, old, &old);
        logf("h2 films: film metadata answered by botcore");
    } __except (EXCEPTION_EXECUTE_HANDLER) {}
}

// MCC's content scan (mcc_theater.cpp) calls this first: halo2 is unloaded and loaded again around each Halo 2 session
// and MCC rescans right then, before botcore's loop could put the film metadata back (live: the H2C film was missing
// from the list after a film)
void h2_film_meta_ensure() {
    uint8_t* h2 = (uint8_t*)GetModuleHandleW(L"halo2.dll");
    if (h2) h2_film_meta_patch(h2);
}

// MCC's launch block arrives at FUN_180039ce0(params, 0x2bf30 bytes). A multiplayer launch (mode +0xC = 3) by the host
// (flags bit 3) needs a game variant (+0x344 non-zero), else error 4 "is_valid_host_game_variant" and halo2 quits (live
// Nov 13: MCC's Theater launch of an H2C film carried the film's path at +180000 and no variant; MCC crashed in halo2's
// shutdown). A film launch takes its game from the film (state 3, FUN_1806f6d80), so with a film path the variant
// check is let through
typedef void(__fastcall* h2_params_fn)(uint8_t* params);
static h2_params_fn o_params;
static void __fastcall h_params(uint8_t* params) {
    __try {
        void* film = *(void**)(params + 180000);
        if (film && *(int32_t*)(params + 0x344) == 0) {
            *(int32_t*)(params + 0x344) = 1;
            logf("h2 films: MCC's Theater launches %.200s", (const char*)film);
            *(volatile uint8_t*)(g_h2 + 0x18a4320) = 0;       // (a film plays: nothing recorded over it)
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {}
    o_params(params);
}

// called from botcore's main loop: hook halo2.dll when it is loaded (again)
void h2_watch() {
    uint8_t* h2 = (uint8_t*)GetModuleHandleW(L"halo2.dll");
    if (!h2) return;
    h2_keep_films();
    if (h2 == g_h2) {                                    // a film left (state off 1): the Theater's camera and speed back
        static int32_t last;
        int32_t st = 0;
        __try { st = *(volatile int32_t*)(h2 + 0x15f4d54); } __except (EXCEPTION_EXECUTE_HANDLER) {}
        if (last == 1 && st != 1) h2_theater_end();
        last = st;
    }
    // A film's game over (its simulation stopped, DAT_1818a432a, in the playback world type 2): halo2 shows its own game
    // over board and waits for a word from MCC that never comes for Halo 2 (live: stuck there, MCC's "end the film" too).
    // It used to end the session after a few seconds (DAT_180e70d38): now the Theater pauses on the last frame before it,
    // and the viewer goes back or presses End Film (Nov 13)
    __try {
        static DWORD over_since;
        uint8_t* world = *(uint8_t**)(h2 + 0x18a4338);
        bool over = world && *(int32_t*)(world + 0x10) == 2 && *(volatile uint8_t*)(h2 + 0x18a432a);
        if (!over) over_since = 0;
        else if (!over_since) { over_since = GetTickCount(); h2_film_over(); }
    } __except (EXCEPTION_EXECUTE_HANDLER) {}
    bool hooked = false;
    __try { hooked = h2 == g_h2 && !memcmp(h2 + H2_PLAYERS_UPDATE, g_h2_patch, 5); }
    __except (EXCEPTION_EXECUTE_HANDLER) { hooked = false; }
    if (hooked) return;
    Sleep(500);
    if ((uint8_t*)GetModuleHandleW(L"halo2.dll") != h2) return;
    if (g_h2) { MH_RemoveHook(g_h2 + H2_PLAYERS_UPDATE); MH_RemoveHook(g_h2 + 0x39050); MH_RemoveHook(g_h2 + 0x34e40); MH_RemoveHook(g_h2 + 0x39ce0); MH_RemoveHook(g_h2 + 0x706ab0); MH_RemoveHook(g_h2 + 0x6d5d10); MH_RemoveHook(g_h2 + 0x6d6b50); MH_RemoveHook(g_h2 + 0x69d040); }
    g_h2 = h2;
    for (int i = 0; i < HB_MAX_PLAYERS; i++) g_shm->bot_player_index[i] = -1;
    if (MH_CreateHook(h2 + H2_PLAYERS_UPDATE, (void*)&h_update, (void**)&o_update) != MH_OK ||
        MH_EnableHook(h2 + H2_PLAYERS_UPDATE) != MH_OK) {
        logf("h2 hook failed at %p", h2);
        return;
    }
    memcpy(g_h2_patch, h2 + H2_PLAYERS_UPDATE, 5);
    g_shm->game = 2;
    logf("h2 hooks on at halo2 %p: players update +0x%llx", h2, (unsigned long long)H2_PLAYERS_UPDATE);
    h2_ragdolls(h2);
    h2_film_record(h2);
    h2_film_meta_patch(h2);
    h2_theater_install(h2);
    static const uint8_t LAUNCH[16] = {0x48, 0x89, 0x6C, 0x24, 0x18, 0x56, 0x48, 0x81, 0xEC, 0xB0, 0x09, 0x00, 0x00, 0x33, 0xED, 0x48};
    if (memcmp(h2 + 0x39050, LAUNCH, sizeof LAUNCH)) logf("h2 films: launch not the decoded build: no playing films");
    else if (MH_CreateHook(h2 + 0x39050, (void*)&h_launch, (void**)&o_launch) != MH_OK || MH_EnableHook(h2 + 0x39050) != MH_OK)
        logf("h2 films: launch hook failed");
    static const uint8_t START[12] = {0x40, 0x53, 0x48, 0x83, 0xEC, 0x20, 0x48, 0x8B, 0xD9, 0x48, 0x85, 0xC9};
    static const uint8_t START_NOW[11] = {0x48, 0x89, 0x5C, 0x24, 0x08, 0x48, 0x89, 0x74, 0x24, 0x10, 0x57};
    if (memcmp(h2 + 0x34e40, START, sizeof START) || memcmp(h2 + 0x35030, START_NOW, sizeof START_NOW)) logf("h2 films: game start not the decoded build");
    else if (MH_CreateHook(h2 + 0x34e40, (void*)&h_start, (void**)&o_start) != MH_OK || MH_EnableHook(h2 + 0x34e40) != MH_OK)
        logf("h2 films: start hook failed");
    static const uint8_t PARAMS[12] = {0x40, 0x53, 0x48, 0x81, 0xEC, 0x30, 0x03, 0x00, 0x00, 0x48, 0x8B, 0xD1};
    if (memcmp(h2 + 0x39ce0, PARAMS, sizeof PARAMS)) logf("h2 films: launch params not the decoded build");
    else if (MH_CreateHook(h2 + 0x39ce0, (void*)&h_params, (void**)&o_params) != MH_OK || MH_EnableHook(h2 + 0x39ce0) != MH_OK)
        logf("h2 films: launch params hook failed");
}

// --- the Theater's controls (theater.cpp) over a Halo 2 film (docs/THEATER_RE.md "H2C controls"). halo2 has the same
// scripted camera as halo1: camera_control (FUN_1806D58A0, the script function) puts the four directors (fn at
// halo2+0x15EB230, 0x150 apart) on FUN_1807186D0, which reads the struct at [halo2+0x1648950]: +0 on, +2 mode (a
// word: 1 a point, or an offset from the object at +0x3C; 4 the object's first person view), +0x18 position, +0x24
// forward, +0x30 up, +0x3C object (-1 none), +0x42 a sub mode (0). The game's speed is the time globals'
// ([halo2+0x15FE008]) +0xC: FUN_180706AB0 scales the frame's ticks by it, and at 0 runs none and holds the blend
// (+0x10) at 0, so a paused film does not shake
#include "theater.h"
namespace {
const uintptr_t H2T_CAMERA_CONTROL = 0x6d58a0, H2T_DIRECTOR0_FN = 0x15eb230, H2T_SCRIPTED = 0x7186d0;
const uintptr_t H2T_CAMERA = 0x1648950, H2T_TIME = 0x15fe008, H2T_QUIT = 0xe70d38, H2T_FILM_STATE = 0x15f4d54;
const uintptr_t H2T_WORLD = 0x18a4338, H2T_FILM_HEADER = 0x15f4d58;
const uint8_t H2T_CAMERA_CONTROL_PROLOGUE[13] = {0x48, 0x89, 0x5C, 0x24, 0x18, 0x55, 0x57, 0x41, 0x56, 0x48, 0x83, 0xEC, 0x20};
bool g_th_cam;
uint32_t g_th_body[16];
float g_th_speed = 1;
volatile uint32_t g_th_ff_to = 0xFFFFFFFFu;      // a seek ahead: fast to this film tick (30ths)
volatile bool g_th2_reopen;                      // a skip back: the film opened again (h2_theater_tick), then fast to g_th_ff_to
volatile DWORD g_th2_reopen_until;               // (until then a missing world is the reload, not the film's end)
uint32_t g_th2_req_tick;                         // (the world's tick when it was asked: a lower one is the new world)
const float H2T_SEEK_SPEED = 8.0f;

int th_rate() { int r = g_h2 ? *(int32_t*)(g_h2 + H2T_FILM_HEADER + 0x10) : 0; return r > 0 ? r : 30; }
uint32_t th_world_tick() { uint8_t* w = *(uint8_t**)(g_h2 + H2T_WORLD); return w ? *(uint32_t*)(w + 0x34) : 0; }

bool th2_playing() {
    // (a skip back reopens the film: through its map's load, the Theater stays as it was)
    __try { return g_h2 && *(volatile int32_t*)(g_h2 + H2T_FILM_STATE) == 1 && (*(uint8_t**)(g_h2 + H2T_WORLD) || (g_th2_reopen_until && (int)(g_th2_reopen_until - GetTickCount()) > 0)); }
    __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}
uint32_t th2_now() { __try { return (uint32_t)((uint64_t)th_world_tick() * 30 / th_rate()); } __except (EXCEPTION_EXECUTE_HANDLER) { return 0; } }
// the film's length: its header's ticks, or up to just before its game over (halo2 records on past it and shows its own
// board there; the end holds the last frame, Nov 13)
uint32_t th2_length() {
    __try {
        uint32_t n = *(uint32_t*)(g_h2 + H2T_FILM_HEADER + 0x180C);
        if (g_th2_over_tick > 4 && g_th2_over_tick - 2 < n) n = g_th2_over_tick - 2;
        return (uint32_t)((uint64_t)n * 30 / th_rate());
    } __except (EXCEPTION_EXECUTE_HANDLER) { return 0; }
}

uint32_t th2_body(int i) {
    uint8_t* p = (i >= 0 && i < 16) ? h2_player(i) : nullptr;
    uint32_t unit = p && *(uint16_t*)p ? *(uint32_t*)(p + 0x2C) : 0xFFFFFFFFu;
    if (h2_object(unit)) g_th_body[i] = unit;
    return i >= 0 && i < 16 && h2_object(g_th_body[i]) ? g_th_body[i] : 0xFFFFFFFFu;
}

void th2_players(th_player out[16]) {
    memset(out, 0, sizeof(th_player) * 16);
    __try {
        for (int i = 0; i < 16; i++) {
            uint8_t* p = h2_player(i);
            if (!p || !*(uint16_t*)p) continue;
            out[i].used = true;
            wcsncpy_s(out[i].name, (const wchar_t*)(p + 0x3C), 15);
            out[i].team = *(uint8_t*)(p + 0xB8);
            out[i].alive = h2_object(*(uint32_t*)(p + 0x2C)) != nullptr;
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {}
}

bool th2_focus(int player, float pos[3], float fwd[3]) {
    __try {
        uint8_t* o = h2_object(th2_body(player));
        if (!o) return false;
        memcpy(pos, o + 0x64, 12);                   // object +0x64 position, +0x70 body forward
        memcpy(fwd, o + 0x70, 12);
        return true;
    } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}

void th2_control(bool on) {
    // (on again whenever director 0 is off the scripted camera: a map's start puts it back, as halo1's did)
    if (g_th_cam == on && (!on || *(void**)(g_h2 + H2T_DIRECTOR0_FN) == (void*)(g_h2 + H2T_SCRIPTED))) return;
    if (memcmp(g_h2 + H2T_CAMERA_CONTROL, H2T_CAMERA_CONTROL_PROLOGUE, sizeof H2T_CAMERA_CONTROL_PROLOGUE)) {
        static bool said;
        if (!said) { said = true; logf("h2 theater: camera_control not the decoded build: the game's camera stays"); }
        return;
    }
    ((void(__fastcall*)(char))(g_h2 + H2T_CAMERA_CONTROL))(on ? 1 : 0);
    g_th_cam = on;
}

// First person is halo2's own camera (FUN_18077C9F0: the player's gun and HUD, the player's field of view), with local
// player 0's control ([halo2+0x15E40D0], 0xB8 a player: +0x18 unit, +0x38 yaw, +0x3C pitch) on the followed unit
// and its aim (unit +0x168), and local player 0's slot ([halo2+0xE80A20] + 0xC, FUN_18069D040: whose HUD and gun) on
// its player, from the directors (FUN_1806D5D10, after the frame's ticks) to the next frame's tick count (FUN_180706AB0)
// as halo1's. halo2 builds the HUD and the gun in its ticks, so a bot's eyes show neither (lent through the ticks, it
// crashed on a bot's handle: film39); the player's own has both. The scripted camera's first person (mode 4) has no gun or
// HUD and its own narrow field of view (too narrow, and no gun, Nov 13)
const uintptr_t H2T_FRAME_TICKS = 0x706ab0, H2T_DIRECTOR_UPDATE = 0x6d5d10, H2T_RAY = 0x75b2c0;
const uintptr_t H2T_PLAYER_CONTROL = 0x15e40d0, H2T_LOCAL_PLAYERS = 0xe80a20, H2T_USER_FOV = 0xb185dc;
const uint8_t H2T_FRAME_TICKS_PROLOGUE[13] = {0x48, 0x8B, 0xC4, 0x56, 0x41, 0x56, 0x48, 0x81, 0xEC, 0x98, 0x00, 0x00, 0x00};
const uint8_t H2T_DIRECTOR_UPDATE_PROLOGUE[15] = {0x48, 0x8B, 0xC4, 0x48, 0x89, 0x58, 0x08, 0x48, 0x89, 0x70, 0x10, 0x48, 0x89, 0x78, 0x18};
const uint8_t H2T_RAY_PROLOGUE[9] = {0x48, 0x83, 0xEC, 0x48, 0xF3, 0x41, 0x0F, 0x10, 0x00};
typedef void(__fastcall* h2_frame_ticks_fn)(float dt, float* frac, uint32_t* ticks);
typedef void(__fastcall* h2_director_update_fn)(float dt);
typedef char(__fastcall* h2_ray_fn)(uint32_t flags, const float* from, const float* to, uint32_t a, uint32_t b, void* result);
h2_frame_ticks_fn g_h2_frame_ticks_orig;
h2_director_update_fn g_h2_director_orig;
h2_ray_fn g_h2_ray;
volatile uint32_t g2_fp_unit = 0xFFFFFFFFu;
bool g2_lent;
uint32_t g2_real_local = 0xFFFFFFFFu;
volatile float g2_orbit_off[3], g2_free_want[3], g2_free_at[3];
volatile uint32_t g2_orbit_unit = 0xFFFFFFFFu;
volatile bool g2_free_on;

// how much of the line from -> to is clear of the world (halo2's observer keeps its cameras out of walls with this
// test: FUN_18075B2C0(0x808C0F, from, to, -1, -1, result), result +4 the clear part), 0..1; 1 without the test
float h2_ray_clear(const float from[3], const float to[3], uint32_t ignore = 0xFFFFFFFFu) {
    if (!g_h2_ray) return 1;
    __try {
        uint8_t res[0x100] = {};
        if (!g_h2_ray(0x808c0f, from, to, ignore, 0xFFFFFFFFu, res)) return 1;
        float t = *(float*)(res + 4);
        return t < 0 ? 0 : t > 1 ? 1 : t;
    } __except (EXCEPTION_EXECUTE_HANDLER) { return 1; }
}

// A bot's first person gun: halo2's first person weapon and HUD code (0x81B000..0x837000: every function there asks
// FUN_18069D040 which player local player 0 is) runs in the ticks, where the slot is the real one again, so a bot's eyes
// had no gun. FUN_18069D040 answers those callers alone (by return address) with the followed player while the view is
// a bot's eyes; the rest of the game (the simulation: lending the slot through the ticks crashed) keeps the real one
const uintptr_t H2T_LOCAL_PLAYER = 0x69d040, H2T_FPW_LO = 0x81b000, H2T_FPW_HI = 0x837000;
const uint8_t H2T_LOCAL_PLAYER_PROLOGUE[16] = {0x83, 0xF9, 0xFF, 0x74, 0x0F, 0x48, 0x8B, 0x05, 0xD4, 0x39, 0x7E, 0x00, 0x48, 0x63, 0xC9, 0x8B};
typedef uint32_t(__fastcall* h2_local_player_fn)(int local);
h2_local_player_fn g_h2_local_player_orig;
volatile uint32_t g2_fpw_player = 0xFFFFFFFFu;   // the followed bot's player (the slot's form) while in its eyes

// (the lent player checked on every call: a skip back reopened the film while a bot's eyes were up, the new game had no
// such player yet, and halo2 read a missing unit, FUN_18081AA18, gun3)
bool h2_lend_ok(uint32_t lend) {
    __try {
        if (!th2_playing() || g_th2_reopen || g_th2_reopen_until || !*(uint8_t**)(g_h2 + H2T_WORLD)) return false;
        uint8_t* p = h2_player(lend & 0xFFFF);
        if (!p || !*(uint16_t*)p || ((lend >> 16) && *(uint16_t*)p != (lend >> 16))) return false;
        uint32_t u = *(uint32_t*)(p + 0x2C);
        return u == g2_fp_unit && h2_object(u) != nullptr;
    } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}

uint32_t __fastcall h2_local_player_hook(int local) {
    uint32_t lend = g2_fpw_player;
    if (local == 0 && lend != 0xFFFFFFFFu) {
        uintptr_t ra = (uintptr_t)_ReturnAddress() - (uintptr_t)g_h2;
        if (ra >= H2T_FPW_LO && ra < H2T_FPW_HI && h2_lend_ok(lend)) return lend;
    }
    return g_h2_local_player_orig(local);
}

void h2_local_back() {
    if (g2_real_local == 0xFFFFFFFFu) return;
    if (uint8_t* lp = *(uint8_t**)(g_h2 + H2T_LOCAL_PLAYERS)) *(uint32_t*)(lp + 0xC) = g2_real_local;
    g2_real_local = 0xFFFFFFFFu;
}

void h2_fp_apply() {
    uint8_t* pc = *(uint8_t**)(g_h2 + H2T_PLAYER_CONTROL);
    uint8_t* lp = *(uint8_t**)(g_h2 + H2T_LOCAL_PLAYERS);
    if (!pc || !lp) return;
    uint32_t u = g2_fp_unit;
    uint8_t* o = u != 0xFFFFFFFFu && th2_playing() ? h2_object(u) : nullptr;
    if (o) {
        const float* a = (const float*)(o + 0x168);
        float yaw = atan2f(a[1], a[0]), z = a[2] > 1 ? 1 : a[2] < -1 ? -1 : a[2];
        if (yaw < 0) yaw += 6.2831853f;
        *(uint32_t*)(pc + 0x18) = u;
        *(float*)(pc + 0x38) = yaw;
        *(float*)(pc + 0x3C) = asinf(z);
        g2_lent = true;
        uint32_t own = g2_real_local != 0xFFFFFFFFu ? g2_real_local : *(uint32_t*)(lp + 0xC);   // (the slot's own player)
        for (int i = 0; i < 16; i++) {                // the followed unit's player into the local slot (same form)
            uint8_t* p = h2_player(i);
            if (!p || !*(uint16_t*)p || *(uint32_t*)(p + 0x2C) != u) continue;
            uint32_t h = (own >> 16) ? (((uint32_t)*(uint16_t*)p << 16) | (uint32_t)i) : (uint32_t)i;
            if (h == own) { h2_local_back(); g2_fpw_player = 0xFFFFFFFFu; }
            else { g2_real_local = own; *(uint32_t*)(lp + 0xC) = h; g2_fpw_player = h; }
            break;
        }
    } else if (g2_lent || g2_real_local != 0xFFFFFFFFu || g2_fpw_player != 0xFFFFFFFFu) {   // (back to the player's own unit and slot)
        g2_fpw_player = 0xFFFFFFFFu;
        h2_local_back();
        uint8_t* p = h2_player(*(int32_t*)(lp + 0xC) & 0xFFFF);
        if (p) *(uint32_t*)(pc + 0x18) = *(uint32_t*)(p + 0x2C);
        g2_lent = false;
    }
}

void h2_orbit_apply() {                               // the orbit stops short of walls (as ce_film.cpp's)
    uint32_t u = g2_orbit_unit;
    uint8_t* d = *(uint8_t**)(g_h2 + H2T_CAMERA);
    uint8_t* o = u != 0xFFFFFFFFu && g_th_cam && d && *(int16_t*)(d + 2) == 1 ? h2_object(u) : nullptr;
    if (!o) return;
    const float* at = (const float*)(o + 0x64);
    float from[3] = {at[0], at[1], at[2] + TH2_LOOK_AT};
    float by[3] = {g2_orbit_off[0], g2_orbit_off[1], g2_orbit_off[2] - TH2_LOOK_AT};
    float to[3] = {from[0] + by[0], from[1] + by[1], from[2] + by[2]};
    float t = h2_ray_clear(from, to, u), k = t < 1 ? fmaxf(0.08f, t - 0.1f) : 1;   // (not the followed body itself: film38 sat in its head)
    float* pos = (float*)(d + 0x18);
    // (a world point: halo2's object-relative mode keeps only the part of an offset along the look, so it gave sky, film40)
    for (int i = 0; i < 3; i++) { g2_free_at[i] = from[i] + by[i] * k; pos[i] = g2_free_at[i]; }
    *(uint32_t*)(d + 0x3C) = 0xFFFFFFFFu;
}

void h2_free_apply() {                                // the free camera stops at walls and slides along them
    uint8_t* d = *(uint8_t**)(g_h2 + H2T_CAMERA);
    if (!g2_free_on || !g_th_cam || !d || *(int16_t*)(d + 2) != 1 || *(uint32_t*)(d + 0x3C) != 0xFFFFFFFFu) return;
    const float MARGIN = 0.05f;
    float at[3] = {g2_free_at[0], g2_free_at[1], g2_free_at[2]};
    for (int k = 0; k < 3; k++) {
        float step = g2_free_want[k] - at[k];
        if (fabsf(step) < 1e-5f) continue;
        float sign = step > 0 ? 1.0f : -1.0f, to[3] = {at[0], at[1], at[2]};
        to[k] += step + sign * MARGIN;
        float t = h2_ray_clear(at, to);
        if (t >= 1) { at[k] += step; continue; }
        float moved = (step + sign * MARGIN) * t - sign * MARGIN;
        if (moved * sign > 0) at[k] += moved;
    }
    float* pos = (float*)(d + 0x18);
    for (int k = 0; k < 3; k++) { g2_free_at[k] = at[k]; pos[k] = at[k]; }
}

void __fastcall h2_director_update_hook(float dt) {
    __try { if (g2_fp_unit != 0xFFFFFFFFu || g2_lent || g2_real_local != 0xFFFFFFFFu || g2_fpw_player != 0xFFFFFFFFu) h2_fp_apply(); if (th2_playing()) { h2_orbit_apply(); h2_free_apply(); } }
    __except (EXCEPTION_EXECUTE_HANDLER) {}
    g_h2_director_orig(dt);
}

// The screen flash (damage's red, pickups): FUN_1806D6B50(local player, out) gives each frame's for a local player from
// the player effects ([halo2+0x15EB778] + i * 0xA0: +0xAE its timer, +0x58 colour; out[1] the strength). In a film it is
// the recorder's, so it shows only through the recorder's own eyes (it turned the screen red in every view,
// Nov 13)
const uintptr_t H2T_FLASH = 0x6d6b50;
const uint8_t H2T_FLASH_PROLOGUE[16] = {0x48, 0x89, 0x5C, 0x24, 0x10, 0x56, 0x48, 0x83, 0xEC, 0x40, 0x48, 0x8B, 0xDA, 0x48, 0x63, 0xF1};
typedef void(__fastcall* h2_flash_fn)(int local, int* out);
h2_flash_fn g_h2_flash_orig;

void __fastcall h2_flash_hook(int local, int* out) {
    g_h2_flash_orig(local, out);
    __try {
        if (!out || !th2_playing()) return;
        uint8_t* lp = *(uint8_t**)(g_h2 + H2T_LOCAL_PLAYERS);
        uint32_t real = g2_real_local != 0xFFFFFFFFu ? g2_real_local : lp ? *(uint32_t*)(lp + 0xC) : 0xFFFFFFFFu;
        uint8_t* p = real != 0xFFFFFFFFu ? h2_player(real & 0xFFFF) : nullptr;
        bool own_eyes = g2_fp_unit != 0xFFFFFFFFu && p && *(uint32_t*)(p + 0x2C) == g2_fp_unit;
        if (!own_eyes) out[1] = 0;
    } __except (EXCEPTION_EXECUTE_HANDLER) {}
}

void __fastcall h2_frame_ticks_hook(float dt, float* frac, uint32_t* ticks) {
    __try {                                           // (the ticks see only the real local player and unit: lent through
        h2_local_back();                              // them, halo2 crashed on a bot's handle, film39)
        uint8_t* pc = *(uint8_t**)(g_h2 + H2T_PLAYER_CONTROL);
        uint8_t* lp = *(uint8_t**)(g_h2 + H2T_LOCAL_PLAYERS);
        if (g2_lent && pc && lp) { if (uint8_t* p = h2_player(*(int32_t*)(lp + 0xC) & 0xFFFF)) *(uint32_t*)(pc + 0x18) = *(uint32_t*)(p + 0x2C); g2_lent = false; }
    } __except (EXCEPTION_EXECUTE_HANDLER) {}
    __try { h2_theater_tick(); } __except (EXCEPTION_EXECUTE_HANDLER) {}   // (a skip back: every frame, the film's end has no ticks)
    g_h2_frame_ticks_orig(dt, frac, ticks);
}

// zoom (right mouse): halo2's base field of view (+0xB185DC, a constant in .rdata that every view starts from, its first
// person and the scripted camera alike: the scripted camera's own (+0x10) is read only in cinematics, so it did not zoom,
// Nov 13) scaled while held, put back when let go and when the film ends
float g2_base_fov;
bool g2_zoomed;
void th2_zoom(float fov) {
    float* base = (float*)(g_h2 + H2T_USER_FOV);
    float ratio = fov / (70.0f * 3.14159265f / 180.0f);
    if (ratio < 0.99f) {
        if (!g2_zoomed) {
            DWORD old;
            if (!VirtualProtect(base, 4, PAGE_READWRITE, &old)) return;
            g2_base_fov = *base;
            g2_zoomed = true;
        }
        *base = g2_base_fov * ratio;
    } else if (g2_zoomed) {
        *base = g2_base_fov;
        g2_zoomed = false;
    }
}

void th2_camera(int mode, int player, const float pos[3], float yaw, float pitch, float fov) {
    __try {
        th2_zoom(mode == TH_GAME || !th2_playing() ? 99.0f : fov);
        if (mode == TH_GAME || !th2_playing()) { g2_fp_unit = 0xFFFFFFFFu; g2_free_on = false; th2_control(false); return; }
        if (!*(uint8_t**)(g_h2 + H2T_WORLD)) return;   // (a skip back's reload: nothing to point)
        uint32_t body = player >= 0 ? th2_body(player) : 0xFFFFFFFFu;
        if (mode == TH_FIRST && body != 0xFFFFFFFFu && g_h2_director_orig && g_h2_frame_ticks_orig) {
            g2_fp_unit = body;                        // (the game's camera: the director hook points it)
            g2_free_on = false;
            g2_orbit_unit = 0xFFFFFFFFu;
            th2_control(false);
            return;
        }
        g2_fp_unit = 0xFFFFFFFFu;
        if (mode == TH_THIRD && body == 0xFFFFFFFFu) return;
        th2_control(true);
        uint8_t* d = *(uint8_t**)(g_h2 + H2T_CAMERA);
        if (!g_th_cam || !d) return;
        *(float*)(d + 0x10) = 0.0f;                     // (the field of view: the player's own; zoom: th2_zoom)
        *(float*)(d + 4) = *(float*)(d + 8) = 0;      // (no blend into it)
        if (mode == TH_FIRST && body != 0xFFFFFFFFu) {   // (no hooks: the scripted camera's eyes)
            *(uint32_t*)(d + 0x3C) = body;
            *(int16_t*)(d + 0x42) = 0;
            *(int16_t*)(d + 2) = 4;
            return;
        }
        float cy = cosf(yaw), sy = sinf(yaw), cp = cosf(pitch), sp = sinf(pitch);
        float f[3] = {cy * cp, sy * cp, sp}, u[3] = {-cy * sp, -sy * sp, cp};
        if (mode == TH_THIRD) {                        // an offset from the body (the director hook stops it at walls)
            memcpy((void*)g2_orbit_off, pos, 12);
            g2_orbit_unit = body;
            g2_free_on = false;
            if (!g_h2_director_orig) memcpy(d + 0x18, pos, 12);
        } else {                                       // free: the place (the director hook moves it, stopping at walls)
            g2_orbit_unit = 0xFFFFFFFFu;
            if (!g2_free_on) { memcpy((void*)g2_free_at, pos, 12); memcpy(d + 0x18, pos, 12); }
            memcpy((void*)g2_free_want, pos, 12);
            g2_free_on = g_h2_director_orig != nullptr;
            if (!g2_free_on) memcpy(d + 0x18, pos, 12);
        }
        memcpy(d + 0x24, f, 12);
        memcpy(d + 0x30, u, 12);
        *(uint32_t*)(d + 0x3C) = 0xFFFFFFFFu;            // (third too: a world point, h2_orbit_apply)
        *(int16_t*)(d + 0x42) = 0;
        *(int16_t*)(d + 2) = 1;
    } __except (EXCEPTION_EXECUTE_HANDLER) {}
}

void th2_where(float pos[3]) { if (g2_free_on || g2_orbit_unit != 0xFFFFFFFFu) for (int k = 0; k < 3; k++) pos[k] = g2_free_at[k]; }

void th2_speed(float s) {
    g_th_speed = s;
    __try {
        uint8_t* tg = *(uint8_t**)(g_h2 + H2T_TIME);
        if (g_th_ff_to != 0xFFFFFFFFu && !g_th2_reopen && !g_th2_reopen_until && th2_now() >= g_th_ff_to) g_th_ff_to = 0xFFFFFFFFu;
        if (tg && th2_playing()) *(float*)(tg + 0xC) = g_th_ff_to != 0xFFFFFFFFu ? H2T_SEEK_SPEED : s;
    } __except (EXCEPTION_EXECUTE_HANDLER) {}
}
void th2_seek(uint32_t t) {
    uint32_t now = th2_now();
    if (t > now) g_th_ff_to = t;                      // ahead: fast to it
    else if (g_th2_path[0]) { g_th_ff_to = t; g_th2_req_tick = th_world_tick(); g_th2_reopen_until = GetTickCount() + 30000; g_th2_reopen = true; }   // back: the film again, fast to it
    else { static int said; if (said++ < 3) logf("h2 theater: skip back: the film's path is not known"); }
}
bool th2_seeking() { return g_th_ff_to != 0xFFFFFFFFu; }
void th2_eject() { __try { *(volatile uint8_t*)(g_h2 + H2T_QUIT) = 1; logf("h2 theater: End Film"); } __except (EXCEPTION_EXECUTE_HANDLER) {} }

const th_backend H2_THEATER = {th2_playing, th2_now, th2_length, th2_players, th2_focus, th2_camera, th2_speed, th2_seek, th2_seeking, th2_eject, th2_where, TH2_LOOK_AT};
}  // namespace

const th_backend* h2_theater() { return &H2_THEATER; }

// a Halo 2 film is over (h_update): the scripted camera off and the speed back to 1 for the games after it (the map is
// leaving, so only the flags: camera_control's cinematic flag [halo2+0x15EB1E8] and the camera struct's on byte)
static void h2_theater_end() {
    if (g_th2_reopen || (g_th2_reopen_until && (int)(g_th2_reopen_until - GetTickCount()) > 0)) return;   // (a skip back reopening it)
    __try { h2_local_back(); if (g2_zoomed) { *(float*)(g_h2 + H2T_USER_FOV) = g2_base_fov; g2_zoomed = false; } } __except (EXCEPTION_EXECUTE_HANDLER) {}
    __try {
        if (g_th_cam) {
            **(uint8_t**)(g_h2 + 0x15eb1e8) = 0;
            if (uint8_t* d = *(uint8_t**)(g_h2 + H2T_CAMERA)) d[0] = 0;
            g_th_cam = false;
        }
        if (uint8_t* tg = *(uint8_t**)(g_h2 + H2T_TIME)) *(float*)(tg + 0xC) = 1.0f;
    } __except (EXCEPTION_EXECUTE_HANDLER) {}
    g_th_ff_to = 0xFFFFFFFFu;
    memset(g_th_body, 0, sizeof g_th_body);
    g2_fp_unit = g2_orbit_unit = 0xFFFFFFFFu;
    g2_free_on = g2_lent = false;
    g2_real_local = 0xFFFFFFFFu;
    g2_fpw_player = 0xFFFFFFFFu;
    g_th2_reopen_until = 0;
}

// the Theater's two halo2 hooks (enabled here; h2_watch drops a gone copy's): without them first person is the scripted
// camera's eyes and the free camera goes through walls
static void h2_theater_install(uint8_t* h2) {
    g_h2_frame_ticks_orig = nullptr;
    g_h2_director_orig = nullptr;
    g_h2_ray = nullptr;
    g_h2_flash_orig = nullptr;
    g_h2_local_player_orig = nullptr;
    __try {
        if (!memcmp(h2 + H2T_RAY, H2T_RAY_PROLOGUE, sizeof H2T_RAY_PROLOGUE)) g_h2_ray = (h2_ray_fn)(h2 + H2T_RAY);
        else logf("h2 theater: collision test not the decoded build: cameras pass through walls");
        if (memcmp(h2 + H2T_FRAME_TICKS, H2T_FRAME_TICKS_PROLOGUE, sizeof H2T_FRAME_TICKS_PROLOGUE) ||
            memcmp(h2 + H2T_DIRECTOR_UPDATE, H2T_DIRECTOR_UPDATE_PROLOGUE, sizeof H2T_DIRECTOR_UPDATE_PROLOGUE)) {
            logf("h2 theater: frame ticks / directors not the decoded build: first person without HUD");
            return;
        }
        if (MH_CreateHook(h2 + H2T_FRAME_TICKS, (void*)&h2_frame_ticks_hook, (void**)&g_h2_frame_ticks_orig) != MH_OK ||
            MH_EnableHook(h2 + H2T_FRAME_TICKS) != MH_OK) { g_h2_frame_ticks_orig = nullptr; logf("h2 theater: frame ticks hook failed"); return; }
        if (MH_CreateHook(h2 + H2T_DIRECTOR_UPDATE, (void*)&h2_director_update_hook, (void**)&g_h2_director_orig) != MH_OK ||
            MH_EnableHook(h2 + H2T_DIRECTOR_UPDATE) != MH_OK) { g_h2_director_orig = nullptr; logf("h2 theater: director hook failed"); }
        if (memcmp(h2 + H2T_FLASH, H2T_FLASH_PROLOGUE, sizeof H2T_FLASH_PROLOGUE)) logf("h2 theater: screen flash not the decoded build: the recorder's flashes show in every view");
        else if (MH_CreateHook(h2 + H2T_FLASH, (void*)&h2_flash_hook, (void**)&g_h2_flash_orig) != MH_OK || MH_EnableHook(h2 + H2T_FLASH) != MH_OK) { g_h2_flash_orig = nullptr; logf("h2 theater: screen flash hook failed"); }
        if (memcmp(h2 + H2T_LOCAL_PLAYER, H2T_LOCAL_PLAYER_PROLOGUE, sizeof H2T_LOCAL_PLAYER_PROLOGUE)) logf("h2 theater: local player lookup not the decoded build: a bot's eyes without its gun");
        else if (MH_CreateHook(h2 + H2T_LOCAL_PLAYER, (void*)&h2_local_player_hook, (void**)&g_h2_local_player_orig) != MH_OK || MH_EnableHook(h2 + H2T_LOCAL_PLAYER) != MH_OK) { g_h2_local_player_orig = nullptr; logf("h2 theater: local player hook failed"); }
    } __except (EXCEPTION_EXECUTE_HANDLER) {}
}

// a skip back, on the game thread (h_update): the film opened again from its start, as Bungie's film_play and
// h2_play_now open one (halo2 replays a film from its first tick; what it has read ahead lives outside the game
// state, so an older game state could not be put back under it), and th2_speed runs it fast to the target
static void h2_theater_tick() {
    if (!g_th2_reopen) {
        __try {                                           // (the reload done: the world back at a low tick)
            if (g_th2_reopen_until && *(uint8_t**)(g_h2 + H2T_WORLD) && th_world_tick() < g_th2_req_tick) g_th2_reopen_until = 0;
        } __except (EXCEPTION_EXECUTE_HANDLER) {}
        return;
    }
    g_th2_reopen = false;
    typedef void(__fastcall* open_fn)(const char*);
    __try {
        h2_local_back();
        *(volatile uint8_t*)(g_h2 + 0x18a4320) = 0;       // (no recording of the film's own game)
        g2_fpw_player = 0xFFFFFFFFu;                   // (no bot's gun lent into a game being remade)
        logf("h2 theater: skip back to %u: the film again from its start", g_th_ff_to);
        ((open_fn)(g_h2 + 0x6f6d80))(g_th2_path);
    } __except (EXCEPTION_EXECUTE_HANDLER) { logf("h2 theater: fault opening the film again"); g_th_ff_to = 0xFFFFFFFFu; g_th2_reopen_until = 0; }
}

// the film's game over tick from its header (+0x1818, u32 tick + 1: written below the first time it is seen; halo2's
// film opener leaves the bytes after its own 0x180C alone, h2_keep_films stamps +0x1810)
static void h2_film_over_read() {
    g_th2_over_tick = 0;
    FILE* f = nullptr;
    if (!g_th2_path[0] || fopen_s(&f, g_th2_path, "rb") || !f) return;
    uint32_t v = 0;
    if (!fseek(f, 0x1818, SEEK_SET) && fread(&v, 4, 1, f) == 1 && v) g_th2_over_tick = v - 1;
    fclose(f);
    if (g_th2_over_tick) logf("h2 theater: the film's game over at tick %u (its header)", g_th2_over_tick);
}

// h2_watch: halo2 stopped the film's game (its board is up): the tick kept in the film, and the Theater goes back to
// just before it and holds there (once; next time th2_length stops short of it)
static void h2_film_over() {
    if (g_th2_reopen || g_th2_reopen_until || g_th_ff_to != 0xFFFFFFFFu) return;   // (a skip under way: not the end)
    uint32_t t = 0;
    __try { t = th_world_tick(); } __except (EXCEPTION_EXECUTE_HANDLER) { return; }
    logf("h2 theater: the film's game over at tick %u: holding just before it", t);
    if (!t || (g_th2_over_tick && g_th2_over_tick <= t)) return;
    g_th2_over_tick = t;
    FILE* f = nullptr;
    if (g_th2_path[0] && !fopen_s(&f, g_th2_path, "r+b") && f) {
        uint32_t v = t + 1;
        if (fseek(f, 0x1818, SEEK_SET) || fwrite(&v, 4, 1, f) != 1) logf("h2 theater: could not keep the game over tick in the film");
        fclose(f);
    }
    uint32_t len = th2_length();
    if (len > 1) th2_seek(len - 1);
}
