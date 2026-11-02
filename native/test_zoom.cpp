// test_zoom.cpp: offline check of how a bot's wanted scope level reaches CE, Halo 2 and Halo 3 (shared.h
// hb_zoom_index / hb_set_zoom; the brain sends Action.zoom in buttons bits 12-13, tools/live_bots.py
// buttons()). In all three the action's zoom field is an absolute level, -1 none, 0 first, 1 second: CE's
// unit control writes its +8 into the unit's +0x301 every tick (ghidra/ce_uc.c line 65); Halo 2's network
// decoder reads "zoom-level" - 1 into +0x2A (ghidra/h2_actdec.c line 47); Halo 3's input copies +0x4A into
// the unit control, which writes it to the unit's +0x299 (ghidra/h3_input.c line 28).
// usage: build_preview.bat, then bin\test_zoom.exe -> "zoom OK"
#include <stdio.h>
#include <string.h>
#include "shared.h"

static int fails = 0;
#define CHECK(c, ...) do { if (!(c)) { printf("FAIL: " __VA_ARGS__); printf("\n"); fails++; } } while (0)

static bool untouched(const uint8_t* a, size_t n, size_t off, size_t len) {
    for (size_t k = 0; k < n; k++)
        if ((k < off || k >= off + len) && a[k] != 0xAB) return false;
    return true;
}

int main() {
    // the level the brain wants -> the field's value; fire and a weapon switch in the same word do not leak in
    const int16_t want[4] = {-1, 0, 1, 1};          // 3 is never sent: the second level at most
    for (uint32_t z = 0; z < 4; z++) {
        uint32_t b = (z << HB_ZOOM_SHIFT) | HB_BTN_FIRE | (2u << HB_WEAPON_SHIFT) | HB_BTN_SPRINT;
        CHECK(hb_zoom_index(b) == want[z], "level %u -> %d (want %d)", z, hb_zoom_index(b), want[z]);
    }
    // each game's field, nothing else in its action touched
    struct { uint32_t game; size_t off, size; } games[] = {{1, 0x1C, 0x30}, {2, 0x2A, 0x60}, {3, 0x4A, 0x88}};
    for (auto& g : games) {
        uint8_t act[0x100];
        memset(act, 0xAB, sizeof act);
        CHECK(hb_set_zoom(g.game, act, g.size, 2u << HB_ZOOM_SHIFT), "game %u: zoom not written", g.game);
        CHECK(*(int16_t*)(act + g.off) == 1, "game %u: +0x%zX = %d (want 1)", g.game, g.off, *(int16_t*)(act + g.off));
        CHECK(untouched(act, sizeof act, g.off, 2), "game %u: bytes outside +0x%zX changed", g.game, g.off);
        hb_set_zoom(g.game, act, g.size, 0);
        CHECK(*(int16_t*)(act + g.off) == -1, "game %u: no zoom wanted left %d (want -1)", g.game, *(int16_t*)(act + g.off));
    }
    // games whose zoom field is not decoded yet (Reach, ODST, H2A, Halo 4) are left as they are
    for (uint32_t game = 4; game <= 7; game++) {
        uint8_t act[0x240];
        memset(act, 0xAB, sizeof act);
        CHECK(!hb_set_zoom(game, act, sizeof act, 1u << HB_ZOOM_SHIFT) && untouched(act, sizeof act, 0, 0),
              "game %u: written although its field is not decoded", game);
    }
    // never past the end of a short buffer (Halo 2's field needs 0x2C bytes)
    uint8_t small[0x2B];
    memset(small, 0xAB, sizeof small);
    CHECK(!hb_set_zoom(2, small, sizeof small, 1u << HB_ZOOM_SHIFT) && untouched(small, sizeof small, 0, 0),
          "a 0x2B-byte Halo 2 action was written");
    if (fails) return 1;
    printf("zoom OK\n");
    return 0;
}
