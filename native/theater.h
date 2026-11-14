// theater.h: Halo 3's Theater controls over a film of Halo: CE or Halo 2 (theater.cpp drives, each game's film
// player answers: ce_film.cpp, h2.cpp)
#pragma once
#include <windows.h>
#include <xinput.h>
#include <stdint.h>

struct ImFont;

enum th_cam { TH_GAME, TH_FIRST, TH_THIRD, TH_FREE };
const float TH_LOOK_AT = 0.25f;                       // CE's orbit aim above a body's origin (world units; th_backend.look_at)
const float TH2_LOOK_AT = 0.5f;                       // Halo 2's: its bodies' origin is at the feet (0.25 aimed at the knees)

struct th_player { bool used, alive; int team; wchar_t name[16]; };

struct th_backend {
    bool (*playing)();                                // a film plays now
    uint32_t (*now)();                                // the film's tick (30 a second)
    uint32_t (*length)();                             // the film's ticks
    void (*players)(th_player out[16]);               // by player index
    // the player's body (alive, or the body it left): its origin and facing (world units); false: none
    bool (*focus)(int player, float pos[3], float fwd[3]);
    // TH_GAME: the game's own camera back. TH_FIRST: the player's eyes. TH_THIRD: pos is the camera's offset from the
    // player's body. TH_FREE: pos is the camera. yaw / pitch radians, fov radians (horizontal)
    void (*camera)(int mode, int player, const float pos[3], float yaw, float pitch, float fov);
    void (*speed)(float s);                           // 0 paused, 1 normal
    void (*seek)(uint32_t tick);                      // the film at this tick (back or ahead)
    bool (*seeking)();                                // a seek still running
    void (*eject)();                                  // the film ends (back to the Theater)
    void (*where)(float pos[3]);                      // the free camera where the game let it go (it stops at walls)
    float look_at;                                    // the orbit aims this far above the body's origin (world units)
};

// overlay.cpp, every frame: true while a film plays and the Theater's interface draws (theater_draw in its ImGui frame)
bool theater_frame(bool menu_up, HWND hwnd);
void theater_draw(ImFont* font, ImFont* label);
// overlay.cpp's window procedure, in a match: true when the message is the Theater's (the game does not get it)
bool theater_input(UINT msg, WPARAM wp, LPARAM lp);
// overlay.cpp's GetRawInputData hook: each raw event MCC reads (the camera's mouse; the game gets none while a film plays)
void theater_raw(RAWINPUT* ri);
// overlay.cpp's XInputGetState hook: MCC's poll of pad 0 (the Theater's while a film plays, the game gets it zeroed)
void theater_pad(XINPUT_STATE* st);
