@echo off
rem Builds bin\panel_preview.exe: the BOTS panel drawn offscreen (no MCC) and its roster self-test, and
rem bin\test_zoom.exe: a bot's scope level into CE / Halo 2 / Halo 3 actions (shared.h hb_set_zoom).
rem usage: build_preview.bat     then: bin\panel_preview.exe --selftest   or   --state normal --size 1920x1080 --out x.ppm
setlocal
rem Visual Studio with the C++ tools, wherever it is installed (vswhere ships with every Visual Studio 2017+)
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
set "VSDIR="
if exist "%VSWHERE%" for /f "usebackq tokens=*" %%i in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "VSDIR=%%i"
if not defined VSDIR (echo Visual Studio with the C++ build tools was not found. & exit /b 1)
call "%VSDIR%\VC\Auxiliary\Build\vcvars64.bat" >nul || exit /b 1
cd /d "%~dp0"
if not exist bin\preview mkdir bin\preview
set IG=third_party\imgui
cl /nologo /O2 /W3 /EHsc /MT panel_preview.cpp bots_panel.cpp model_view.cpp d3dcompiler.lib %IG%\imgui.cpp %IG%\imgui_draw.cpp %IG%\imgui_tables.cpp %IG%\imgui_widgets.cpp %IG%\imgui_impl_dx11.cpp d3d11.lib /Fe:bin\panel_preview.exe /Fo:bin\preview\ || exit /b 1
echo BUILD OK bin\panel_preview.exe
cl /nologo /O2 /W3 /EHsc /MT test_zoom.cpp /Fe:bin\test_zoom.exe /Fo:bin\preview\ || exit /b 1
echo BUILD OK bin\test_zoom.exe
