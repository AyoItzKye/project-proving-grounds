// native/input_gate.h: ImGui hears the window's keys only while botcore's own UI is up (overlay.cpp wndproc: the lobby's
// tile and panel, the bug report over a match). A key let go while it was not listening stayed down for it: after an
// ODST match the panel ran on through its controls as if Right were held (Nov 8; a key pressed as the match ended,
// its release lost while nothing listened). When ImGui starts listening again it forgets the keys it had down.
// overlay.cpp and native/tests/test_input_gate.cpp use it (an ImGuiIO, or anything with its two calls).
#pragma once

struct hb_input_gate {
    bool fed = false;                       // ImGui heard the window's input last frame
    template <class IO> bool frame(bool fed_now, IO& io) {   // each frame; true when listening resumed (keys forgotten)
        bool resumed = fed_now && !fed;
        fed = fed_now;
        if (resumed) {
            io.ClearEventsQueue();          // (a press queued before the gap, its release never came)
            io.ClearInputKeys();
        }
        return resumed;
    }
};
