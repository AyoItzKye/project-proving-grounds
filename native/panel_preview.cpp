// panel_preview.cpp: draws the BOTS panel (bots_panel.cpp) offscreen, no MCC needed, to check its look
// in every state and size (the Master of UI/UX render matrix), and self-tests the roster operations.
//   panel_preview.exe --state normal --size 1920x1080 --out preview.ppm [--yaw 0.35] [--zoom 1] [--bot 0]   (python: PNG)
//   panel_preview.exe --selftest
// states: normal empty off lidar ce eight long quick clear full bugbutton bug bugtext
#include <windows.h>
#include <d3d11.h>
#include <stdio.h>
#include <string.h>
#include "bots_panel.h"
#include "ui_layout.h"
#include "model_view.h"
#include "shared.h"
#include "third_party/imgui/imgui.h"
#include "third_party/imgui/imgui_impl_dx11.h"

extern int hb_panel_firefight;    // bots_panel.cpp: the Firefight lobby's list (3 bots, your team)

void bots_panel_debug(int select, const char* popup);
void bots_panel_debug_tab(int tab);
void bots_panel_debug_reroll_failed(bool f);
void bots_panel_debug_edit(int i, int game);
void bots_panel_debug_view(int species);
void bots_panel_debug_looks();
void bots_panel_debug_yaw(float yaw);
void bots_panel_debug_zoom(float z);
void bots_panel_debug_time(double t);

static ID3D11Device* g_dev;                  // the profile view's pictures (bots_panel_env make_texture)
static ID3D11DeviceContext* g_ctx;
static unsigned long long render_model(const wchar_t* path, const mv_pick* picks, int n, const mv_colors& c, float yaw,
                                       int w, int h) {
    return mv_render(g_dev, g_ctx, path, picks, n, c, yaw, w, h);
}
static bool model_has(const wchar_t* path, const char* region, const char* perm) { return mv_has(g_dev, path, region, perm); }
// the panel's sounds, printed instead of played (tools/test_panel_sounds.py reads them; tests stay quiet)
static void print_sound(int kind, uint32_t volume) {
    static const char* NAME[] = { "move", "select", "back", "open", "error" };
    printf("sound %s %u\n", kind >= 0 && kind < 5 ? NAME[kind] : "?", volume);
}

static unsigned long long make_texture(int w, int h, const unsigned char* rgba) {
    D3D11_TEXTURE2D_DESC d{};
    d.Width = w; d.Height = h; d.MipLevels = 1; d.ArraySize = 1; d.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
    d.SampleDesc.Count = 1; d.Usage = D3D11_USAGE_DEFAULT; d.BindFlags = D3D11_BIND_SHADER_RESOURCE;
    D3D11_SUBRESOURCE_DATA sd{ rgba, (UINT)w * 4, 0 };
    ID3D11Texture2D* t = nullptr;
    ID3D11ShaderResourceView* v = nullptr;
    if (FAILED(g_dev->CreateTexture2D(&d, &sd, &t))) return ImTextureID_Invalid;
    g_dev->CreateShaderResourceView(t, nullptr, &v);
    t->Release();
    return (ImTextureID)(intptr_t)v;
}

static int fails;
#define CHECK(c, msg) do { if (!(c)) { printf("FAIL: %s\n", msg); fails++; } } while (0)

static int selftest() {
    hb_roster r{};
    roster_fill(r, 2, 4, 3, HB_STYLE_ANY, 7);
    CHECK(r.n == 8 && roster_on_team(r, 0) == 4 && roster_on_team(r, 1) == 4, "2 teams x 4");
    for (int i = 0; i < r.n; i++) {
        CHECK(strlen(r.bot[i].name) > 0 && strlen(r.bot[i].name) <= 15, "name length");
        for (int k = 0; k < i; k++) CHECK(_stricmp(r.bot[i].name, r.bot[k].name) != 0, "names unique");
    }
    roster_fill(r, 4, 4, 4, 0, 9);                                  // 16 asked, 15 fit: every team cut evenly
    CHECK(r.n == 15, "capped at 15");
    CHECK(roster_on_team(r, 3) == 3 && roster_on_team(r, 0) == 4, "the cap takes the last team's last bot");
    int tiers[5] = {};
    for (int i = 0; i < r.n; i++) tiers[r.bot[i].tier < 5 ? r.bot[i].tier : 4]++;
    CHECK(tiers[0] && tiers[1] && tiers[2] && tiers[3], "mixed deals every difficulty");
    CHECK(!roster_add(r, 0, 1, 0, 3), "no 16th bot");
    for (int i = 0; i < r.n; i++) r.bot[i].team = 0;                  // all on red: balance spreads them
    roster_balance(r);
    for (int t = 0; t < 4; t++) CHECK(roster_on_team(r, t) >= 3 && roster_on_team(r, t) <= 4, "balanced within one");
    int before[4]; for (int t = 0; t < 4; t++) before[t] = roster_on_team(r, t);
    roster_shuffle(r, 11);
    for (int t = 0; t < 4; t++) CHECK(roster_on_team(r, t) == before[t], "shuffle keeps team sizes");
    roster_rename_all(r, 5);
    for (int i = 0; i < r.n; i++) for (int k = 0; k < i; k++) CHECK(_stricmp(r.bot[i].name, r.bot[k].name) != 0, "renamed unique");
    char second[16]; strcpy_s(second, r.bot[1].name);
    roster_remove(r, 0);
    CHECK(r.n == 14 && strcmp(r.bot[0].name, second) == 0, "remove shifts the rest up");
    CHECK(roster_max_teams(1) == 2 && roster_max_teams(5) == 8, "Halo: CE two teams, the others eight");
    // botcore.ini round trip: what the panel writes, botcore (and tools/botctl.py) reads back the same
    r.bot[3].style = 6; strcpy_s(r.bot[4].name, "Ghost, the 3rd");
    r.bot[5].tier = 4;                                                // Scaling, a bot's own difficulty ("scaling")
    CHECK(!strcmp(tier_key(4), "scaling") && !strcmp(tier_name(4), "Scaling"), "Scaling's key and name");
    {
        hb_roster q{};
        roster_fill(q, 2, 4, 5, HB_STYLE_ANY, 3);                     // quick setup's Scaling: every bot on it
        int on = 0;
        for (int i = 0; i < q.n; i++) on += q.bot[i].tier == 4;
        CHECK(q.n == 8 && on == 8, "quick setup's Scaling puts every bot on Scaling");
    }
    {   // Firefight (4 players): its list holds 3 bots on one team, whatever quick setup or Add asks for
        hb_panel_firefight = 1;
        hb_roster q{};
        roster_fill(q, 4, 5, 3, HB_STYLE_ANY, 7);
        bool more = roster_add(q, 0, 3, HB_STYLE_ANY, 9);
        CHECK(q.n == 3 && q.teams == 1 && !more && roster_max_teams(5) == 1, "Firefight: 3 bots, one team, Add stops");
        hb_panel_firefight = 0;
        CHECK(roster_max_teams(5) == 8, "multiplayer keeps its eight teams after Firefight");
    }
    char path[MAX_PATH]; GetTempPathA(MAX_PATH, path); strcat_s(path, "hb_roster_test.ini");
    FILE* f = nullptr; fopen_s(&f, path, "w");
    if (f) { fprintf(f, "enabled=1\n"); roster_write(f, r); fclose(f); }
    hb_roster back{}; back.teams = 2;
    fopen_s(&f, path, "r");
    char line[128];
    while (f && fgets(line, sizeof line, f)) roster_parse_line(line, back);
    if (f) fclose(f);
    DeleteFileA(path);
    CHECK(back.n == r.n && back.teams == r.teams, "round trip: count and teams");
    for (int i = 0; i < r.n && i < back.n; i++)
        CHECK(!strcmp(back.bot[i].name, r.bot[i].name) && back.bot[i].team == r.bot[i].team && back.bot[i].tier == r.bot[i].tier
              && back.bot[i].style == r.bot[i].style, "round trip: every bot the same");
    // the Settings tab's re-roll: 15 unique names, clan tags of 2-4 characters (or none), the experience and the
    // armor effects choice written and read back
    wchar_t pp[MAX_PATH]; GetTempPathW(MAX_PATH, pp); wcscat_s(pp, L"hb_profiles_test.ini");
    CHECK(profiles_reroll(pp, 1, 3, 77), "re-roll writes the file");
    CHECK(profiles_count() == 15 && profiles_experience() == 1 && profiles_effects() == 3, "re-roll: 15 bots, Modern, effects frequent");
    for (int fx = 0; fx < 4; fx++)
        CHECK(profiles_reroll(pp, 1, fx, 80 + fx) && profiles_effects() == fx, "every armor effects level written and read back");
    {   // a file from the first re-roll build said effects=0 / effects=1: read as none / common
        FILE* f = nullptr;
        _wfopen_s(&f, pp, L"w");
        if (f) { fputs("experience=modern\neffects=1\nbot=Old,5,\n", f); fclose(f); }
        bots_panel_profiles(pp);
        CHECK(profiles_effects() == 2 && profiles_count() == 1, "an old effects=1 file reads as common");
    }
    CHECK(profiles_reroll(pp, 1, 3, 77), "re-roll again after the old file");
    int clans = 0;
    for (int i = 0; i < profiles_count(); i++) {
        CHECK(strlen(profile_name(i)) > 0 && strlen(profile_name(i)) <= 15, "profile name length");
        for (int k = 0; k < i; k++) CHECK(_stricmp(profile_name(i), profile_name(k)) != 0, "profile names unique");
        size_t cl = strlen(profile_clan(i));
        CHECK(cl == 0 || (cl >= 2 && cl <= 4), "clan tag 2-4 characters or none");
        clans += cl > 0;
    }
    CHECK(clans > 0 && clans < 15, "some bots in clans, some not");
    CHECK(profiles_reroll(pp, 0, 0, 78) && profiles_experience() == 0 && profiles_effects() == 0, "re-roll: Original, effects none");
    // the species choice (brain/looks.py elite_share): Spartans only / Elites only / mixed at a share, kept by a save
    CHECK(profiles_species() == 1 && profiles_elite_share() == -1, "re-roll by default: mixed, each game's own share");
    CHECK(profiles_reroll(pp, 0, 0, 79, 0) && profiles_species() == 0, "re-roll: Spartans only");
    CHECK(profiles_reroll(pp, 0, 0, 79, 2) && profiles_species() == 2 && profiles_elite_share() == -1, "re-roll: Elites only");
    CHECK(profiles_reroll(pp, 0, 0, 79, 1, 35) && profiles_species() == 1 && profiles_elite_share() == 35, "re-roll: mixed, 35% Elites");
    CHECK(profiles_save(), "save after the species re-roll");
    bots_panel_profiles(pp);
    CHECK(profiles_species() == 1 && profiles_elite_share() == 35, "the species share kept by a save and a reload");
    CHECK(profiles_reroll(pp, 0, 0, 78), "re-roll back to the defaults");
    // the bot editor's hand-set looks: set, replace, clear, and kept through a save and a reload with the clan tag
    char clan0[8]; strcpy_s(clan0, profile_clan(0));
    profile_over_set(0, "h3.primary", 5);
    profile_over_set(0, "h3.helmet", 2);
    profile_over_set(0, "h3.primary", 7);
    profile_over_set(0, "reach.seed", 3);
    profile_over_set(0, "reach.seed", -1);
    CHECK(profile_over_get(0, "h3.primary") == 7 && profile_over_get(0, "h3.helmet") == 2 && profile_over_get(0, "reach.seed") == -1
          && profile_over_get(0, "h3.prim") == -1, "editor values set, replaced and cleared");
    CHECK(profiles_save(), "editor values saved");
    bots_panel_profiles(pp);
    CHECK(profile_over_get(0, "h3.primary") == 7 && profile_over_get(0, "h3.helmet") == 2 && !strcmp(profile_clan(0), clan0)
          && profiles_count() == 15, "editor values and clan tag read back");
    DeleteFileW(pp);
    wchar_t bad[MAX_PATH]; GetTempPathW(MAX_PATH, bad); wcscat_s(bad, L"hb_no_such_dir\\bot_profiles.ini");
    CHECK(!profiles_reroll(bad, 1, 2, 79) && profiles_count() == 15 && profiles_experience() == 0,
          "a re-roll that cannot write says so and keeps the bots it had");
    // every copy of the player's id in a bot's configuration becomes the bot's (Halo 3 keeps a second at +0x78, at
    // any alignment; MCC's post-game report named every bot after the player)
    uint8_t cfg[0xB8] = {};
    const uint64_t person = 0x0009000012345678ull, bot = 0xB07B07B000000003ull;
    static const size_t ATS[3] = { 0x10, 0x78, 0x31 };
    for (size_t at : ATS) memcpy(cfg + at, &person, 8);
    cfg[0x20] = 0x78;                                     // a lone byte of the id stays as it is
    hb_replace_id(cfg, sizeof cfg, person, bot);
    bool all = true;
    for (size_t at : ATS) all &= !memcmp(cfg + at, &bot, 8);
    CHECK(all && cfg[0x20] == 0x78, "every copy of the player's id replaced by the bot's, nothing else");
    printf(fails ? "panel self-test FAILED (%d)\n" : "panel self-test OK\n", fails);
    return fails ? 1 : 0;
}

int main(int argc, char** argv) {
    const char* state = "normal";
    const char* out = "preview.ppm";
    int W = 1920, H = 1080;
    float clicks[8][2]; int nclick = 0;    // --click x,y[;x,y..]: real mouse clicks there one after another (the
                                           // the player's path, not a debug hook: a box opened, then an item
                                           // in it)
    float yaw = -99;                       // --yaw radians: the profile view's 3D bot turned so (QC from every side)
    float zoom = -1;                       // --zoom 0..1: how close it frames the bot (0 the whole figure, 1 the torso)
    double fx_time = -1;                   // --time s: the armor effects held at that moment (still renders)
    int bot = 0;                           // --bot n: whose profile the edit<game> states show (QC of rolled looks)
    struct key_press { ImGuiKey key; bool shift; };
    key_press keys[64]; int nkey = 0;      // --keys tab*3,stab,space,down,enter,esc: key presses one after another,
                                           // after the clicks (the keyboard pass; stab: Shift+Tab)
    bool readonly = false;                 // --readonly: the profiles file made read-only once set up (a save that fails)
    uint32_t sounds = 60;                  // --sounds 0-100: the panel's sound volume (printed: print_sound)
    const char* wavs = nullptr;            // --wavs <dir>: the five sounds written there as WAV files, then out
    float hover[2] = { -1, -1 };
    const char* sets = "";                 // --set h3.elite_helmet=12,h3.species=1: hand-set looks on that bot (QC of
    for (int i = 1; i < argc; i++) {       // every piece)
        if (!strcmp(argv[i], "--set") && i + 1 < argc) { sets = argv[++i]; continue; }
        if (!strcmp(argv[i], "--selftest")) return selftest();
        if (!strcmp(argv[i], "--state") && i + 1 < argc) state = argv[++i];
        else if (!strcmp(argv[i], "--out") && i + 1 < argc) out = argv[++i];
        else if (!strcmp(argv[i], "--size") && i + 1 < argc) sscanf_s(argv[++i], "%dx%d", &W, &H);
        else if (!strcmp(argv[i], "--click") && i + 1 < argc) {
            for (const char* p = argv[++i]; *p && nclick < 8; p += strcspn(p, ";"), p += *p == ';')
                if (sscanf_s(p, "%f,%f", &clicks[nclick][0], &clicks[nclick][1]) == 2) nclick++;
        }
        else if (!strcmp(argv[i], "--keys") && i + 1 < argc) {
            static const struct { const char* name; ImGuiKey key; } NAMES[] = { {"tab", ImGuiKey_Tab}, {"stab", ImGuiKey_Tab},
                {"space", ImGuiKey_Space}, {"enter", ImGuiKey_Enter}, {"esc", ImGuiKey_Escape}, {"up", ImGuiKey_UpArrow},
                {"down", ImGuiKey_DownArrow}, {"left", ImGuiKey_LeftArrow}, {"right", ImGuiKey_RightArrow},
                {"pad_up", ImGuiKey_GamepadDpadUp}, {"pad_down", ImGuiKey_GamepadDpadDown},   // the pad (Xbox)
                {"pad_left", ImGuiKey_GamepadDpadLeft}, {"pad_right", ImGuiKey_GamepadDpadRight},
                {"pad_a", ImGuiKey_GamepadFaceDown}, {"pad_b", ImGuiKey_GamepadFaceRight},
                {"pad_lb", ImGuiKey_GamepadL1}, {"pad_rb", ImGuiKey_GamepadR1} };
            for (const char* p = argv[++i]; *p; p += strcspn(p, ","), p += *p == ',') {
                char name[16] = {}; int n = 1;
                sscanf_s(p, "%15[a-z_]*%d", name, (unsigned)sizeof name, &n);
                for (const auto& k : NAMES)
                    if (!strcmp(name, k.name))
                        for (int r = 0; r < n && nkey < 64; r++) keys[nkey++] = { k.key, !strcmp(name, "stab") };
            }
        }
        else if (!strcmp(argv[i], "--readonly")) readonly = true;
        else if (!strcmp(argv[i], "--hover") && i + 1 < argc) sscanf_s(argv[++i], "%f,%f", &hover[0], &hover[1]);   // mouse rests there (tooltips)
        else if (!strcmp(argv[i], "--sounds") && i + 1 < argc) sounds = (uint32_t)atoi(argv[++i]);
        else if (!strcmp(argv[i], "--wavs") && i + 1 < argc) wavs = argv[++i];
        else if (!strcmp(argv[i], "--yaw") && i + 1 < argc) yaw = (float)atof(argv[++i]);
        else if (!strcmp(argv[i], "--zoom") && i + 1 < argc) zoom = (float)atof(argv[++i]);
        else if (!strcmp(argv[i], "--time") && i + 1 < argc) fx_time = atof(argv[++i]);
        else if (!strcmp(argv[i], "--bot") && i + 1 < argc) bot = atoi(argv[++i]);
    }
    if (wavs) {                            // the panel's five sounds at --sounds' volume, for the test to read
        static const char* NAME[] = { "move", "select", "back", "open", "error" };
        static char buf[12000];
        for (int k = 0; k < 5; k++) {
            int n = panel_sound_wav(k, sounds, buf, (int)sizeof buf);
            char path[MAX_PATH]; sprintf_s(path, "%s\\%s.wav", wavs, NAME[k]);
            FILE* fp = nullptr;
            if (!n || fopen_s(&fp, path, "wb") != 0 || !fp) { printf("cannot write %s\n", path); return 1; }
            fwrite(buf, 1, n, fp);
            fclose(fp);
        }
        return 0;
    }
    ID3D11Device* dev = nullptr; ID3D11DeviceContext* ctx = nullptr;
    if (FAILED(D3D11CreateDevice(nullptr, D3D_DRIVER_TYPE_HARDWARE, nullptr, 0, nullptr, 0, D3D11_SDK_VERSION, &dev, nullptr, &ctx)) &&
        FAILED(D3D11CreateDevice(nullptr, D3D_DRIVER_TYPE_WARP, nullptr, 0, nullptr, 0, D3D11_SDK_VERSION, &dev, nullptr, &ctx))) {
        printf("no D3D11 device\n"); return 1;
    }
    D3D11_TEXTURE2D_DESC td{};
    td.Width = W; td.Height = H; td.MipLevels = 1; td.ArraySize = 1; td.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
    td.SampleDesc.Count = 1; td.BindFlags = D3D11_BIND_RENDER_TARGET;
    ID3D11Texture2D* rt = nullptr; dev->CreateTexture2D(&td, nullptr, &rt);
    ID3D11RenderTargetView* rtv = nullptr; dev->CreateRenderTargetView(rt, nullptr, &rtv);
    td.BindFlags = 0; td.Usage = D3D11_USAGE_STAGING; td.CPUAccessFlags = D3D11_CPU_ACCESS_READ;
    ID3D11Texture2D* st = nullptr; dev->CreateTexture2D(&td, nullptr, &st);

    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO();
    io.IniFilename = nullptr;
    io.DisplaySize = ImVec2((float)W, (float)H);
    io.DeltaTime = 1.0f / 60.0f;
    float scale = mcc_content((float)W, (float)H).s;   // (as botcore: MCC's fitted menu page, ui_layout.h)
    ImFont* f = io.Fonts->AddFontFromFileTTF("C:\\Windows\\Fonts\\bahnschrift.ttf", 21.0f * scale);
    if (!f) f = io.Fonts->AddFontDefault();
    io.FontDefault = f;
    ImGui::StyleColorsDark();
    ImGui_ImplDX11_Init(dev, ctx);

    // the state to draw
    hb_roster r{};
    uint32_t enabled = 1, difficulty = 3, lidar = 0, lidar_players = 16, collector = 0;
    bool open = true;
    int title = 5, select = -1;
    const char* popup = nullptr;
    roster_fill(r, 2, 4, 4, HB_STYLE_ANY, 42);
    r.bot[1].style = 0; r.bot[2].style = 6; r.bot[5].style = 1;
    if (!strcmp(state, "normal")) select = 2;
    else if (!strcmp(state, "empty")) r.n = 0;
    else if (!strcmp(state, "off")) enabled = 0;
    else if (!strcmp(state, "lidar")) lidar = 1;
    else if (!strcmp(state, "scaling")) { difficulty = 5; roster_fill(r, 2, 4, 5, HB_STYLE_ANY, 42); select = 2; }
    // the footer on Scaling, every bot on it (brain/scaling.py)
    else if (!strcmp(state, "collector")) collector = 1;
    else if (!strcmp(state, "collectoroff")) { collector = 1; enabled = 0; }   // on, but greyed out: no bots
    else if (!strcmp(state, "ce")) { title = 1; r.bot[0].team = 2; r.teams = 3; }
    else if (!strncmp(state, "firefight", 9)) {           // Firefight's own list: 3 bots, your team (botcore.cpp ff_seed)
        hb_panel_firefight = 1; roster_fill(r, 1, 3, 3, HB_STYLE_ANY, 42); select = 1;
        if (!strcmp(state, "firefightquick")) popup = "Quick setup";
        if (!strcmp(state, "firefightempty")) { r.n = 0; select = -1; }
    }
    else if (!strcmp(state, "eight")) { roster_fill(r, 8, 2, 4, HB_STYLE_ANY, 5); select = 9; }
    else if (!strcmp(state, "full")) { roster_fill(r, 3, 5, 4, 0, 8); select = 0; }
    else if (!strcmp(state, "long")) {
        for (int i = 0; i < r.n; i++) sprintf_s(r.bot[i].name, "WWWWWWWWWWWWW%02d", i);
        select = 0;
    } else if (!strcmp(state, "quick")) popup = "Quick setup";
    else if (!strcmp(state, "quickscaling")) { popup = "Quick setup"; difficulty = 5; }
    else if (!strcmp(state, "clear")) popup = "Remove all bots";
    else if (!strcmp(state, "advanced") || !strcmp(state, "advancedprof")) {   // the Advanced tab (Scaling); prof: a
        wchar_t tmp[MAX_PATH]; GetTempPathW(MAX_PATH, tmp); wcscat_s(tmp, L"hb_profiles_preview.ini");   // locked rating
        profiles_reroll(tmp, 0, 1, 42);                                         // and a custom profile in use
        wchar_t sc[MAX_PATH]; GetTempPathW(MAX_PATH, sc); wcscat_s(sc, L"scaling.ini");
        FILE* fs = nullptr;
        if (_wfopen_s(&fs, sc, L"w") == 0 && fs) {
            if (!strcmp(state, "advancedprof"))
                fprintf(fs, "lock=1\nrating=900\nuse=1\nprofile=Aim first|reaction=80|aim=150|turn=120\n");
            fclose(fs);
        }
        difficulty = 5;
        bots_panel_debug_tab(2);
    }
    else if (!strcmp(state, "mod") || !strcmp(state, "reroll") || !strcmp(state, "rerollerr") || !strcmp(state, "modnone")
             || !strncmp(state, "edit", 4)) {
        wchar_t tmp[MAX_PATH]; GetTempPathW(MAX_PATH, tmp); wcscat_s(tmp, L"hb_profiles_preview.ini");   // the Settings tab
        if (!strcmp(state, "modnone")) { DeleteFileW(tmp); bots_panel_profiles(tmp); }   // no profiles file yet
        else profiles_reroll(tmp, !strncmp(state, "edit", 4) && strchr(state + 5, 'm') ? 1 : 0, 1, 42);   // Original
        // (edit..m: Modern), effects rare
        bots_panel_debug_tab(1);
        if (!strcmp(state, "reroll") || !strcmp(state, "rerollerr")) popup = "Re-roll bot profiles";
        bots_panel_debug_reroll_failed(!strcmp(state, "rerollerr"));   // the file could not be written
        if (!strncmp(state, "edit", 4)) {   // edit<game 0-5>[c][e][o][n]: the profile view as rolled; c: some looks
            int game = state[4] >= '0' && state[4] <= '5' ? state[4] - '0' : 2;   // changed by hand, e: the species
            static const char* KEY[6] = { "ce", "h2", "h3", "reach", "h2a", "h4" };   // set to Elite, o: Reach
            const char* fl = state + 5;                                               // showing the other species, n:
            char k[32];                                                               // no look file (made before one),
            if (strchr(fl, 'c')) {                                                    // s: set to Spartan (each on the --bot shown)
                sprintf_s(k, "%s.primary", KEY[game]); profile_over_set(bot, k, 3);
                sprintf_s(k, "%s.color", KEY[game]); profile_over_set(bot, k, 3);
                sprintf_s(k, "%s.helmet", KEY[game]); profile_over_set(bot, k, 4);
            }
            if (strchr(fl, 'e')) { sprintf_s(k, "%s.species", KEY[game]); profile_over_set(bot, k, 1); }
            if (strchr(fl, 's')) { sprintf_s(k, "%s.species", KEY[game]); profile_over_set(bot, k, 0); }
            if (strchr(fl, 'f')) profile_over_set(bot, "reach.gender", 1);      // f: a Reach Spartan set female
            for (const char* p = sets; *p;) {
                char kv[64] = {}; int len = (int)strcspn(p, ",");
                strncpy_s(kv, p, len < 63 ? len : 63);
                if (char* eq = strchr(kv, '=')) { *eq = 0; profile_over_set(bot, kv, atoi(eq + 1)); }
                p += len + (p[len] == ',');
            }
            if (strchr(fl, 'c') || strchr(fl, 'e') || strchr(fl, 's') || strchr(fl, 'f') || *sets) profiles_save();
            bots_panel_debug_edit(bot, game);
            if (!strchr(fl, 'n')) bots_panel_debug_looks();
            if (strchr(fl, 'o')) bots_panel_debug_view(1);
            if (strchr(fl, 'r')) bots_panel_debug_yaw(2.6f);      // r: turned round (the back)
            if (yaw > -99) bots_panel_debug_yaw(yaw);
            if (zoom >= 0) bots_panel_debug_zoom(zoom);
            if (fx_time >= 0) bots_panel_debug_time(fx_time);
            popup = "Bot editor";
        }
    }
    bots_panel_env e{};
    e.roster = &r; e.enabled = &enabled; e.difficulty = &difficulty; e.lidar_mode = &lidar; e.lidar_players = &lidar_players; e.collector = &collector;
    static uint32_t scale_games = 5;
    e.scale_games = &scale_games;
    e.title = title; e.scale = scale; e.f_title = e.f_head = e.f_body = e.f_small = f; e.open = &open;
    g_dev = dev; g_ctx = ctx;
    e.make_texture = make_texture;
    e.render_model = render_model; e.model_has = model_has; e.model_zoom = mv_set_zoom; e.model_head = mv_head; e.model_headroom = mv_set_headroom;
    e.sounds = &sounds; e.play_sound = print_sound;
    for (int k = 0; k < nkey; k++) e.pad |= keys[k].key >= ImGuiKey_GamepadStart && keys[k].key <= ImGuiKey_GamepadRStickDown;

    io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard | ImGuiConfigFlags_NavEnableGamepad;   // as the overlay while
    io.BackendFlags |= ImGuiBackendFlags_HasGamepad;                                             // the panel is open
    wchar_t prof[MAX_PATH]; GetTempPathW(MAX_PATH, prof); wcscat_s(prof, L"hb_profiles_preview.ini");
    if (readonly) SetFileAttributesW(prof, FILE_ATTRIBUTE_READONLY);
    int k0 = 3 + 3 * nclick;                                 // the keys after the clicks: key j down on frame k0 + 2j
    int frames = k0 + 2 * nkey + 2 > 8 ? k0 + 2 * nkey + 2 : 8;   // a few frames: layout, popups and the atlas settle;
    int settled = frames;                                    // after clicks or keys 1.5 s more, in real time: what they
    if (nclick || nkey || hover[0] >= 0) frames += 30;                        // started (a look export) comes in
    for (int frame = 0; frame < frames; frame++) {
        if (frame >= settled) Sleep(50);
        if (frame >= k0 && frame < k0 + 2 * nkey) {          // down, then up the next frame
            const key_press& kp = keys[(frame - k0) / 2];
            bool down = (frame - k0) % 2 == 0;
            if (kp.shift && down) io.AddKeyEvent(ImGuiMod_Shift, true);
            io.AddKeyEvent(kp.key, down);
            if (kp.shift && !down) io.AddKeyEvent(ImGuiMod_Shift, false);
        }
        int k = (frame - 2) / 3 < nclick - 1 ? (frame - 2) / 3 : nclick - 1;   // click k: moved there, pressed on
        if (k >= 0) {                                                        // frame 3 + 3k, released the next
            io.AddMousePosEvent(clicks[k][0], clicks[k][1]);
            if (frame == 3 + 3 * k) io.AddMouseButtonEvent(0, true);
            if (frame == 4 + 3 * k) io.AddMouseButtonEvent(0, false);
        }
        if (hover[0] >= 0 && frame >= k0 + 2 * nkey) io.AddMousePosEvent(hover[0], hover[1]);
        ImGui_ImplDX11_NewFrame();
        ImGui::NewFrame();
        // a stand-in for the lobby behind the panel: MCC's dark backdrop and its tile row
        ImDrawList* bg = ImGui::GetBackgroundDrawList();
        bg->AddRectFilledMultiColor(ImVec2(0, 0), io.DisplaySize, IM_COL32(9, 30, 44, 255), IM_COL32(4, 14, 22, 255),
                                    IM_COL32(2, 8, 12, 255), IM_COL32(6, 22, 34, 255));
        float w16 = H * 16.0f / 9.0f, x0 = (W - w16) * 0.5f;
        for (int k = 0; k < 5; k++)
            bg->AddRect(ImVec2(x0 + w16 * (0.13f + k * 0.127f), H * 0.146f), ImVec2(x0 + w16 * (0.25f + k * 0.127f), H * 0.292f),
                        IM_COL32(78, 132, 168, 160));
        if (!strncmp(state, "bug", 3)) {                    // the bug report over a match: bugbutton, bug, bugtext
            static bool bopen = strcmp(state, "bugbutton") != 0;
            static char btext[1001] = "";
            if (frame == 0 && !strcmp(state, "bugtext"))
                strcpy_s(btext, "Blue bot got stuck on the stairs by the flag for about 30 seconds, then walked off the ledge.");
            bug_report_env be{ scale, f, true, &bopen, btext, (int)sizeof btext, false };
            bug_report_ui(be);
        } else {
            if (frame == 1) bots_panel_debug(select, popup);
            bots_panel(e);
        }
        ImGui::Render();
        float clear[4] = { 0, 0, 0, 1 };
        ctx->OMSetRenderTargets(1, &rtv, nullptr);
        ctx->ClearRenderTargetView(rtv, clear);
        D3D11_VIEWPORT vp{ 0, 0, (float)W, (float)H, 0, 1 };
        ctx->RSSetViewports(1, &vp);
        ImGui_ImplDX11_RenderDrawData(ImGui::GetDrawData());
    }
    if (readonly) SetFileAttributesW(prof, FILE_ATTRIBUTE_NORMAL);
    ctx->CopyResource(st, rt);
    D3D11_MAPPED_SUBRESOURCE m;
    if (FAILED(ctx->Map(st, 0, D3D11_MAP_READ, 0, &m))) { printf("readback failed\n"); return 1; }
    FILE* fp = nullptr;
    fopen_s(&fp, out, "wb");
    if (!fp) { printf("cannot write %s\n", out); return 1; }
    fprintf(fp, "P6\n%d %d\n255\n", W, H);
    for (int y = 0; y < H; y++) {
        const uint8_t* row = (const uint8_t*)m.pData + y * m.RowPitch;
        for (int x = 0; x < W; x++) fwrite(row + x * 4, 1, 3, fp);
    }
    fclose(fp);
    ctx->Unmap(st, 0);
    printf("wrote %s (%dx%d, %s)\n", out, W, H, state);
    ImGui_ImplDX11_Shutdown();
    ImGui::DestroyContext();
    return 0;
}
