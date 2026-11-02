@echo off
rem Builds the temporary diagnostics DLLs (bin\diag.dll: pickup checks, bin\filemon.dll: file opens).
setlocal
rem Visual Studio with the C++ tools, wherever it is installed (vswhere ships with every Visual Studio 2017+)
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
set "VSDIR="
if exist "%VSWHERE%" for /f "usebackq tokens=*" %%i in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "VSDIR=%%i"
if not defined VSDIR (echo Visual Studio with the C++ build tools was not found. & exit /b 1)
call "%VSDIR%\VC\Auxiliary\Build\vcvars64.bat" >nul || exit /b 1
cd /d "%~dp0"
set MH=third_party\minhook\src
cl /nologo /O2 /W3 /EHsc /MT /LD diag.cpp %MH%\hook.c %MH%\buffer.c %MH%\trampoline.c %MH%\hde\hde64.c /Fe:bin\diag.dll /Fo:bin\ || exit /b 1
cl /nologo /O2 /W3 /EHsc /MT /LD filemon.cpp %MH%\hook.c %MH%\buffer.c %MH%\trampoline.c %MH%\hde\hde64.c /Fe:bin\filemon.dll /Fo:bin\ || exit /b 1
cl /nologo /O2 /W3 /EHsc /MT /LD watch.cpp psapi.lib /Fe:bin\watch.dll /Fo:bin\ || exit /b 1
echo BUILD OK bin\diag.dll bin\filemon.dll bin\watch.dll
