import ctypes
from ctypes import wintypes
import json
import pathlib
import subprocess
import threading
import time

def start_hidden(args, **kwargs):
    startup = subprocess.STARTUPINFO()
    startup.dwFlags = subprocess.STARTF_USESHOWWINDOW | 0x80
    startup.wShowWindow = 0
    process = subprocess.Popen(args, startupinfo=startup, **kwargs)
    audit_root = pathlib.Path(__file__).parent / 'hidden-window-audits'
    audit_root.mkdir(exist_ok=True)
    audit = audit_root / (str(process.pid) + '-' + str(time.time_ns()) + '.jsonl')
    def watch():
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        user32.IsWindowVisible.argtypes = [wintypes.HWND]
        user32.ShowWindowAsync.argtypes = [wintypes.HWND, ctypes.c_int]
        callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        def hide(window, parameter):
            owner = wintypes.DWORD()
            user32.GetWindowThreadProcessId(window, ctypes.byref(owner))
            if owner.value == process.pid and user32.IsWindowVisible(window):
                user32.ShowWindowAsync(window, 0)
                with audit.open('a', encoding='utf-8') as channel:
                    channel.write(json.dumps({'at': time.time(), 'action': 'hide-owned-window', 'pid': process.pid, 'window': int(window)}) + '\n')
            return True
        callback = callback_type(hide)
        user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
        while process.poll() is None:
            user32.EnumWindows(callback, 0)
            time.sleep(0.15)
    threading.Thread(target=watch, daemon=True).start()
    return process
