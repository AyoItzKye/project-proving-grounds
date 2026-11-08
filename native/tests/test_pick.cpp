// native/shared.h helpers: hb_pick_loose, which loose weapon a bot's Use takes, and hb_spawn_take, when a bot's new unit
// moves to its Invasion spawn. Built and run by tools/test_native_pick.py.
#include <stdio.h>
#include "../shared.h"

static int fails = 0;
static void want(const char* what, int got, int expect) {
    if (got != expect) { printf("FAIL %s: picked %d, want %d\n", what, got, expect); fails++; }
}

int main() {
    const float feet[3] = {0.0f, 0.0f, 0.0f};
    // 1. Spire, live: the core 0.85 u ahead on its stand (view on it), a gun on the floor 0.5 u to the side
    const float spire[2][3] = {{0.3f, 0.4f, 0.0f}, {0.85f, 0.0f, 0.4f}};
    float yaw = atan2f(0.0f, 0.85f), pitch = atan2f(0.4f - 0.62f, 0.85f);
    want("the core in view, a gun nearer", hb_pick_loose(spire, 2, feet, yaw, pitch), 1);
    // 2. ... and 0.62 u off it (this morning's 45 s with Use doing nothing)
    const float close[1][3] = {{0.62f, 0.0f, 0.4f}};
    want("the core 0.62 u off in view", hb_pick_loose(close, 1, feet, atan2f(0.0f, 0.62f), atan2f(0.4f - 0.62f, 0.62f)), 0);
    // 3. walking over a gun, looking ahead: the nearest within 0.6 u, as before
    const float floor_gun[1][3] = {{-0.3f, 0.2f, 0.0f}};
    want("a gun underfoot, view ahead", hb_pick_loose(floor_gun, 1, feet, 0.0f, 0.0f), 0);
    // 4. a gun 0.8 u off behind: out of both rules
    const float behind[1][3] = {{-0.8f, 0.0f, 0.0f}};
    want("a gun 0.8 u behind", hb_pick_loose(behind, 1, feet, 0.0f, 0.0f), -1);
    // 5. anything past 1 u across or 1 u up: never
    const float far_gun[2][3] = {{1.2f, 0.0f, 0.6f}, {0.5f, 0.0f, 1.2f}};
    want("past reach", hb_pick_loose(far_gun, 2, feet, 0.0f, 0.0f), -1);
    // hb_spawn_take (Reach Invasion spawns, reach.cpp hr_spawn_moves): a bot's new unit moves once, to a target sent
    // while it was dead
    const uint32_t NONE = 0xFFFFFFFFu;
    uint32_t last = 0x1000A, done = 3;
    want("alive, a target sent: dropped", hb_spawn_take(0x1000A, &last, 4, &done), 0);
    want("... and not taken at the next spawn", hb_spawn_take(NONE, &last, 4, &done) + hb_spawn_take(0x2000B, &last, 4, &done), 0);
    want("dead, a target sent: it waits", hb_spawn_take(NONE, &last, 5, &done), 0);
    want("dead, sent again: still waits", hb_spawn_take(NONE, &last, 6, &done), 0);
    want("the new unit: moved", hb_spawn_take(0x3000C, &last, 6, &done), 1);
    want("the same unit next tick: not again", hb_spawn_take(0x3000C, &last, 6, &done), 0);
    want("a late target while it lives: dropped", hb_spawn_take(0x3000C, &last, 7, &done) + hb_spawn_take(NONE, &last, 7, &done)
         + hb_spawn_take(0x4000D, &last, 7, &done), 0);
    want("a respawn with no target: not moved", hb_spawn_take(NONE, &last, 7, &done) + hb_spawn_take(0x5000E, &last, 7, &done), 0);
    // hb_use_picks_up: a Use asking for a seat never picks up a gun lying there (match 221404: the bot's rifle swapped out)
    want("Use, no seat: picks up", hb_use_picks_up(HB_BTN_ACTION), 1);
    want("Use asking for the gunner seat: no pickup", hb_use_picks_up(HB_BTN_ACTION | (2u << HB_SEAT_SHIFT)), 0);
    want("Use asking for the driver seat: no pickup", hb_use_picks_up(HB_BTN_ACTION | (1u << HB_SEAT_SHIFT)), 0);
    want("no Use: no pickup", hb_use_picks_up(0), 0);
    want("the seat asked for", hb_seat(HB_BTN_ACTION | (3u << HB_SEAT_SHIFT)), 2);
    // hb_loose_parent_ok: a vehicle's own weapon or one in hands is no loose gun (187 s: rifles dropped at exits)
    want("lying free: takeable", hb_loose_parent_ok(-1), 1);
    want("on a vehicle (a horn, a Revenant's gun): not", hb_loose_parent_ok(1), 0);
    want("in someone's hands: not", hb_loose_parent_ok(0), 0);
    want("on a stand or a marker (a flag, the ball): takeable", hb_loose_parent_ok(10) + hb_loose_parent_ok(6), 2);
    // hb_chat_feed: the chat commands, the burst typed before Enter; nothing else leaves it
    auto line = [](const char* typed, uint32_t gap_after_first = 50) {
        hb_chat_line s{};
        uint32_t t = 1000;
        int got = 0;
        for (const char* p = typed; *p; p++) {
            got = hb_chat_feed(&s, (uint8_t)*p == '\n' ? '\r' : (uint8_t)*p, t);
            t += p == typed ? gap_after_first : 50;
        }
        return got;
    };
    want("follow me", line("follow me\n"), HB_SAY_FOLLOW);
    want("Follow Me, spaces and capitals", line("  Follow   Me \n"), HB_SAY_FOLLOW);
    want("roam", line("roam\n"), HB_SAY_ROAM);
    want("the chat key's letter before it", line("troam\n") + line("y follow me\n"), HB_SAY_ROAM + HB_SAY_FOLLOW);
    want("walking keys long before it: a new line", line("wfollow me\n", 3000), HB_SAY_FOLLOW);
    want("other words: nothing", line("gg roam around\n") + line("follow\n") + line("dont follow me ok\n"), 0);
    want("a typo taken back", line("roan\bm\n") - HB_SAY_ROAM + line("rom\n"), 0);
    want("Esc throws it away", line("roam\x1b\n"), 0);
    if (!fails) printf("pick OK, spawn take OK, use OK\n");
    return fails ? 1 : 0;
}
