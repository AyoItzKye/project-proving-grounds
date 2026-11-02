; Project Proving Grounds' Windows installer (Inno Setup 6). Built by tools/build_installer.py, which stages the files
; (Payload) and passes the version: ISCC /DAppVersion=0.1.0 /DPayload=<folder> /DBuildDir=<folder> this file.
;
; Installs for the current user (no administrator rights needed) into %LOCALAPPDATA%\Programs\Project Proving Grounds,
; with a Start Menu shortcut to the launcher and an optional desktop one. Asks before each optional step: the Windows
; Security exclusion for the mod's folder (native\bin: Windows Security can mistake the injector that loads the mod
; into MCC for malware) is off unless ticked, and asks for administrator permission only then. Uninstalling removes the
; exclusion again and asks whether to keep the player's LiDAR scans, learned map data and recorded matches.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef Payload
  #error Payload (the staged files) must be given: ISCC /DPayload=<folder>
#endif
#ifndef BuildDir
  #define BuildDir "."
#endif

[Setup]
AppId={{8C3B2F7E-5A41-4D8E-9C6B-1F2E3D4C5B6A}
AppName=Project Proving Grounds
AppVersion={#AppVersion}
AppVerName=Project Proving Grounds {#AppVersion}
AppPublisher=The Project Proving Grounds contributors
DefaultDirName={autopf}\Project Proving Grounds
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir={#BuildDir}
OutputBaseFilename=ProjectProvingGrounds-Setup-{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
LicenseFile={#BuildDir}\license.txt
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\installer\icon.ico
UninstallDisplayName=Project Proving Grounds
WizardStyle=modern
CloseApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"
Name: "defender"; Description: "Add the mod's folder (native\bin) to Windows Security's exclusions, so it does not delete the injector that loads the bots into MCC (asks for administrator permission)"; GroupDescription: "Windows Security:"; Flags: unchecked

[Files]
Source: "{#Payload}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Project Proving Grounds"; Filename: "{app}\python\pythonw.exe"; Parameters: "-I ""{app}\tools\launcher.py"""; WorkingDir: "{app}"; IconFilename: "{app}\installer\icon.ico"; Comment: "PvP bots for Halo: The Master Chief Collection"
Name: "{autodesktop}\Project Proving Grounds"; Filename: "{app}\python\pythonw.exe"; Parameters: "-I ""{app}\tools\launcher.py"""; WorkingDir: "{app}"; IconFilename: "{app}\installer\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\python\pythonw.exe"; Parameters: "-I ""{app}\tools\launcher.py"" --setup"; WorkingDir: "{app}"; Description: "Open Project Proving Grounds and run the first-time setup"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
; the app windows' own Edge profile (tools/appwindow.py)
Type: filesandordirs; Name: "{localappdata}\ProjectProvingGrounds"

[Code]
const
  MARK = '\installer\windows-security-exclusion.txt';

function Quoted(S: String): String;          { a PowerShell single-quoted string: its quotes doubled }
begin
  Result := S;
  StringChangeEx(Result, '''', '''''', True);
  Result := '''' + Result + '''';
end;

function RunElevatedPowerShell(Command: String): Boolean;
var
  Code: Integer;
begin
  Result := ShellExec('runas', 'powershell.exe', '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "' + Command + '"',
                      '', SW_HIDE, ewWaitUntilTerminated, Code) and (Code = 0);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Dir: String;
begin
  if (CurStep = ssPostInstall) and WizardIsTaskSelected('defender') then
  begin
    Dir := ExpandConstant('{app}\native\bin');
    if RunElevatedPowerShell('Add-MpPreference -ExclusionPath ' + Quoted(Dir)) then
      SaveStringToFile(ExpandConstant('{app}') + MARK, Dir, False)
    else
      SuppressibleMsgBox('The Windows Security exclusion was not added (permission was not given, or Windows Security ' +
                         'is managed by another program). The bots still work; if Windows Security removes inject.exe, ' +
                         'the launcher says so.', mbInformation, MB_OK, IDOK);
  end;
end;

var
  KeepData: Boolean;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Dir: AnsiString;
begin
  if CurUninstallStep = usUninstall then
  begin
    if LoadStringFromFile(ExpandConstant('{app}') + MARK, Dir) then
      RunElevatedPowerShell('Remove-MpPreference -ExclusionPath ' + Quoted(String(Dir)));
    // (a silent uninstall keeps them: /SUPPRESSMSGBOXES answers Yes)
    KeepData := SuppressibleMsgBox('Keep your LiDAR scans, what the bots learned on each map and your recorded matches?'
                                   + #13#10 + #13#10 + 'Yes keeps them in ' + ExpandConstant('{app}') + ' (maps and logs ' +
                                   'folders) for a later install; No deletes everything.', mbConfirmation, MB_YESNO,
                                   IDYES) = IDYES;
  end;
  if CurUninstallStep = usPostUninstall then
  begin
    if KeepData then
    begin
      DelTree(ExpandConstant('{app}\native'), True, True, True);
      DelTree(ExpandConstant('{app}\python'), True, True, True);
      DelTree(ExpandConstant('{app}\tools'), True, True, True);
      DelTree(ExpandConstant('{app}\brain'), True, True, True);
    end
    else
      DelTree(ExpandConstant('{app}'), True, True, True);
  end;
end;
