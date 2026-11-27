// SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
// SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
//
// This SPDX license identifier and copyright notice must not be
// removed, altered, or obscured. Doing so is a material breach of the PolyForm Strict License 1.0.0.

using System;
using System.Runtime.InteropServices;

public static class OwnedFrameClose
{
    const uint WindowClose = 0x0010;

    [DllImport("user32.dll", ExactSpelling = true)]
    static extern uint GetWindowThreadProcessId(IntPtr window, out uint process);

    [DllImport("user32.dll", ExactSpelling = true)]
    static extern bool PostMessageW(IntPtr window, uint message, IntPtr word, IntPtr data);

    public static bool Request(long frameHandle, int expectedProcess)
    {
        if(frameHandle==0 || frameHandle==0xffff || expectedProcess<=0) return false;
        var window=new IntPtr(frameHandle);
        uint process;
        return GetWindowThreadProcessId(window,out process)!=0 && process==(uint)expectedProcess
            && PostMessageW(window,WindowClose,IntPtr.Zero,IntPtr.Zero);
    }
}
