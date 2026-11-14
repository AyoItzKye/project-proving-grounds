// theater.cpp: Halo 3's Theater over a film of Halo: CE or Halo 2 (docs/THEATER_RE.md "Controls").
//
// Halo 3 draws its Theater itself (halo3.dll; MCC only maps the keys). halo1 and halo2 have none, so botcore's overlay
// does: the camera (any player's eyes, an orbit behind them, a free camera), playback (pause, fast forward while E is
// held, skip back / ahead), the timeline, the controls panel and the followed player's name box. Keys are MCC's own
// Theater defaults: X panel, Z interface, C first / third person, Space the view (first, third, free), Enter pause / play, E fast
// forward, Left / Right skip (with the panel up: its buttons), left mouse its button, Up / Down (or the wheel) the
// player, W A S D move, R / F up / down, Left Shift faster, Left Alt pan, right mouse zoom. While a film plays the
// game gets none of the viewer's input (Esc and Tab still do: MCC's menu, the scores): before, the viewer's mouse turned
// the recorder's view as if in a game (Nov 13).
#include <windows.h>
#include <xinput.h>
#include <math.h>
#include <stdio.h>
#include <time.h>
#include "theater.h"
#include "third_party/imgui/imgui.h"

void logf(const char* fmt, ...);
const th_backend* ce_theater();                     // ce_film.cpp
const th_backend* h2_theater();                     // h2.cpp
void theater_screenshot();                          // overlay.cpp: the next frame (without this UI) saved as a picture

namespace {
const float PI = 3.14159265f;
const float FOV = 70.0f * PI / 180.0f, ZOOM_FOV = 28.0f * PI / 180.0f;
const float SENS = 0.0022f;                         // radians a mouse count
const float FREE_SPEED = 1.5f;                      // world units (10 ft) a second, x4 with Shift
const float ORBIT = 0.9f, EYE = 0.62f;   // the orbit's distance, its aim above the body, eye height
const uint32_t SKIP = 10 * 30;                      // skip back / ahead: 10 s
const float FAST = 4.0f;                            // E held

const th_backend* g_b;
int g_mode = TH_FIRST, g_player = -1;
bool g_third;                                       // following: third person (C)
float g_yaw, g_pitch, g_pos[3], g_fov = FOV;        // the orbit's / free camera's look; the camera's last position
// first person: the mouse is a pointer over the interface (the view is the player's own: looking around there was
// the game's own look, Nov 14), as in Halo 3's Theater; third person and the free camera look with it
float g_cur[2] = {-1, -1}, g_scr[2] = {1920, 1080};
ImVec2 g_btn[5][2], g_tl[2];                        // the panel's buttons and the timeline as last drawn (none: x -1)
bool g_paused, g_panel = true, g_hidden;
int g_sel = 2;                                      // the panel's button: 0 screenshot, 1 back, 2 pause, 3 ahead, 4 end
bool g_keys;                                        // the viewer's input is the Theater's (MCC in front, its menu down)
volatile LONG g_dx, g_dy, g_wheel;
bool g_was[256];
LARGE_INTEGER g_t0, g_freq;
th_player g_pl[16];
DWORD g_shot_at;

bool down(int vk) { return (GetAsyncKeyState(vk) & 0x8000) != 0; }

// the pad (theater_pad: its last state from MCC's own XInput poll; the game gets it zeroed): H3's layout. D-pad up /
// down the player, left / right skip (the panel's buttons with it up), A pause (the panel's button), X the panel, Y the
// view (first, third, free), B first / third person, Back the interface, left stick move, right stick look, LB / RB down / up, LT
// faster, RT fast forward, right stick click zoom; Start stays MCC's (its menu)
XINPUT_GAMEPAD g_pad;
DWORD g_pad_at;
WORD g_pad_was;
float stick(SHORT v) { float f = v / 32767.0f; return fabsf(f) < 0.24f ? 0 : (f > 0 ? (f - 0.24f) : (f + 0.24f)) / 0.76f; }
bool pressed(int vk) { return down(vk) && !g_was[vk]; }

void dir(float yaw, float pitch, float f[3]) { f[0] = cosf(yaw) * cosf(pitch); f[1] = sinf(yaw) * cosf(pitch); f[2] = sinf(pitch); }

int next_player(int from, int step) {
    for (int k = 1; k <= 16; k++) {
        int i = ((from + step * k) % 16 + 16) % 16;
        if (g_pl[i].used) return i;
    }
    return from;
}

void start() {
    g_b->players(g_pl);
    g_player = next_player(-1, 1);
    g_mode = TH_FIRST; g_third = false; g_paused = false; g_panel = true; g_hidden = false; g_sel = 2;
    g_fov = FOV;
    float f[3];
    if (g_player >= 0 && g_b->focus(g_player, g_pos, f)) { g_yaw = atan2f(f[1], f[0]); g_pitch = -0.2f; }
    InterlockedExchange(&g_dx, 0); InterlockedExchange(&g_dy, 0); InterlockedExchange(&g_wheel, 0);
    logf("theater: film on, following player %d", g_player);
}

void skip(int ticks) {
    int64_t t = (int64_t)g_b->now() + ticks, end = g_b->length();
    if (t < 0) t = 0;
    if (end && t > end - 1) t = end - 1;
    g_b->seek((uint32_t)t);
}

void press(int button) {
    if (button == 0) { theater_screenshot(); g_shot_at = GetTickCount() | 1; }
    else if (button == 1) skip(-(int)SKIP);
    else if (button == 2) g_paused = !g_paused;
    else if (button == 3) skip((int)SKIP);
    else if (button == 4) { logf("theater: End Film"); g_b->eject(); }
}

void follow(int player) {
    if (player < 0) return;
    float f[3], p[3];
    if (g_mode == TH_FREE && g_b->focus(player, p, f)) { g_yaw = atan2f(f[1], f[0]); g_pitch = -0.2f; }
    g_player = player;
    g_mode = g_third ? TH_THIRD : TH_FIRST;
}

void camera(float dt, float dx, float dy) {
    float f[3], body[3], bf[3];
    bool zoom = g_keys && (down(VK_RBUTTON) || (g_pad.wButtons & XINPUT_GAMEPAD_RIGHT_THUMB));
    g_fov += ((zoom ? ZOOM_FOV : FOV) - g_fov) * fminf(1.0f, dt * 12.0f);
    bool have = g_player >= 0 && g_b->focus(g_player, body, bf);
    if (g_mode != TH_FREE && !have) {                   // nobody to follow (gone): the camera stays where it was
        g_b->camera(TH_FREE, -1, g_pos, g_yaw, g_pitch, g_fov);
        return;
    }
    if (g_mode == TH_FREE && g_b->where) g_b->where(g_pos);   // (from where the walls let it go)
    bool pan = g_keys && down(VK_LMENU);
    if (g_mode == TH_FREE && pan) {                     // Alt: the mouse slides the camera in its own plane
        float r[3] = {sinf(g_yaw), -cosf(g_yaw), 0}, u[3];
        dir(g_yaw, g_pitch + PI / 2, u);
        for (int k = 0; k < 3; k++) g_pos[k] += (r[k] * dx - u[k] * dy) * 0.004f;
    } else if (g_mode != TH_FIRST) {                   // (first person: the player's own aim; the mouse is the pointer)
        g_yaw -= dx * SENS * (g_fov / FOV);
        g_pitch -= dy * SENS * (g_fov / FOV);
        if (g_pitch > 1.5f) g_pitch = 1.5f;
        if (g_pitch < -1.5f) g_pitch = -1.5f;
    }
    if (g_mode == TH_FIRST) {
        bool alive = g_player >= 0 && g_pl[g_player].alive;
        if (alive) {
            g_b->camera(TH_FIRST, g_player, nullptr, 0, 0, g_fov);
            g_pos[0] = body[0]; g_pos[1] = body[1]; g_pos[2] = body[2] + EYE;
            g_yaw = atan2f(bf[1], bf[0]);
            return;
        }
    }
    if (g_mode != TH_FREE) {                            // third person, or a dead player's body: the orbit
        dir(g_yaw, g_pitch, f);
        float off[3] = {-f[0] * ORBIT, -f[1] * ORBIT, -f[2] * ORBIT + g_b->look_at};
        g_b->camera(TH_THIRD, g_player, off, g_yaw, g_pitch, g_fov);
        for (int k = 0; k < 3; k++) g_pos[k] = body[k] + off[k];
        if (g_b->where) g_b->where(g_pos);               // (where it really is: short of a wall)
        return;
    }
    if (g_keys) {                                       // the free camera: W A S D along the look, R / F up and down
        dir(g_yaw, g_pitch, f);
        float r[3] = {sinf(g_yaw), -cosf(g_yaw), 0};
        float v = FREE_SPEED * (down(VK_LSHIFT) || g_pad.bLeftTrigger > 60 ? 4.0f : 1.0f) * dt;
        float fw = (down('W') ? 1.0f : 0) - (down('S') ? 1.0f : 0) + stick(g_pad.sThumbLY), rt = (down('D') ? 1.0f : 0) - (down('A') ? 1.0f : 0) + stick(g_pad.sThumbLX);
        float up = (down('R') || (g_pad.wButtons & XINPUT_GAMEPAD_RIGHT_SHOULDER) ? 1.0f : 0) - (down('F') || (g_pad.wButtons & XINPUT_GAMEPAD_LEFT_SHOULDER) ? 1.0f : 0);
        for (int k = 0; k < 3; k++) g_pos[k] += (f[k] * fw + r[k] * rt) * v;
        g_pos[2] += up * v;
    }
    g_b->camera(TH_FREE, -1, g_pos, g_yaw, g_pitch, g_fov);
}

// ---- the interface, Halo 3's: a timeline top centre, the panel bottom right, the name box bottom centre
const ImU32 BLUE = IM_COL32(150, 205, 255, 255), BLUE_DIM = IM_COL32(150, 205, 255, 110);
const ImU32 PANEL = IM_COL32(8, 14, 34, 225), STRIP = IM_COL32(4, 8, 20, 235);
const ImU32 BTN = IM_COL32(40, 72, 130, 235), BTN_SEL = IM_COL32(125, 180, 245, 255), GLYPH = IM_COL32(235, 242, 255, 255);

// text with a 1 px dark shadow: the timeline floats over the game (bright sky made its time unreadable, film33)
void shadow_text(ImDrawList* dl, ImFont* f, float size, float s, ImVec2 p, ImU32 col, const char* t) {
    dl->AddText(f, size, ImVec2(p.x + 1.5f * s, p.y + 1.5f * s), IM_COL32(0, 0, 0, 200), t);
    dl->AddText(f, size, p, col, t);
}

void clock(char* out, size_t n, uint32_t ticks) { unsigned s = ticks / 30; snprintf(out, n, "%02u:%02u", s / 60, s % 60); }

void glyph(ImDrawList* dl, int kind, ImVec2 c, float r, ImU32 col) {
    if (kind == 0) {                                    // a camera
        dl->AddRectFilled(ImVec2(c.x - r, c.y - r * 0.55f), ImVec2(c.x + r, c.y + r * 0.7f), col, r * 0.15f);
        dl->AddRectFilled(ImVec2(c.x - r * 0.35f, c.y - r * 0.8f), ImVec2(c.x + r * 0.35f, c.y - r * 0.5f), col);
        dl->AddCircleFilled(ImVec2(c.x, c.y + r * 0.08f), r * 0.42f, IM_COL32(40, 72, 130, 255));
        dl->AddCircleFilled(ImVec2(c.x, c.y + r * 0.08f), r * 0.24f, col);
    } else if (kind == 1) {                             // |<
        dl->AddRectFilled(ImVec2(c.x - r * 0.75f, c.y - r * 0.7f), ImVec2(c.x - r * 0.5f, c.y + r * 0.7f), col);
        dl->AddTriangleFilled(ImVec2(c.x + r * 0.65f, c.y - r * 0.7f), ImVec2(c.x + r * 0.65f, c.y + r * 0.7f), ImVec2(c.x - r * 0.4f, c.y), col);
    } else if (kind == 2) {                             // || (playing) or > (paused)
        if (!g_paused) {
            dl->AddRectFilled(ImVec2(c.x - r * 0.55f, c.y - r * 0.7f), ImVec2(c.x - r * 0.15f, c.y + r * 0.7f), col);
            dl->AddRectFilled(ImVec2(c.x + r * 0.15f, c.y - r * 0.7f), ImVec2(c.x + r * 0.55f, c.y + r * 0.7f), col);
        } else dl->AddTriangleFilled(ImVec2(c.x - r * 0.5f, c.y - r * 0.75f), ImVec2(c.x - r * 0.5f, c.y + r * 0.75f), ImVec2(c.x + r * 0.7f, c.y), col);
    } else if (kind == 3) {                             // >|
        dl->AddTriangleFilled(ImVec2(c.x - r * 0.65f, c.y - r * 0.7f), ImVec2(c.x - r * 0.65f, c.y + r * 0.7f), ImVec2(c.x + r * 0.4f, c.y), col);
        dl->AddRectFilled(ImVec2(c.x + r * 0.5f, c.y - r * 0.7f), ImVec2(c.x + r * 0.75f, c.y + r * 0.7f), col);
    } else if (kind == 4) {                             // eject
        dl->AddTriangleFilled(ImVec2(c.x - r * 0.75f, c.y + r * 0.15f), ImVec2(c.x + r * 0.75f, c.y + r * 0.15f), ImVec2(c.x, c.y - r * 0.75f), col);
        dl->AddRectFilled(ImVec2(c.x - r * 0.75f, c.y + r * 0.4f), ImVec2(c.x + r * 0.75f, c.y + r * 0.7f), col);
    } else if (kind == 5) {                             // >> (fast forward)
        dl->AddTriangleFilled(ImVec2(c.x - r, c.y - r * 0.7f), ImVec2(c.x - r, c.y + r * 0.7f), ImVec2(c.x, c.y), col);
        dl->AddTriangleFilled(ImVec2(c.x, c.y - r * 0.7f), ImVec2(c.x, c.y + r * 0.7f), ImVec2(c.x + r, c.y), col);
    }
}

}  // namespace

// overlay.cpp's GetRawInputData hook, for every raw event MCC reads (its WM_INPUT goes to a window of its own, not the
// one the overlay subclasses: film34 turned no camera): the mouse moves the Theater's camera and the game gets none of
// the viewer's mouse or keys (Esc, Tab and F9 still do)
void theater_raw(RAWINPUT* ri) {
    if (!g_b || !g_keys || !ri) return;
    if (ri->header.dwType == RIM_TYPEMOUSE) {
        RAWMOUSE& m = ri->data.mouse;
        if (!(m.usFlags & MOUSE_MOVE_ABSOLUTE)) {
            InterlockedExchangeAdd(&g_dx, m.lLastX);
            InterlockedExchangeAdd(&g_dy, m.lLastY);
        }
        if (m.usButtonFlags & RI_MOUSE_WHEEL) InterlockedExchangeAdd(&g_wheel, (SHORT)m.usButtonData);
        m.lLastX = m.lLastY = 0;
        m.usButtonFlags = 0;
        m.ulRawButtons = 0;
    } else if (ri->header.dwType == RIM_TYPEKEYBOARD) {
        USHORT vk = ri->data.keyboard.VKey;
        if (vk != VK_ESCAPE && vk != VK_TAB && vk != VK_F9) { ri->data.keyboard.VKey = 0xFF; ri->data.keyboard.MakeCode = 0; }
    }
}

bool theater_input(UINT msg, WPARAM wp, LPARAM lp) {
    if (!g_b || !g_keys) return false;
    (void)lp;
    if (msg == WM_INPUT) return true;                   // (if it ever comes here: the raw hook has taken it)
    bool keys = msg >= WM_KEYFIRST && msg <= WM_KEYLAST, mouse = msg >= WM_MOUSEFIRST && msg <= WM_MOUSELAST;
    if (keys && (wp == VK_ESCAPE || wp == VK_TAB || wp == VK_F9)) return false;   // MCC's menu, the scores, the bug report
    return keys || mouse;
}

bool theater_frame(bool menu_up, HWND hwnd) {
    const th_backend* b = ce_theater();
    if (!b->playing()) b = h2_theater();
    if (!b->playing()) b = nullptr;
    if (b != g_b) {
        g_b = b;
        if (!b) { g_keys = false; logf("theater: film off"); return false; }
        QueryPerformanceFrequency(&g_freq);
        QueryPerformanceCounter(&g_t0);
        start();
    }
    if (!b) return false;
    LARGE_INTEGER t;
    QueryPerformanceCounter(&t);
    float dt = (float)(t.QuadPart - g_t0.QuadPart) / (float)g_freq.QuadPart;
    g_t0 = t;
    if (dt > 0.1f) dt = 0.1f;
    g_keys = !menu_up && GetForegroundWindow() == hwnd;
    float dx = (float)InterlockedExchange(&g_dx, 0), dy = (float)InterlockedExchange(&g_dy, 0);
    LONG wheel = InterlockedExchange(&g_wheel, 0);
    b->players(g_pl);
    XINPUT_GAMEPAD pad = g_pad;                         // (the pad: theater_pad)
    if (GetTickCount() - g_pad_at > 500) { memset(&pad, 0, sizeof pad); memset(&g_pad, 0, sizeof g_pad); }   // (none read lately: no pad)
    auto pp = [&](WORD b) { return (pad.wButtons & b) && !(g_pad_was & b); };
    if (g_keys) {
        bool panel_up = g_panel && !g_hidden;
        if (pressed('X') || pp(XINPUT_GAMEPAD_X)) g_panel = !g_panel;
        if (pressed('Z') || pp(XINPUT_GAMEPAD_BACK)) g_hidden = !g_hidden;
        if (pressed(VK_RETURN) || (!panel_up && pp(XINPUT_GAMEPAD_A))) g_paused = !g_paused;
        if (pressed(VK_SPACE) || pp(XINPUT_GAMEPAD_Y)) {   // first person, third person, free camera, round again
            if (g_mode == TH_FIRST) { g_third = true; g_mode = TH_THIRD; g_pitch = -0.2f; }
            else if (g_mode == TH_THIRD) g_mode = TH_FREE;
            else { g_third = false; follow(g_player >= 0 ? g_player : next_player(-1, 1)); }
        }
        if ((pressed('C') || pp(XINPUT_GAMEPAD_B)) && g_mode != TH_FREE) { g_third = !g_third; g_mode = g_third ? TH_THIRD : TH_FIRST; g_pitch = -0.2f; }
        if (pressed(VK_UP) || wheel > 0 || pp(XINPUT_GAMEPAD_DPAD_UP)) follow(next_player(g_player, 1));
        if (pressed(VK_DOWN) || wheel < 0 || pp(XINPUT_GAMEPAD_DPAD_DOWN)) follow(next_player(g_player, -1));
        bool panel = g_panel && !g_hidden;
        bool left = pressed(VK_LEFT) || pp(XINPUT_GAMEPAD_DPAD_LEFT), right = pressed(VK_RIGHT) || pp(XINPUT_GAMEPAD_DPAD_RIGHT);
        bool click = pressed(VK_LBUTTON);
        if (g_mode == TH_FIRST && !g_hidden) {          // first person: the pointer (hover picks a button, a click acts)
            if (g_cur[0] < 0) { g_cur[0] = g_scr[0] * 0.5f; g_cur[1] = g_scr[1] * 0.5f; }
            g_cur[0] = fminf(fmaxf(g_cur[0] + dx, 0), g_scr[0] - 1);
            g_cur[1] = fminf(fmaxf(g_cur[1] + dy, 0), g_scr[1] - 1);
            auto in = [](const ImVec2* r) { return r[0].x >= 0 && g_cur[0] >= r[0].x && g_cur[0] < r[1].x && g_cur[1] >= r[0].y && g_cur[1] < r[1].y; };
            int hover = -1;
            for (int i = 0; i < 5; i++) if (panel && in(g_btn[i])) hover = i;
            if (hover >= 0) g_sel = hover;
            if (click && hover >= 0) press(hover);
            else if (click && in(g_tl) && g_b->length()) {   // the timeline: there
                float f = (g_cur[0] - g_tl[0].x) / (g_tl[1].x - g_tl[0].x);
                g_b->seek((uint32_t)(f * (float)(g_b->length() - 1)));
            }
            click = false;
        }
        if (panel) {                                    // the panel's buttons: Left / Right, left mouse or A presses
            if (left) g_sel = (g_sel + 4) % 5;
            if (right) g_sel = (g_sel + 1) % 5;
            if (click || pp(XINPUT_GAMEPAD_A)) press(g_sel);
        } else {
            if (left) skip(-(int)SKIP);
            if (right) skip((int)SKIP);
        }
        for (int k = 0; k < 256; k++) g_was[k] = down(k);
        // the right stick turns the camera (as the mouse: counts a second at full tilt)
        float rx = stick(pad.sThumbRX), ry = stick(pad.sThumbRY);
        dx += rx * 1100.0f * dt;
        dy -= ry * 800.0f * dt;
        g_pad_was = pad.wButtons;
    } else {
        dx = dy = 0;
        memset(g_was, 1, sizeof g_was);                 // (a key held as the viewer comes back is no press)
    }
    // the film's end: paused on its last frame (Halo 3's Theater holds it there: the end does not end the
    // viewing, Nov 13); back or End Film from there
    uint32_t len = b->length();
    bool at_end = len && b->now() + 1 >= len && !b->seeking();
    if (at_end) g_paused = true;
    b->speed(at_end ? 0.0f : g_keys && (down('E') || g_pad.bRightTrigger > 60) ? FAST : g_paused ? 0.0f : 1.0f);
    if (g_player < 0 || (!g_pl[g_player].used && !b->seeking())) {   // (the film's first player once made; a skip back remakes them: kept)
        g_player = next_player(-1, 1);
        if (g_player >= 0) logf("theater: following player %d", g_player);
    }
    if (g_mode == TH_FIRST) dx = dy = 0;              // (the pointer's)
    if (g_player >= 0 || g_mode == TH_FREE) camera(dt, dx, dy);
    return !g_hidden && !menu_up;                       // (MCC's own menu up: it alone, Nov 13)
}

void theater_draw(ImFont* font, ImFont* label) {
    for (auto& r : g_btn) r[0].x = -1;               // (none drawn: none to point at)
    g_tl[0].x = -1;
    if (!g_b || g_hidden) return;
    ImGuiIO& io = ImGui::GetIO();
    ImDrawList* dl = ImGui::GetForegroundDrawList();
    float W = io.DisplaySize.x, H = io.DisplaySize.y;
    g_scr[0] = W; g_scr[1] = H;
    float pw = fminf(W, H * 16.0f / 9.0f), x0 = (W - pw) * 0.5f, s = H / 1080.0f;   // (Halo 3's 16:9 page)
    float fs = 24.0f * s;
    char a[16], b2[16];
    // the timeline: the film so far, its time under the head, the length at the end
    uint32_t now = g_b->now(), len = g_b->length();
    float tx0 = x0 + pw * 0.367f, tx1 = x0 + pw * 0.632f, ty = H * 0.21f, th = 18.0f * s;
    g_tl[0] = ImVec2(tx0, ty - 6 * s); g_tl[1] = ImVec2(tx1, ty + th + 6 * s);
    float f = len ? fminf(1.0f, (float)now / (float)len) : 0;
    dl->AddRectFilled(ImVec2(tx0, ty), ImVec2(tx1, ty + th), IM_COL32(6, 14, 28, 150));
    dl->AddRect(ImVec2(tx0, ty), ImVec2(tx1, ty + th), BLUE_DIM, 0, 0, 1.5f * s);
    dl->AddRectFilled(ImVec2(tx0, ty), ImVec2(tx0 + (tx1 - tx0) * f, ty + th), IM_COL32(150, 205, 255, 200));
    clock(a, sizeof a, now); clock(b2, sizeof b2, len);
    float hx = tx0 + (tx1 - tx0) * f;
    shadow_text(dl, font, fs, s, ImVec2(fminf(hx, tx1 - 60 * s), ty + th + 6 * s), BLUE, a);
    shadow_text(dl, font, fs, s, ImVec2(tx1 + 10 * s, ty + (th - fs) * 0.5f), BLUE, b2);
    bool fast = g_keys && (down('E') || g_pad.bRightTrigger > 60);
    if (fast || g_b->seeking()) glyph(dl, 5, ImVec2(tx0 - 26 * s, ty + th * 0.5f), 11 * s, BLUE);
    else if (g_paused) glyph(dl, 2, ImVec2(tx0 - 26 * s, ty + th * 0.5f), 11 * s, BLUE);
    // the followed player's name box (not in the free camera)
    if (g_mode != TH_FREE && g_player >= 0 && g_pl[g_player].used) {
        float nx0 = x0 + pw * 0.40f, nx1 = x0 + pw * 0.595f, ny0 = H * 0.872f, ny1 = ny0 + 34 * s;
        dl->AddRectFilled(ImVec2(nx0, ny0), ImVec2(nx1, ny1), IM_COL32(10, 14, 24, 170));
        static const ImU32 TEAM[8] = {IM_COL32(200, 40, 40, 255), IM_COL32(50, 90, 220, 255), IM_COL32(40, 160, 60, 255),
                                     IM_COL32(220, 130, 30, 255), IM_COL32(130, 60, 190, 255), IM_COL32(220, 200, 40, 255),
                                     IM_COL32(120, 80, 40, 255), IM_COL32(230, 120, 170, 255)};
        dl->AddRectFilled(ImVec2(nx0 + 6 * s, ny0 + 5 * s), ImVec2(nx0 + 30 * s, ny1 - 5 * s), TEAM[g_pl[g_player].team & 7]);
        char name[40];
        WideCharToMultiByte(CP_UTF8, 0, g_pl[g_player].name, -1, name, sizeof name, nullptr, nullptr);
        dl->AddText(font, fs, ImVec2(nx0 + 40 * s, ny0 + (ny1 - ny0 - fs) * 0.5f), GLYPH, name);
        float ax = nx1 - 16 * s, ay = (ny0 + ny1) * 0.5f;   // up / down: the next player
        dl->AddTriangleFilled(ImVec2(ax - 6 * s, ay - 3 * s), ImVec2(ax + 6 * s, ay - 3 * s), ImVec2(ax, ay - 11 * s), GLYPH);
        dl->AddTriangleFilled(ImVec2(ax - 6 * s, ay + 3 * s), ImVec2(ax + 6 * s, ay + 3 * s), ImVec2(ax, ay + 11 * s), GLYPH);
    }
    if (g_shot_at && GetTickCount() - g_shot_at < 2000)
        shadow_text(dl, font, fs, s, ImVec2(x0 + pw * 0.675f, H * 0.58f), GLYPH, "Screenshot saved to Pictures");
    if (g_panel) {
        // the panel: the screenshot button and the playback buttons, the selected one's name, the hints
        float px0 = x0 + pw * 0.675f, px1 = x0 + pw * 0.913f, py0 = H * 0.622f, py1 = H * 0.768f, sy = py1 - 34 * s;
        dl->AddRectFilled(ImVec2(px0, py0), ImVec2(px1, py1), PANEL);
        dl->AddRect(ImVec2(px0, py0), ImVec2(px1, py1), IM_COL32(90, 130, 190, 160), 0, 0, 1.5f * s);
        dl->AddRectFilled(ImVec2(px0 + 1, sy), ImVec2(px1 - 1, py1 - 1), STRIP);
        float bw = 44 * s, bh = 38 * s, by = py0 + 10 * s;
        for (int i = 0; i < 5; i++) {
            float bx = i == 0 ? px0 + 10 * s : px1 - 10 * s - (5 - i) * (bw + 4 * s) + 4 * s;
            ImU32 bg = i == g_sel ? BTN_SEL : BTN;
            dl->AddRectFilled(ImVec2(bx, by), ImVec2(bx + bw, by + bh), bg);
            g_btn[i][0] = ImVec2(bx, by); g_btn[i][1] = ImVec2(bx + bw, by + bh);
            bool off = (i == 1 && now == 0) || (i == 3 && len && now + 1 >= len);
            glyph(dl, i, ImVec2(bx + bw * 0.5f, by + bh * 0.5f), 12 * s, off ? IM_COL32(150, 160, 180, 140) : GLYPH);
        }
        static const char* NAMES[5] = {"Screenshot", "Skip Back", "Pause", "Skip Ahead", "End Film"};
        const char* nm = g_sel == 2 && g_paused ? "Play" : NAMES[g_sel];
        dl->AddText(font, fs, ImVec2(px0 + 12 * s, by + bh + 6 * s), BLUE, nm);
        float hx0 = px0 + 10 * s, hy = sy + (34 * s - fs) * 0.5f;   // hints: arrows Navigate, mouse Select
        for (int k = 0; k < 2; k++) {
            float kx = hx0 + k * 22 * s;
            dl->AddRect(ImVec2(kx, hy), ImVec2(kx + 18 * s, hy + fs), GLYPH, 2 * s, 0, 1.2f * s);
            float cx = kx + 9 * s, cy = hy + fs * 0.5f;
            if (k == 0) dl->AddTriangleFilled(ImVec2(cx + 4 * s, cy - 5 * s), ImVec2(cx + 4 * s, cy + 5 * s), ImVec2(cx - 4 * s, cy), GLYPH);
            else dl->AddTriangleFilled(ImVec2(cx - 4 * s, cy - 5 * s), ImVec2(cx - 4 * s, cy + 5 * s), ImVec2(cx + 4 * s, cy), GLYPH);
        }
        dl->AddText(font, fs, ImVec2(hx0 + 48 * s, hy), GLYPH, "Navigate");
        float mx = hx0 + 48 * s + font->CalcTextSizeA(fs, 1e9f, 0, "Navigate").x + 18 * s;
        dl->AddRect(ImVec2(mx, hy), ImVec2(mx + 14 * s, hy + fs), GLYPH, 7 * s, 0, 1.2f * s);   // a mouse, its left button lit
        dl->AddRectFilled(ImVec2(mx + 2 * s, hy + 2 * s), ImVec2(mx + 7 * s, hy + fs * 0.42f), GLYPH);
        dl->AddText(font, fs, ImVec2(mx + 22 * s, hy), GLYPH, "Select");
    }
    if (g_mode == TH_FIRST && g_cur[0] >= 0) {        // first person: the pointer (an arrow, dark edged)
        ImVec2 p(g_cur[0], g_cur[1]);
        float k = 22.0f * s;
        ImVec2 a = p, b(p.x, p.y + k), c(p.x + k * 0.36f, p.y + k * 0.74f), d(p.x + k * 0.72f, p.y + k * 0.72f);
        dl->AddTriangleFilled(a, b, c, GLYPH);
        dl->AddTriangleFilled(a, c, d, GLYPH);
        ImVec2 pts[4] = {a, b, c, d};
        dl->AddPolyline(pts, 4, IM_COL32(0, 0, 0, 220), ImDrawFlags_Closed, 1.5f * s);
    }
    (void)label;
}

// overlay.cpp's XInputGetState hook, MCC's poll of pad 0: while a film plays (and MCC is in front, its menu down) the
// pad is the Theater's and the game gets it zeroed but for Start (MCC's menu)
void theater_pad(XINPUT_STATE* st) {
    if (!g_b || !g_keys || !st) return;
    g_pad = st->Gamepad;
    g_pad_at = GetTickCount();
    WORD keep = st->Gamepad.wButtons & XINPUT_GAMEPAD_START;
    memset(&st->Gamepad, 0, sizeof st->Gamepad);
    st->Gamepad.wButtons = keep;
}
