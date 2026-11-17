from __future__ import annotations

import ctypes
import re

def assembly_progress(title, statics, buttons):
    if title or len(statics) < 3 or not set(buttons) <= {"Close", "Do not show again", "Hide Details", "Show Details"}:
        return False
    first, second, third, *details = statics
    if not re.fullmatch(r"(?:Open|Opening|Opened|Loaded)(?: -?\d+)?\nComponents", first):
        indexed = re.fullmatch(r"Opening Component ([1-9][0-9]*) of ([1-9][0-9]*)", first)
        if indexed is None or int(indexed[1]) > int(indexed[2]):
            return False
    if second not in {"Update\nAssembly", "Updating\nAssembly", "Assembly\nUpdated"}:
        return False
    if third not in {"Update\nGraphics", "Generating\nGraphics", "Graphics\nGenerated"}:
        return False
    known = r"(?:\s*|Elapsed time: \d+(?:s| seconds?)|This file was last opened in \d+ seconds?\.|For more information, view: *|Performance Evaluation|Opening File: .+|Post load updating)"
    return all(re.fullmatch(known, detail) for detail in details)


if __name__ == "__main__":
    import json
    import sys

    if sys.argv[1:] != ["--classify"]:
        raise SystemExit("usage: ObserveAssemblyLoad.py --classify < windows.json")
    records = json.load(sys.stdin)
    print(json.dumps([assembly_progress(row["dialog"], row["text"], row["buttons"]) for row in records]))
    raise SystemExit(0)


import Swapp


class AssemblyLoadMonitor(Swapp.Dismisser):
    def scan(self):
        allowed = Swapp.owned_process_ids()
        windows = []

        def top(handle, unused):
            pid = Swapp.wt.DWORD()
            Swapp.user32.GetWindowThreadProcessId(handle, ctypes.byref(pid))
            if pid.value in allowed and Swapp._cls(handle) == "#32770" and Swapp.user32.IsWindowVisible(handle):
                windows.append((handle, pid.value))
            return not self.stop.is_set()

        Swapp.user32.EnumWindows(Swapp.EnumProc(top), 0)
        for handle, pid in windows:
            if self.stop.is_set() or pid not in Swapp.owned_process_ids():
                continue
            title = Swapp._text(handle)
            statics, buttons = [], []

            def child(item, unused):
                role = Swapp._cls(item)
                if role == "Static":
                    value = Swapp._text(item).replace("\r", "")
                    if value:
                        statics.append(value)
                if role == "Button" and Swapp.user32.IsWindowVisible(item) and Swapp.user32.IsWindowEnabled(item):
                    buttons.append(Swapp._text(item))
                return not self.stop.is_set()

            Swapp.user32.EnumChildWindows(handle, Swapp.EnumProc(child), 0)
            is_progress = assembly_progress(title, statics, buttons)
            row = {"kind": "assembly-load-progress" if is_progress else "unclassified-owned-dialog", "dialog": title, "text": statics, "buttons": buttons, "dismissed": False, "process_id": pid}
            destination = self.progress if is_progress else self.log
            if row not in destination:
                destination.append(row)

    def run(self):
        while not self.stop.is_set():
            try:
                self.scan()
            except Exception as error:
                self.log.append({"kind": "assembly-window-query-failed", "error": repr(error), "dismissed": False})
                self.stop.set()
            self.stop.wait(0.25)
