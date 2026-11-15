from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import csv
import io
import json
import subprocess
import sys
import threading
import time

import pythoncom
import win32com.client as wc
from win32com.client import VARIANT

PROGID = "SldWorks.Application.34"
EXPECTED_BUILD = "34.5.2"
PROCESSES = (
    "SLDWORKS.exe",
    "sldworks_util.exe",
    "swMsgHandler.exe",
    "SLDWORKS_Splash.exe",
    "SLDEXITAPP.exe",
    "sldProcMon.exe",
)
DOC_PART = 1
DOC_ASSEMBLY = 2
OPEN_SILENT = 1
OPEN_READONLY = 2
SAVE_SILENT = 1
SAVE_COPY = 2

user32 = ctypes.windll.user32
EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)


def _text(h):
    n = user32.GetWindowTextLengthW(h)
    b = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(h, b, n + 1)
    return b.value


def _cls(h):
    b = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(h, b, 256)
    return b.value


def process_ids():
    result = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True, check=True)
    names = {name.casefold() for name in PROCESSES}
    return {int(row[1].replace(",", "")) for row in csv.reader(io.StringIO(result.stdout)) if len(row) >= 2 and row[0].casefold() in names}


def _dismiss_once(log, allowed_pids):
    found = []

    def top(h, _):
        pid = wt.DWORD()
        user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
        if pid.value in allowed_pids and _cls(h) == "#32770" and user32.IsWindowVisible(h):
            found.append(h)
        return True

    user32.EnumWindows(EnumProc(top), 0)
    for d in found:
        title = _text(d)
        buttons = []
        statics = []

        def child(h, _):
            c = _cls(h)
            if c == "Button":
                buttons.append((h, _text(h)))
            elif c == "Static":
                t = _text(h)
                if t:
                    statics.append(t)
            return True

        user32.EnumChildWindows(d, EnumProc(child), 0)
        pick = None
        for pref in ("OK", "&OK", "Close", "&Close", "Yes", "&Yes", "Continue", "Don't Save", "&Don't Save", "No", "&No"):
            for h, t in buttons:
                if t == pref:
                    pick = h
                    break
            if pick:
                break
        if pick:
            log.append({"dialog": title, "text": statics[:4], "button": _text(pick)})
            user32.SendMessageW(pick, 245, 0, 0)


class Dismisser:
    def __init__(self):
        self.log = []
        self.stop = threading.Event()
        self.t = threading.Thread(target=self.run, daemon=True)

    def run(self):
        while not self.stop.is_set():
            try:
                _dismiss_once(self.log, process_ids())
            except Exception as error:
                self.log.append({"error": repr(error)})
                self.stop.set()
            time.sleep(0.5)

    def __enter__(self):
        self.t.start()
        return self

    def __exit__(self, *a):
        self.stop.set()
        self.t.join(timeout=3)


def sweep():
    for p in PROCESSES:
        subprocess.run(["taskkill", "/F", "/IM", p], capture_output=True, check=False)
    time.sleep(4.0)


def cv(obj, name, *args):
    a = getattr(obj, name)
    if args:
        return a(*args)
    if callable(a) and not hasattr(a, "_oleobj_"):
        return a()
    return a


def byref_long():
    return VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)


def byref_bool():
    return VARIANT(pythoncom.VT_BYREF | pythoncom.VT_BOOL, False)


def nothing():
    return VARIANT(pythoncom.VT_DISPATCH, None)


class Sw:
    def __init__(self, visible=False):
        pythoncom.CoInitialize()
        self.diagnostics = []
        self.app = wc.DispatchEx(PROGID)
        self.app.Visible = visible
        self.app.UserControl = False
        try:
            self.app.FrameState = 1
        except Exception as error:
            self.diagnostics.append({"stage": "frame_state", "error": repr(error)})
        self.revision = str(cv(self.app, "RevisionNumber"))
        self.launches = 0

    def close(self):
        try:
            self.app.CloseAllDocuments(True)
        except Exception as error:
            self.diagnostics.append({"stage": "close_documents", "error": repr(error)})
        try:
            cv(self.app, "ExitApp")
        except Exception as error:
            self.diagnostics.append({"stage": "exit_application", "error": repr(error)})
        self.app = None
        pythoncom.CoUninitialize()

    def template(self, kind="part"):
        return str(self.app.GetUserPreferenceStringValue(8 if kind == "part" else 9))

    def new_part(self):
        m = self.app.NewDocument(self.template("part"), 0, 0, 0)
        if m is None:
            raise RuntimeError("NewDocument returned None")
        return m

    def new_assembly(self):
        m = self.app.NewDocument(self.template("assembly"), 0, 0, 0)
        if m is None:
            raise RuntimeError("NewDocument returned None")
        return m

    def open(self, path, doctype=None):
        path = str(path)
        if doctype is None:
            doctype = DOC_ASSEMBLY if path.lower().endswith(".sldasm") else DOC_PART
        e, w = byref_long(), byref_long()
        m = self.app.OpenDoc6(path, doctype, OPEN_SILENT, "", e, w)
        return m, int(e.value), int(w.value)

    def close_doc(self, m):
        try:
            self.app.CloseDoc(str(cv(m, "GetTitle")))
        except Exception as error:
            self.diagnostics.append({"stage": "close_document", "error": repr(error)})

    def save_as(self, m, path):
        e, w = byref_long(), byref_long()
        ok = m.Extension.SaveAs3(str(path), 0, SAVE_SILENT, nothing(), nothing(), e, w)
        return bool(ok), int(e.value), int(w.value)


def mass(m):
    out = {}
    try:
        mp = cv(m.Extension, "CreateMassProperty")
        if mp is None:
            return None
        mp.UseSystemUnits = True
        out["volume"] = float(mp.Volume)
        out["area"] = float(mp.SurfaceArea)
        out["com"] = [float(v) for v in mp.CenterOfMass]
        out["mass"] = float(mp.Mass)
    except Exception as ex:
        out["error"] = repr(ex)
    return out


def bodies(m):
    try:
        b = m.GetBodies2(0, False)
        return 0 if b is None else len(b)
    except Exception:
        return -1


def features(m):
    res = []
    f = cv(m, "FirstFeature")
    while f is not None:
        item = {"name": str(f.Name), "type": str(cv(f, "GetTypeName2"))}
        try:
            warning = byref_bool()
            code = f.GetErrorCode2(warning)
            item["error"] = int(code) if not isinstance(code, tuple) else int(code[0])
            item["warning"] = bool(warning.value) if not isinstance(code, tuple) else bool(code[1])
        except Exception as error:
            item["error_query_error"] = repr(error)
        try:
            item["suppressed"] = bool(cv(f, "IsSuppressed"))
        except Exception as error:
            item["suppression_query_error"] = repr(error)
        dims = []
        d = cv(f, "GetFirstDisplayDimension")
        while d is not None:
            try:
                dd = d.GetDimension2(0)
                dims.append({"name": str(dd.FullName), "value": float(dd.SystemValue)})
            except Exception as error:
                dims.append({"error": repr(error)})
            d = f.GetNextDisplayDimension(d)
        if dims:
            item["dims"] = dims
        res.append(item)
        f = cv(f, "GetNextFeature")
    return res


def rebuild_errors(m):
    try:
        what = cv(m.Extension, "GetWhatsWrongCount")
    except Exception:
        what = None
    return what


def measure(sw, path, rebuild=True):
    rec = {"path": str(path), "session_diagnostics": list(sw.diagnostics)}
    t0 = time.time()
    m, e, w = sw.open(path)
    rec["open_errors"] = e
    rec["open_warnings"] = w
    rec["opened"] = m is not None
    if m is None:
        return rec
    try:
        if rebuild:
            rec["rebuilt"] = bool(m.ForceRebuild3(False))
        rec["whats_wrong"] = rebuild_errors(m)
        rec["bodies"] = bodies(m)
        rec["mass"] = mass(m)
        rec["features"] = features(m)
    finally:
        sw.close_doc(m)
    rec["session_diagnostics"] = list(sw.diagnostics)
    rec["seconds"] = round(time.time() - t0, 2)
    return rec


def emit(obj):
    sys.stdout.write("@@RESULT@@" + json.dumps(obj) + "\n")
    sys.stdout.flush()
