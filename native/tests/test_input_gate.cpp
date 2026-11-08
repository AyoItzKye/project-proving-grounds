// native/tests/test_input_gate.cpp: the BOTS panel running on through its controls after an ODST match (Nov 8), with
// ImGui's own keyboard navigation over a row of buttons: Right goes down while ImGui listens, its release comes while
// it does not (overlay.cpp's wndproc feeds it only under botcore's UI), and it listens again.
//   1. without native/input_gate.h the focus keeps moving right frame after frame (the bug, shown)
//   2. with it the held key is forgotten when listening resumes: the focus stays put
//   3. and a new press of Right still moves it (the panel's keys are not lost)
// usage: built and run by tools/test_native_input_gate.py
#include <stdio.h>
#include "../input_gate.h"
#include "../third_party/imgui/imgui.h"
#include "../third_party/imgui/imgui_internal.h"

static int fails;
static void check(bool ok, const char* what) {
    printf("%s %s\n", ok ? "ok  " : "FAIL", what);
    fails += !ok;
}

static ImGuiID frame() {                     // one frame of a row of 40 buttons; the focused one's id after it
    ImGuiIO& io = ImGui::GetIO();
    io.DeltaTime = 1.0f / 60.0f;
    ImGui::NewFrame();
    ImGui::SetNextWindowPos(ImVec2(0, 0));
    ImGui::SetNextWindowSize(io.DisplaySize);
    ImGui::Begin("panel", nullptr, ImGuiWindowFlags_NoDecoration);
    for (int k = 0; k < 40; k++) {
        char id[8];
        snprintf(id, sizeof id, "b%02d", k);
        if (k) ImGui::SameLine();
        ImGui::Button(id);
    }
    ImGui::End();
    ImGui::Render();
    return ImGui::GetCurrentContext()->NavId;
}

static int moves(int n) {                    // how many of n frames moved the focus
    int m = 0;
    ImGuiID at = frame();
    for (int k = 0; k < n; k++) {
        ImGuiID now = frame();
        m += now != at;
        at = now;
    }
    return m;
}

// Right pressed while ImGui listens, released while it does not; then a second of frames with it listening again
static int run_on(bool gated) {
    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO();
    io.DisplaySize = ImVec2(4000, 200);
    io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard;
    unsigned char* px; int w, h;
    io.Fonts->GetTexDataAsRGBA32(&px, &w, &h);
    hb_input_gate gate;
    gate.frame(true, io);                    // listening (the lobby)
    frame();
    io.AddKeyEvent(ImGuiKey_RightArrow, true);
    frame();
    if (gated) gate.frame(false, io);        // not listening (the match ending): Right's release is lost
    frame();
    if (gated) gate.frame(true, io);         // listening again (back in the lobby, the panel opened)
    int m = moves(60);
    if (gated) {                             // 3. a new press (and release) still moves the focus, then it rests
        ImGuiID a = frame();
        io.AddKeyEvent(ImGuiKey_RightArrow, true);
        frame();
        io.AddKeyEvent(ImGuiKey_RightArrow, false);
        frame();
        ImGuiID b = frame();
        check(a != b && moves(30) == 0, "a new Right press after resuming moves the focus, then it rests");
    }
    ImGui::DestroyContext();
    return m;
}

int main() {
    int stuck = run_on(false);
    check(stuck > 5, "without the gate the lost release keeps the focus moving (the bug)");
    printf("     (moved %d of 60 frames)\n", stuck);
    int held = run_on(true);
    check(held == 0, "with the gate the focus stays put after listening resumes");
    printf("     (moved %d of 60 frames)\n", held);
    return fails ? 1 : 0;
}
