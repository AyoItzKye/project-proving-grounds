# Mute or unmute one program's sound in the Windows volume mixer (every playback device), for test runs of MCC on
# the second monitor with no audio (owner, Oct 24). Windows remembers a program's mute, so always unmute before MCC
# closes, or the owner's next game is silent.
# usage: powershell -ExecutionPolicy Bypass -File mute_app.ps1 [-Process MCC-Win64-Shipping] [-Unmute]
param([string]$Process = "MCC-Win64-Shipping", [switch]$Unmute)

Add-Type -TypeDefinition @"
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.InteropServices;

[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class MMDeviceEnumeratorCo {}

[Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator {
    [PreserveSig] int EnumAudioEndpoints(int dataFlow, int stateMask, out IMMDeviceCollection devices);
}
[Guid("0BD7A1BE-7A1A-44DB-8397-CC5392387B5E"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceCollection {
    [PreserveSig] int GetCount(out uint count);
    [PreserveSig] int Item(uint index, out IMMDevice device);
}
[Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice {
    [PreserveSig] int Activate(ref Guid iid, int clsCtx, IntPtr activationParams, [MarshalAs(UnmanagedType.IUnknown)] out object iface);
}
[Guid("77AA99A0-1BD6-484F-8BC7-2C654C9A9B6F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioSessionManager2 {
    int GetAudioSessionControl();
    int GetSimpleAudioVolume();
    [PreserveSig] int GetSessionEnumerator(out IAudioSessionEnumerator sessions);
}
[Guid("E2F5BB11-0570-40CA-ACDD-3AA01277DEE8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioSessionEnumerator {
    [PreserveSig] int GetCount(out int count);
    [PreserveSig] int GetSession(int index, out IAudioSessionControl2 session);
}
[Guid("bfb7ff88-7239-4fc9-8fa2-07c950be9c6d"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioSessionControl2 {
    int GetState(); int GetDisplayName(); int SetDisplayName(); int GetIconPath(); int SetIconPath();
    int GetGroupingParam(); int SetGroupingParam(); int RegisterAudioSessionNotification();
    int UnregisterAudioSessionNotification(); int GetSessionIdentifier(); int GetSessionInstanceIdentifier();
    [PreserveSig] int GetProcessId(out uint pid);
}
[Guid("87CE5498-68D6-44E5-9215-6DA47EF883D8"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface ISimpleAudioVolume {
    int SetMasterVolume(); int GetMasterVolume();
    [PreserveSig] int SetMute(bool mute, ref Guid context);
    [PreserveSig] int GetMute(out bool mute);
}

public static class AppMute {
    // sets every audio session of the named process on every active playback device; returns how many
    public static int Set(string process, bool mute) {
        var pids = new HashSet<uint>();
        foreach (var p in Process.GetProcessesByName(process)) pids.Add((uint)p.Id);
        int n = 0;
        var en = (IMMDeviceEnumerator)(new MMDeviceEnumeratorCo());
        IMMDeviceCollection devs;
        if (en.EnumAudioEndpoints(0, 1, out devs) != 0) return 0;      // render devices, active
        uint count; devs.GetCount(out count);
        Guid iid = typeof(IAudioSessionManager2).GUID;
        for (uint i = 0; i < count; i++) {
            IMMDevice dev; devs.Item(i, out dev);
            object o; if (dev.Activate(ref iid, 23, IntPtr.Zero, out o) != 0) continue;   // CLSCTX_ALL
            IAudioSessionEnumerator se; ((IAudioSessionManager2)o).GetSessionEnumerator(out se);
            int sc; se.GetCount(out sc);
            for (int k = 0; k < sc; k++) {
                IAudioSessionControl2 s; se.GetSession(k, out s);
                uint pid; s.GetProcessId(out pid);
                if (!pids.Contains(pid)) continue;
                Guid ctx = Guid.Empty;
                ((ISimpleAudioVolume)s).SetMute(mute, ref ctx);
                n++;
            }
        }
        return n;
    }
}
"@

$n = [AppMute]::Set($Process, -not $Unmute)
"{0} {1} audio session(s) of {2}" -f ($(if ($Unmute) { "unmuted" } else { "muted" })), $n, $Process
