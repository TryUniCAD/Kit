from __future__ import annotations

import ctypes

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
            stages = (
                {"Open\nComponents", "Opening\nComponents", "Opened\nComponents", "Loaded\nComponents"},
                {"Update\nAssembly", "Updating\nAssembly", "Assembly\nUpdated"},
                {"Update\nGraphics", "Generating\nGraphics", "Graphics\nGenerated"},
            )
            is_progress = not title and 3 <= len(statics) <= 4 and all(statics[index] in values for index, values in enumerate(stages)) and all(not x.strip() for x in statics[3:]) and all(button == "Close" for button in buttons)
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
