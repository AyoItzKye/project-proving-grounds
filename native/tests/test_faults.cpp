// botcore's Halo 4 / H2A hook (native/h4f.cpp) on fake game memory in this process: its guards' failure paths, and its
// vehicle exit call.
// 1. a fault inside a bot's boarding is caught at its call and logged with the bot ("boarding faulted (bot 1)")
// 2. a fault inside a command (adding a bot) gives cmd_fault 1, result -1, and the command still completes
// 3. a fault anywhere else in the players-update hook gives cmd_fault 2 and the hook returns
// 6. Halo 4: a bot in a seat holding Use (no seat asked for) is got out by the game's unit_exit_vehicle (a stand-in at its
//    address, with its checked bytes): its unit, type 0, once in 15 ticks; never on foot, asking for a seat or not
//    holding Use
// 4. H2A's first tick of a match with no bot coming: held, then goes on after 4 s, and says so
// 5. H2A's first tick after a stall later in a match (its clock past 1 s): never held; and H2A's exit as in 6
// 7. a build whose exit code is not the decoded one: no call, and says so
// 8. Halo 4's boarding pick passes over a vehicle on its roof for the standing one farther off
// 9. Halo 3 (native/h3.cpp h3_board): Use with a seat asked for, on foot, fills the seat interaction (type 4, the seat, the
//    nearest standing vehicle; with the gun asked for, the gun riding on it); nothing without a seat or when seated
// 10. Halo 3 (h3_pickup_target): a flag on its stand on an Elephant is a pickup target, placed along the Elephant's axes
// Prints "faults OK" (exit 0) or the failures (exit 1). Built and run by tools/test_native_faults.py.
#include "../h4f.cpp"
#define tls_index_of h3_tls_index_of                   // (each file has its own; one program here)
#include "../h3.cpp"
#undef tls_index_of
#include <stdarg.h>

hb_shared* g_shm;
uint32_t g_prejoin = 1;
static char g_log[8192];
void logf(const char* fmt, ...) {
    size_t n = strlen(g_log);
    va_list a;
    va_start(a, fmt);
    vsnprintf(g_log + n, sizeof g_log - n - 2, fmt, a);
    va_end(a);
    strcat_s(g_log, sizeof g_log, "\n");
}
void report_note_bot(int, const wchar_t*, const wchar_t*, int, const wchar_t*, const uint16_t*) {}
void bot_service_tag(const wchar_t*, wchar_t tag[4]) { tag[0] = 0; }
extern "C" MH_STATUS WINAPI MH_CreateHook(LPVOID, LPVOID, LPVOID*) { return MH_OK; }
extern "C" MH_STATUS WINAPI MH_EnableHook(LPVOID) { return MH_OK; }
extern "C" MH_STATUS WINAPI MH_RemoveHook(LPVOID) { return MH_OK; }
extern "C" unsigned long _tls_index;                  // this program's own slot in the thread's TLS table (the CRT's)

// the game's thread block (players +0x8, objects +0x18, configurations +0x90), reached the way f_tls reads it: TEB +0x58,
// the slot after this program's own
static uint8_t game_tls[0x100], players_hdr[0x60], objects_hdr[0x60], players[4][0x1000], ents[8][0x18], unit[0x1000];
static uint8_t actions[0x10 + 4 * F_ACTION];
static void* tls_table[8];
static hb_shared shm;

static void put_ptr(uint8_t* at, const void* p) { memcpy(at, &p, sizeof p); }

// a stand-in for the game's unit_exit_vehicle at its address: the checked thunk before it and head, then it notes its
// unit (+48), type (+52) and calls (+56) and returns
static uint8_t* put_exit(uint8_t* mod, uintptr_t at) {
    static const uint8_t body[] = {
        0x48, 0x89, 0x5C, 0x24, 0x08, 0x55, 0x48, 0x8B, 0xEC, 0x48, 0x83, 0xEC, 0x70,   // the checked head
        0x89, 0x0D, 0x1D, 0x00, 0x00, 0x00,                                           // mov [rip+0x1D], ecx
        0x66, 0x89, 0x15, 0x1A, 0x00, 0x00, 0x00,                                     // mov [rip+0x1A], dx
        0xFF, 0x05, 0x18, 0x00, 0x00, 0x00,                                           // inc dword [rip+0x18]
        0x48, 0x83, 0xC4, 0x70, 0x5D, 0x48, 0x8B, 0x5C, 0x24, 0x08, 0xC3 };           // add rsp; pop rbp; mov rbx; ret
    uint8_t* f = mod + at;
    memcpy(f - sizeof F_EXIT_THUNK, F_EXIT_THUNK, sizeof F_EXIT_THUNK);
    memcpy(f, body, sizeof body);
    FlushInstructionCache(GetCurrentProcess(), f, sizeof body);
    return f;
}
static uint32_t exit_calls(uint8_t* f) { return *(uint32_t*)(f + 56); }

int main() {
    int fails = 0;
    void** real = (void**)__readgsqword(0x58);
    if (!real || _tls_index + 1 >= 8) { printf("FAIL: no TLS table to stand in for (slot %lu)\n", _tls_index); return 1; }
    for (unsigned long i = 0; i <= _tls_index; i++) tls_table[i] = real[i];
    tls_table[_tls_index + 1] = game_tls;
    __writegsqword(0x58, (DWORD64)tls_table);
    uint8_t* tls = game_tls;
    g_shm = &shm;
    for (int i = 0; i < HB_MAX_PLAYERS; i++) shm.bot_player_index[i] = -1;
    // players (the player 0, bot 1, free 2-3); objects (the bot's unit at 2; at 3 a vehicle whose object cannot be
    // read)
    put_ptr(tls + 0x8, players_hdr);
    *(int32_t*)(players_hdr + 0x20) = 0x1000;
    *(int32_t*)(players_hdr + 0x2C) = 4;
    put_ptr(players_hdr + 0x50, players);
    *(uint16_t*)players[0] = 1;
    *(uint16_t*)players[1] = 1;
    *(uint32_t*)(players[1] + 0x2C) = (0x1234u << 16) | 2;
    put_ptr(tls + 0x18, objects_hdr);
    *(int32_t*)(objects_hdr + 0x2C) = 8;
    put_ptr(objects_hdr + 0x50, ents);
    *(uint16_t*)ents[2] = 0x1234;
    put_ptr(ents[2] + 0x10, unit);
    *(uint32_t*)(unit + 0x24) = 0xFFFFFFFFu;           // on foot
    *(int32_t*)(unit + 0x534) = -1;                    // no sprint slot
    *(uint32_t*)(unit + 0xD40) = 0xFFFFFFFFu;
    *(uint16_t*)ents[3] = 0x5678;
    ents[3][4] = 1;
    put_ptr(ents[3] + 0x10, (void*)0x10);
    // Halo 4's module: only the boarding code's checked prologues
    h4f_game G = g_h4;
    G.mod = (uint8_t*)VirtualAlloc(nullptr, 0x700000, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    uint8_t* exit_h4 = put_exit(G.mod, F_EXIT_H4);
    uint8_t* exit_h2a = put_exit(G.mod, F_EXIT_H2A);
    G.tls_index = _tls_index + 1;
    memcpy(G.mod + F_BOARD_H4.seats, F_SEATS_HEAD, sizeof F_SEATS_HEAD);
    memcpy(G.mod + F_BOARD_H4.can, F_CAN_HEAD, sizeof F_CAN_HEAD);
    memcpy(G.mod + F_BOARD_H4.occupant, F_OCC_HEAD, sizeof F_OCC_HEAD);
    memcpy(G.mod + F_BOARD_H4.occupant + 7, F_OCC_TAIL, sizeof F_OCC_TAIL);

    // 1. bot 1 holds Use with the driver's seat asked: its boarding reads the vehicle and faults
    shm.bot_player_index[0] = 1;
    shm.actions[0].seq = 1;
    shm.actions[0].buttons = HB_BTN_ACTION | (1u << HB_SEAT_SHIFT);
    f_update(G, actions);
    if (!strstr(g_log, "h4 boarding faulted (bot 1)")) { printf("FAIL 1: no boarding fault logged:\n%s", g_log); fails++; }
    if (shm.cmd_fault) { printf("FAIL 1: the boarding fault reached the hook (cmd_fault %u)\n", shm.cmd_fault); fails++; }

    // 2. adding a bot with the configurations block unreadable
    put_ptr(tls + 0x90, (void*)0x10);
    shm.cmd = HB_CMD_ADD_BOT;
    shm.cmd_arg = 1u << G.cmd_bit;
    shm.cmd_seq = shm.cmd_done_seq + 1;
    f_command(G, tls);
    if (shm.cmd_fault != 1 || shm.cmd_result != -1 || shm.cmd_done_seq != shm.cmd_seq) {
        printf("FAIL 2: command fault %u result %lld done %u of %u (want 1, -1, done)\n", shm.cmd_fault,
               (long long)shm.cmd_result, shm.cmd_done_seq, shm.cmd_seq);
        fails++;
    }

    // 3. the players block unreadable: the hook's own guard
    shm.cmd_fault = 0;
    put_ptr(players_hdr + 0x50, (void*)0x10);
    f_update(G, actions);
    if (shm.cmd_fault != 2) { printf("FAIL 3: cmd_fault %u after a fault in the hook (want 2)\n", shm.cmd_fault); fails++; }
    put_ptr(players_hdr + 0x50, players);

    // 6. Halo 4: bot 1 in a Warthog's seat 0 holding Use, no seat asked for: out by the game's own call
    const uint32_t uh = (0x1234u << 16) | 2, veh = (0x5678u << 16) | 3;
    *(uint32_t*)(unit + 0x24) = veh;
    *(int16_t*)(unit + 0x2C) = 0;
    shm.actions[0].buttons = HB_BTN_ACTION;
    g_log[0] = 0;
    f_update(G, actions);
    if (exit_calls(exit_h4) != 1 || *(uint32_t*)(exit_h4 + 48) != uh || *(int16_t*)(exit_h4 + 52) != 0 ||
        !strstr(g_log, "h4 vehicle exit found") || !strstr(g_log, "h4 bot 1 gets out of 56780003 seat 0")) {
        printf("FAIL 6: exit calls %u, unit %08x type %d (want 1, %08x, 0); logged:\n%s", exit_calls(exit_h4),
               *(uint32_t*)(exit_h4 + 48), *(int16_t*)(exit_h4 + 52), uh, g_log);
        fails++;
    }
    f_update(G, actions);                             // the next tick: still within its 15
    uint32_t held_calls = exit_calls(exit_h4);
    shm.game_tick += 15;
    f_update(G, actions);
    uint32_t again = exit_calls(exit_h4);
    uint32_t no_exit[3];
    shm.game_tick += 15;
    *(uint32_t*)(unit + 0x24) = 0xFFFFFFFFu;          // on foot
    f_update(G, actions);
    no_exit[0] = exit_calls(exit_h4);
    *(uint32_t*)(unit + 0x24) = veh;
    shm.actions[0].buttons = HB_BTN_ACTION | (1u << HB_SEAT_SHIFT);   // asking for a seat (boarding)
    f_update(G, actions);
    no_exit[1] = exit_calls(exit_h4);
    shm.actions[0].buttons = 0;                       // not holding Use
    f_update(G, actions);
    no_exit[2] = exit_calls(exit_h4);
    if (held_calls != 1 || again != 2 || no_exit[0] != 2 || no_exit[1] != 2 || no_exit[2] != 2) {
        printf("FAIL 6: calls %u next tick (want 1), %u 15 ticks on (want 2), %u / %u / %u on foot / asking for a "
               "seat / no Use (want 2)\n", held_calls, again, no_exit[0], no_exit[1], no_exit[2]);
        fails++;
    }
    shm.bot_player_index[0] = -1;

    // 4. H2A, a match's first tick (its clock at 0, no bot in it): held for the brain's commands; none comes
    h4f_game H = g_h2a;
    H.tls_index = G.tls_index;
    H.mod = G.mod;
    shm.bot_player_index[0] = -1;
    memset(players[1] + 0xE0, 0, 8);                  // (no bot's id on player 1 now)
    shm.bots_enabled = 1;
    *(int32_t*)(players[0] + 0xA94) = 0;
    g_log[0] = 0;
    DWORD t0 = GetTickCount();
    f_update(H, actions);
    DWORD held = GetTickCount() - t0;
    if (held < 3900 || held > 5000 || !strstr(g_log, "holding for the bots") || !strstr(g_log, "(0 commands)")) {
        printf("FAIL 4: the first tick took %lu ms (want about 4000) and logged:\n%s", held, g_log);
        fails++;
    }

    // 5. a 3 s stall later in the match (its clock at 10 s): the next tick looks like a first one, but is not held; and
    // bot 1, still in its seat, holds Use: out by H2A's own call
    Sleep(3100);
    *(int32_t*)(players[0] + 0xA94) = 600;
    shm.bot_player_index[0] = 1;
    shm.actions[0].buttons = HB_BTN_ACTION;
    shm.game_tick += 30;
    g_log[0] = 0;
    t0 = GetTickCount();
    f_update(H, actions);
    DWORD stall = GetTickCount() - t0;
    if (stall > 500 || !strstr(g_log, "match clock 600, not held")) {
        printf("FAIL 5: the tick after a stall took %lu ms and logged:\n%s", stall, g_log);
        fails++;
    }
    if (exit_calls(exit_h2a) != 1 || *(uint32_t*)(exit_h2a + 48) != uh || exit_calls(exit_h4) != 2 ||
        !strstr(g_log, "h2a bot 1 gets out of 56780003 seat 0")) {
        printf("FAIL 5: H2A exit calls %u (want 1, Halo 4's still 2: %u), unit %08x; logged:\n%s", exit_calls(exit_h2a),
               exit_calls(exit_h4), *(uint32_t*)(exit_h2a + 48), g_log);
        fails++;
    }

    // 7. another build (its exit code not the decoded bytes): no call, and says so
    h4f_game X = g_h2a;
    X.id = 5;                                         // (its own checked-once slot)
    X.tls_index = G.tls_index;
    X.mod = (uint8_t*)VirtualAlloc(nullptr, 0x700000, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    shm.game_tick += 30;
    g_log[0] = 0;
    f_update(X, actions);
    if (exit_calls(exit_h2a) != 1 || exit_calls(exit_h4) != 2 || !strstr(g_log, "vehicle exit not the decoded build") ||
        strstr(g_log, "exit faulted")) {                    // (a call into the other build's bytes faults in its guard)
        printf("FAIL 7: exit calls %u / %u on another build (want 1 / 2); logged:\n%s", exit_calls(exit_h2a),
               exit_calls(exit_h4), g_log);
        fails++;
    }
    // 8. Halo 4's boarding pick: a vehicle on its roof 1 u off is passed over for the standing one 2.5 u off
    // (objects 0x200: a live one reaches past its damage flags at +0x16C; 0x100 read the next fixture there)
    static uint8_t standing[0x200], on_roof[0x200];
    *(uint32_t*)(standing + 0x24) = *(uint32_t*)(on_roof + 0x24) = 0xFFFFFFFFu;   // top level
    ((float*)(standing + 0x40))[0] = 2.5f;
    ((float*)(on_roof + 0x40))[0] = 1.0f;
    ((float*)(standing + 0x7C))[2] = 1.0f;            // up z
    ((float*)(on_roof + 0x7C))[2] = -1.0f;
    *(uint16_t*)ents[3] = 0;                          // (case 1's unreadable vehicle out of the way)
    *(uint16_t*)ents[4] = 0x0A0A;
    ents[4][4] = 1;
    put_ptr(ents[4] + 0x10, standing);
    *(uint16_t*)ents[5] = 0x0B0B;
    ents[5][4] = 1;
    put_ptr(ents[5] + 0x10, on_roof);
    memset(unit + 0x40, 0, 12);                       // the bot at the origin
    uint32_t pick = f_near_vehicle(G, tls, unit);
    if (pick != ((0x0A0Au << 16) | 4)) { printf("FAIL 8: Halo 4 picked %08x (want the standing one, 0a0a0004)\n", pick); fails++; }
    // ... and a destroyed one (damage flags +0x16C bit 2, s156) standing 1 u off is passed over too
    ((float*)(on_roof + 0x7C))[2] = 1.0f;
    on_roof[0x16C] = 4;
    pick = f_near_vehicle(G, tls, unit);
    if (pick != ((0x0A0Au << 16) | 4)) { printf("FAIL 8: Halo 4 picked %08x by a wreck (want 0a0a0004)\n", pick); fails++; }
    // ... a giant (type 13, Halo 4's Mantis) is boarded in Halo 4; H2A's type 13 is not
    ents[4][4] = 13;
    pick = f_near_vehicle(G, tls, unit);
    if (pick != ((0x0A0Au << 16) | 4)) { printf("FAIL 8: Halo 4 passed over a giant (picked %08x)\n", pick); fails++; }
    {
        h4f_game A = g_h2a;
        pick = f_near_vehicle(A, tls, unit);
        if (pick != 0xFFFFFFFFu) { printf("FAIL 8: H2A boarded a type 13 object (%08x)\n", pick); fails++; }
    }
    ents[4][4] = 1;

    // 9. Halo 3 boarding (objects at TLS +0x38: +0x20 count, +0x48 entries of 0x18: +0 salt, +3 type, +0x10 the object;
    // object +0x10 parent, +0x50 position, +0x5C forward, +0x68 up)
    // (objects 0x200: a live one reaches past its damage flags at +0x110; 0x100 read the next fixture's parent there)
    static uint8_t h3_hdr[0x60], h3_ents[6][0x18], h3_unit[0x200], hog[0x200], roof[0x200], gun[0x200], act3[0x100],
        wreck[0x200];
    put_ptr(tls + 0x38, h3_hdr);
    *(int32_t*)(h3_hdr + 0x20) = 6;
    put_ptr(h3_hdr + 0x48, h3_ents);
    auto h3_put = [&](int i, uint16_t salt, uint8_t type, uint8_t* o, uint32_t parent, float x, float y, float z, float upz) {
        *(uint16_t*)h3_ents[i] = salt;
        h3_ents[i][3] = type;
        put_ptr(h3_ents[i] + 0x10, o);
        *(uint32_t*)(o + 0x10) = parent;
        float* f = (float*)(o + 0x50);
        f[0] = x, f[1] = y, f[2] = z;                 // position
        f[3] = 1.0f, f[4] = 0.0f, f[5] = 0.0f;        // forward (+0x5C)
        f[6] = 0.0f, f[7] = 0.0f, f[8] = upz;         // up (+0x68)
    };
    const uint32_t hog_h = (0x0101u << 16) | 1, roof_h = (0x0202u << 16) | 2, gun_h = (0x0303u << 16) | 3;
    h3_put(0, 0x0505, 0, h3_unit, 0xFFFFFFFFu, 0.0f, 0.0f, 0.0f, 1.0f);   // the bot, on foot at the origin
    h3_put(1, 0x0101, 1, hog, 0xFFFFFFFFu, 2.0f, 0.0f, 0.0f, 1.0f);       // a standing Warthog 2 u off
    h3_put(2, 0x0202, 1, roof, 0xFFFFFFFFu, 1.0f, 0.0f, 0.0f, -1.0f);     // one on its roof 1 u off
    h3_put(3, 0x0303, 1, gun, hog_h, -0.5f, 0.0f, 0.5f, 1.0f);            // the standing one's gun (relative)
    h3_put(4, 0x0404, 1, wreck, 0xFFFFFFFFu, 0.5f, 0.0f, 0.0f, 1.0f);     // a destroyed one standing 0.5 u off
    wreck[0x110] = 4;                                                     // (damage flags bit 2, s156: passed over)
    const uint32_t use_seat0 = HB_BTN_ACTION | (1u << HB_SEAT_SHIFT);
    memset(act3, 0, sizeof act3);
    h3_board(tls, act3, h3_unit, use_seat0);
    uint32_t got_driver = *(uint32_t*)(act3 + 0x50);
    int16_t got_type = *(int16_t*)(act3 + 0x4C), got_seat = *(int16_t*)(act3 + 0x4E);
    memset(act3, 0, sizeof act3);
    h3_board(tls, act3, h3_unit, use_seat0 | HB_BTN_TURRET);
    uint32_t got_gun = *(uint32_t*)(act3 + 0x50);
    memset(act3, 0, sizeof act3);
    h3_board(tls, act3, h3_unit, HB_BTN_ACTION);                          // Use, no seat asked
    int16_t no_seat = *(int16_t*)(act3 + 0x4C);
    *(uint32_t*)(h3_unit + 0x10) = hog_h;                                 // already riding
    h3_board(tls, act3, h3_unit, use_seat0);
    int16_t seated = *(int16_t*)(act3 + 0x4C);
    *(uint32_t*)(h3_unit + 0x10) = 0xFFFFFFFFu;
    if (got_type != 4 || got_seat != 0 || got_driver != hog_h || got_gun != gun_h || no_seat || seated) {
        printf("FAIL 9: Halo 3 boarding type %d seat %d vehicle %08x gun %08x (want 4, 0, %08x, %08x), no seat %d, seated %d "
               "(want 0, 0); the one on its roof is %08x\n", got_type, got_seat, got_driver, got_gun, hog_h, gun_h, no_seat,
               seated, roof_h);
        fails++;
    }

    // 10. Halo 3 flag pickup (h3_pickup_target): the flag on its stand on an Elephant (Sandtrap) is offered where the
    // stand puts it along the Elephant's axes; the bot's own gun never is; a flag on a stand on the ground still is
    static uint8_t p_ents[7][0x18], bot10[0x100], ele[0x100], stand[0x100], flag[0x100], held10[0x100], gstand[0x100],
        gflag[0x100];
    put_ptr(h3_hdr + 0x48, p_ents);
    *(int32_t*)(h3_hdr + 0x20) = 7;
    auto hnd = [](int i) { return ((uint32_t)(0x1000 + i) << 16) | (uint32_t)i; };
    auto p_put = [&](int i, uint8_t type, uint8_t* o, uint32_t parent, float x, float y, float z) {
        *(uint16_t*)p_ents[i] = (uint16_t)(0x1000 + i);
        p_ents[i][3] = type;
        put_ptr(p_ents[i] + 0x10, o);
        *(uint32_t*)(o + 0x10) = parent;
        float* f = (float*)(o + 0x50);
        f[0] = x, f[1] = y, f[2] = z;
        f[3] = 0.0f, f[4] = 1.0f, f[5] = 0.0f;        // facing +y (left is -x)
        f[6] = 0.0f, f[7] = 0.0f, f[8] = 1.0f;
    };
    p_put(0, 0, bot10, 0xFFFFFFFFu, 10.6f, 21.2f, -20.65f);    // the bot, on the Elephant's deck
    p_put(1, 1, ele, 0xFFFFFFFFu, 10.0f, 20.0f, -22.0f);       // the Elephant
    p_put(2, 10, stand, hnd(1), 1.44f, -0.45f, 1.35f);         // its flag stand (relative, as read live on Sandtrap)
    p_put(3, 2, flag, hnd(2), 0.0f, 0.0f, 0.31f);              // the flag on it: at (10.45, 21.44, -20.34)
    p_put(4, 2, held10, hnd(0), 0.0f, 0.0f, 0.0f);             // the bot's own gun
    p_put(5, 10, gstand, 0xFFFFFFFFu, 40.0f, 0.0f, 0.0f);      // a flag stand on the ground
    p_put(6, 2, gflag, hnd(5), 0.0f, 0.0f, 0.31f);
    float* bp = (float*)(bot10 + 0x50);
    uint32_t on_ele = h3_pickup_target(tls, bot10);
    bp[0] = 12.5f, bp[1] = 21.44f;                             // 2 u off the Elephant's flag: out of reach
    uint32_t too_far = h3_pickup_target(tls, bot10);
    bp[0] = 40.2f, bp[1] = 0.1f, bp[2] = 0.0f;
    uint32_t on_ground = h3_pickup_target(tls, bot10);
    bp[0] = 10.6f, bp[1] = 21.2f, bp[2] = -20.65f;
    *(uint32_t*)(stand + 0x10) = hnd(1) ^ 0x00010000u;         // the stand's vehicle handle gone stale (another salt)
    uint32_t stale = h3_pickup_target(tls, bot10);
    *(uint32_t*)(stand + 0x10) = hnd(1);
    if (on_ele != hnd(3) || too_far != 0xFFFFFFFFu || on_ground != hnd(6) || stale != 0xFFFFFFFFu) {
        printf("FAIL 10: Halo 3 pickup on the Elephant %08x (want %08x), 2 u off %08x (want none), on the ground %08x "
               "(want %08x), stale vehicle %08x (want none)\n", on_ele, hnd(3), too_far, on_ground, hnd(6), stale);
        fails++;
    }

    __writegsqword(0x58, (DWORD64)real);
    if (fails) return 1;
    printf("faults OK (boarding fault logged, command fault 1 / -1, hook fault 2, first tick held %lu ms, after a stall %lu ms);"
           " exits OK (Halo 4 2, H2A 1, none on foot / boarding / no Use / another build); a vehicle on its roof passed"
           " over; Halo 3 boarding OK (seat interaction, gun, none without a seat or seated); Halo 3 flag on an Elephant"
           " offered\n", held, stall);
    return 0;
}
