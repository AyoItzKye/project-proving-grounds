// native/ui_layout.h at every window size: botcore's BOTS tile and "Report bot bug" button land where MCC's own menu
// items are, stay on screen, keep their anchors and never cover MCC's items. Built and run by tools/test_native_ui_layout.py
// (also with /DUI_OLD: the layout before Nov 5, which must FAIL: it was laid out for 3440x1440 only).
#include <math.h>
#include <stdio.h>
#include "../ui_layout.h"

#ifdef UI_OLD   // the old overlay.cpp tile_rect and bots_panel.cpp button, kept to prove the test catches them
static ui_rect tile(float W, float H) {
    float w16 = H * 16.0f / 9.0f, x0 = (W - w16) * 0.5f;
    if (w16 > W) { w16 = W; x0 = 0; }
    return { x0 + w16 * 0.637f, H * 0.1463f, x0 + w16 * 0.759f, H * 0.2925f };
}
static ui_rect button(float W, float H) { float s = H / 1080; return { W - 380 * s, H * 0.80f, W - 60 * s, H * 0.80f + 56 * s }; }
#else
static ui_rect tile(float W, float H) { return bots_tile_rect(W, H); }
static ui_rect button(float W, float H) { return bug_button_rect(W, H); }
#endif

static int fails = 0;
static void check(bool ok, const char* what, float W, float H) {
    if (!ok) { printf("FAIL %gx%g: %s\n", W, H, what); fails++; }
}
static bool near(float a, float b, float tol) { return fabsf(a - b) <= tol; }

int main() {
    // MCC's own items as seen on screen (logs/tmp/ui_res screenshots, Nov 5): START tile and the Back button
    struct seen { float W, H, sx0, sy0, sx1, bx0, by0, bx1, by1; } SEEN[] = {
        {1920, 1080, 976, 158, 1211, 108, 984, 193, 1022},   // 16:9 (monitor 2, borderless / windowed / exclusive)
        {1440, 900, 732, 164, 908, 90, 820, 159, 851},       // 16:10 windowed
        {1920, 540, 968, 79, 1085, 534, 492, 578, 512},      // 32:9 windowed (Back row measured on the lobby)
        {3440, 1440, 1741, 211, 2055, 584, 1312, 694, 1366}, // 21:9 the owner's
    };
    for (const seen& m : SEEN) {
        ui_rect st = mcc_lobby_start(m.W, m.H), bk = mcc_footer_back(m.W, m.H);
        check(near(st.x0, m.sx0, 3) && near(st.y0, m.sy0, 3) && near(st.x1, m.sx1, 3), "model START != screenshot", m.W, m.H);
        check(near(bk.x0, m.bx0, 3) && near(bk.y0, m.by0, 3) && near(bk.x1, m.bx1, 3), "model Back != screenshot", m.W, m.H);
        ui_rect t = tile(m.W, m.H);   // the BOTS tile: START's line and height, right next to it
        check(near(t.y0, m.sy0, 3) && near(t.y1 - t.y0, st.y1 - st.y0, 3), "BOTS tile off START's row", m.W, m.H);
        check(t.x0 >= m.sx1 && t.x0 - m.sx1 <= 10 * m.H / 1080 + 3, "BOTS tile not next to START", m.W, m.H);
        ui_rect b = button(m.W, m.H);  // the bug button: in the footer row, on Back's line
        check((near(b.y0, m.by0, 4) || near(b.y1 - b.y0, 28, 0.5f)) && near(b.y1, m.by1 + 1, 4), "bug button off MCC's footer row", m.W, m.H);   // (or grown to 28 px)
    }
    // the render matrix: every size a player can pick, windowed or full screen
    const float SIZES[][2] = {
        {1280, 720}, {1366, 768}, {1600, 900}, {1920, 1080}, {2560, 1440}, {3840, 2160},   // 16:9
        {1280, 800}, {1440, 900}, {1680, 1050}, {1920, 1200}, {2560, 1600},              // 16:10
        {1024, 768}, {1280, 1024},                                                       // 4:3, 5:4
        {2560, 1080}, {3440, 1440}, {3840, 1600}, {5120, 2160},                          // 21:9
        {3840, 1080}, {5120, 1440}, {1920, 540},                                         // 32:9
        {1904, 1041}, {1264, 681},                                                       // windowed, client area
    };
    for (const auto& z : SIZES) {
        float W = z[0], H = z[1];
        ui_rect t = tile(W, H), b = button(W, H), st = mcc_lobby_start(W, H), op = mcc_lobby_options(W, H);
        ui_rect row = mcc_lobby_tiles(W, H), pause = mcc_pause_tiles(W, H), back = mcc_footer_back(W, H);
        ui_page c = mcc_content(W, H), f = mcc_frame(W, H);
        check(ui_inside(t, W, H), "BOTS tile off screen", W, H);
        check(ui_inside(b, W, H), "bug button off screen", W, H);
        check(!ui_overlap(t, row) && !ui_overlap(t, st) && !ui_overlap(t, op), "BOTS tile covers MCC's tiles", W, H);
        check(!ui_overlap(b, pause) && !ui_overlap(b, back), "bug button covers MCC's pause items", W, H);
        check(near(t.y0, st.y0, 0.5f) && near(t.y1, st.y1, 0.5f) && near(t.x0 - st.x1, 5 * c.s, 0.5f), "tile anchor", W, H);
        check(near(t.x1 - t.x0, st.x1 - st.x0, 0.5f), "tile not START's size", W, H);
        check(near(b.x1, f.x0 + f.w - 109 * f.s, 0.5f) && near(b.y1, back.y1, 0.5f), "button anchor", W, H);
        check(b.y1 - b.y0 >= 28 && t.y1 - t.y0 >= 28 && b.x1 - b.x0 >= 28, "hit size under 28 px", W, H);
        check(b.x0 >= f.x0 && b.x1 <= f.x0 + f.w, "bug button outside MCC's frame", W, H);
        // our windows scale with MCC's content: the panel (1400x860 units) and the report (680 wide) fit
        check(1400 * c.s <= W && 860 * c.s <= H && 680 * c.s <= W, "panel / report wider than the window", W, H);
        // the lobby probe reads inside the window
        check(mcc_probe_x(W, H, 0) >= 6 && mcc_probe_x(W, H, 1) + 6 <= W && mcc_probe_rows(W, H).y1 <= H, "probe", W, H);
    }
    if (fails) { printf("%d failures\n", fails); return 1; }
    printf("ui layout OK\n");
    return 0;
}
