# Security

## What the mod does on your PC

- It loads a DLL (`native\bin\botcore.dll`) into Halo: The Master Chief Collection with a small injector
  (`inject.exe`), only while MCC runs with Easy Anti-Cheat off. Antivirus programs often flag DLL injectors; the
  installer offers a Windows Security exclusion for that one folder, off unless you tick it.
- It runs local servers for its windows (the launcher, the Observer, the LiDAR view, the nav painter) on 127.0.0.1
  only: nothing is reachable from other PCs. Actions that change anything need a header only the tool's own page sends.
- It writes files inside its install folder and in its windows' own browser profile
  (`%LOCALAPPDATA%\ProjectProvingGrounds`, never your browser's). It reads MCC's game files (to build the 3D bots and
  pictures on your PC) and MCC's post-game reports. It changes MCC's folder only when you ask the launcher to start
  without clashing mods for one session (those files are renamed and put back).
- It never connects to online services, matchmaking or Xbox network, and sends nothing anywhere.

## Supported versions

The latest release. MCC updates can change the game's code; a new release follows when one does.

## Reporting a vulnerability

Please report it privately: this repository's **Security** tab > **Report a vulnerability**. Say what is affected and
how to reproduce it. Please do not open a public issue for a security problem.
