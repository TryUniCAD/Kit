# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import traceback
from uuid import uuid4

if not __debug__:
    raise RuntimeError("Run verification without Python optimization")

root = Path(sys.argv[1]).resolve()
bin_path = Path(sys.executable).resolve().parent
(phase,) = sys.argv[2:]
if phase not in {"edit", "reopen"}:
    raise ValueError(phase)
if (root / f"Native-{phase}.json").exists():
    raise FileExistsError("A receipt for this phase already exists")
instance = root / f"Native-{phase}-{uuid4().hex}"
instance.mkdir()
for key, suffix in {
    "APPDATA": "Roaming",
    "LOCALAPPDATA": "Local",
    "TEMP": "Temp",
    "TMP": "Temp",
    "XDG_CONFIG_HOME": "Config",
    "XDG_CACHE_HOME": "Cache",
    "XDG_DATA_HOME": "Data",
    "FREECAD_USER_HOME": "FreeCAD",
}.items():
    directory = instance / suffix
    directory.mkdir(exist_ok=True)
    os.environ[key] = str(directory)
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["PATH"] = str(bin_path) + os.pathsep + os.environ.get("PATH", "")
application_directory = os.add_dll_directory(str(bin_path))
sys.path.insert(0, str(bin_path))
import FreeCAD as App
import Part
import Sketcher
import Spreadsheet


def path_sha(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def write(path, values):
    path.write_text(
        json.dumps(values, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def process_start():
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel.GetCurrentProcess
    handle.restype = wintypes.HANDLE
    times = kernel.GetProcessTimes
    times.argtypes = [wintypes.HANDLE, *[ctypes.POINTER(wintypes.FILETIME)] * 4]
    times.restype = wintypes.BOOL
    creation, termination, kernel_time, user_time = (
        wintypes.FILETIME() for _ in range(4)
    )
    if not times(
        handle(),
        *[
            ctypes.byref(value)
            for value in (creation, termination, kernel_time, user_time)
        ],
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    return f"windows:{(creation.dwHighDateTime << 32) + creation.dwLowDateTime}"


def actual_library(name):
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    find = kernel.GetModuleHandleW
    find.argtypes = [wintypes.LPCWSTR]
    find.restype = wintypes.HMODULE
    get = kernel.GetModuleFileNameW
    get.argtypes = [wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD]
    get.restype = wintypes.DWORD
    buffer = ctypes.create_unicode_buffer(32768)
    module = find(name)
    if not module or not get(module, buffer, len(buffer)):
        raise ctypes.WinError(ctypes.get_last_error())
    return {"path": buffer.value, "sha256": path_sha(buffer.value)}


def vector(value):
    return [float(value.x), float(value.y), float(value.z)]


def geometry(shape):
    if shape.isNull():
        return {
            "shape_type": "null",
            "body_count": 0,
            "volume_mm3": None,
            "world_bounds_mm": None,
            "com_mm": None,
        }
    bounds = shape.BoundBox
    solids = shape.Solids
    mass = sum(item.Volume for item in solids)
    center = (
        None
        if not mass
        else [
            sum(item.Volume * getattr(item.CenterOfMass, component) for item in solids)
            / mass
            for component in ("x", "y", "z")
        ]
    )
    return {
        "shape_type": shape.ShapeType,
        "is_valid": bool(shape.isValid()),
        "body_count": len(solids),
        "volume_mm3": float(shape.Volume),
        "world_bounds_mm": [
            [bounds.XMin, bounds.YMin, bounds.ZMin],
            [bounds.XMax, bounds.YMax, bounds.ZMax],
        ],
        "com_mm": center,
    }


def control(name):
    doc = App.newDocument(name)
    try:
        box = doc.addObject("Part::Box", "IndependentBox")
        box.Length = 37
        box.Width = 21
        box.Height = 16
        box.Placement.Base = App.Vector(0, 0, -5)
        count = doc.recompute()
        return {
            "native_type": box.TypeId,
            "recomputed": count,
            "state": list(box.State),
            **geometry(box.Shape),
        }
    finally:
        App.closeDocument(doc.Name)


def native_extrusion_control(name, reversed_, symmetric):
    doc = App.newDocument(name)
    try:
        sketch = doc.addObject("Sketcher::SketchObject", "IndependentRectangle")
        vertices = (
            App.Vector(0, 0, 0),
            App.Vector(37, 0, 0),
            App.Vector(37, 21, 0),
            App.Vector(0, 21, 0),
        )
        for first, second in zip(vertices, (*vertices[1:], vertices[0])):
            sketch.addGeometry(Part.LineSegment(first, second), False)
        feature = doc.addObject("Part::Extrusion", "IndependentExtrusion")
        feature.Base = sketch
        feature.Dir = App.Vector(0, 0, 1)
        feature.LengthFwd = 16 if symmetric else 11
        feature.LengthRev = 0 if symmetric else 5
        feature.Reversed = reversed_
        feature.Symmetric = symmetric
        feature.Solid = True
        count = doc.recompute()
        return {"recomputed": count, **feature_values(feature)}
    finally:
        App.closeDocument(doc.Name)


def feature_values(feature):
    base = feature.Base
    return {
        "name": feature.Name,
        "native_type": feature.TypeId,
        "linked_sketch": (
            {
                "name": base.Name,
                "type": base.TypeId,
                "geometry_count": base.GeometryCount,
                "constraint_count": base.ConstraintCount,
            }
            if base is not None
            else None
        ),
        "dir": vector(feature.Dir),
        "dir_mode": str(feature.DirMode),
        "reversed": bool(feature.Reversed),
        "symmetric": bool(feature.Symmetric),
        "solid": bool(feature.Solid),
        "end_condition": getattr(feature, "EndCondition", None),
        "length_fwd_mm": float(feature.LengthFwd.Value),
        "length_rev_mm": float(feature.LengthRev.Value),
        "expressions": {
            str(prop): str(value) for prop, value in feature.ExpressionEngine
        },
        "state": list(feature.State),
        "geometry": geometry(feature.Shape),
    }


def sheet_values(sheet, cell_names):
    return {
        alias: {
            "address": address,
            "contents": str(sheet.getContents(address)),
            "value": str(sheet.get(address)),
        }
        for alias, address in cell_names.items()
    }


def snapshot(feature, sheet, aliases):
    return {
        "feature": feature_values(feature),
        "spreadsheet": sheet_values(sheet, aliases),
    }


def rebuild(doc, feature):
    feature.touch()
    return doc.recompute()


def error_record(error):
    return {
        "type": type(error).__name__,
        "message": str(error),
        "traceback": traceback.format_exc(),
    }


def inspect_one(name, package, report, previous):
    row = report["cases"][name] = {}
    source = root / "Originals" / package["path"]
    row["original_sha256_before"] = path_sha(source)
    if row["original_sha256_before"] != package["sha256"]:
        row["error"] = {
            "type": "ValueError",
            "message": "Original does not match preparation",
        }
        return
    path = source
    destination = root / "Restored" / f"{name}-restored.FCStd"
    if phase == "reopen":
        saved = previous["cases"][name].get("saved_sha256")
        if not saved or not destination.is_file():
            row["error"] = {"type": "ValueError", "message": "No save to reopen"}
            return
        path = destination
        row["opened_sha256"] = path_sha(path)
        if row["opened_sha256"] != saved:
            row["error"] = {
                "type": "ValueError",
                "message": "Restored save no longer matches phase one",
            }
            return
    doc = None
    try:
        doc = App.openDocument(str(path))
        row["document"] = {
            "name": doc.Name,
            "file": doc.FileName,
            "object_types": {feature.Name: feature.TypeId for feature in doc.Objects},
        }
        (feature,) = [item for item in doc.Objects if item.TypeId == "Part::Extrusion"]
        (sheet,) = [item for item in doc.Objects if item.TypeId == "Spreadsheet::Sheet"]
        fields = package["archive_metadata"]["expected_drivers"]
        aliases = {
            driver.split(".", 1)[1]: sheet.getCellFromAlias(driver.split(".", 1)[1])
            for driver in fields.values()
        }
        row["loaded"] = snapshot(feature, sheet, aliases)
        row["initial_recompute"] = rebuild(doc, feature)
        row["rebuilt"] = snapshot(feature, sheet, aliases)
        if phase == "edit":
            edits = (
                {"depth_total": "20 mm"}
                if name == "symmetric"
                else {"depth_forward": "14 mm", "depth_reverse": "8 mm"}
            )
            row["edits"] = {}
            for alias, value in edits.items():
                edit = row["edits"][alias] = {
                    "requested": value,
                    "before": snapshot(feature, sheet, aliases),
                }
                cell = aliases[alias]
                original = sheet.getContents(cell)
                try:
                    sheet.set(cell, value)
                    edit["after_write"] = snapshot(feature, sheet, aliases)
                    edit["recompute"] = rebuild(doc, feature)
                    edit["edited"] = snapshot(feature, sheet, aliases)
                except Exception as error:
                    edit["error"] = error_record(error)
                finally:
                    sheet.set(cell, original)
                    edit["restore_recompute"] = rebuild(doc, feature)
                    edit["restored"] = snapshot(feature, sheet, aliases)
            row["before_save"] = snapshot(feature, sheet, aliases)
            if destination.exists():
                raise FileExistsError(destination)
            doc.saveAs(str(destination))
            row["saved_sha256"] = path_sha(destination)
            row["saved_bytes"] = destination.stat().st_size
            row["saved_name"] = destination.name
    except Exception as error:
        row["error"] = error_record(error)
    finally:
        if doc is not None:
            App.closeDocument(doc.Name)
        row["original_sha256_after"] = path_sha(source)
        row["original_bytes_unchanged"] = (
            row["original_sha256_before"]
            == row["original_sha256_after"]
            == package["sha256"]
        )


def native_controls(controls, expected):
    for name, (low, high) in expected.items():
        value = controls[name]
        if name not in ("before", "after"):
            value = value["geometry"]
        if (
            value["body_count"] != 1
            or not value["is_valid"]
            or abs(value["volume_mm3"] - 37 * 21 * (high - low)) > 1e-8
        ):
            raise RuntimeError(
                f"Unhealthy independently authored native control {name}: {value}"
            )
        if value["world_bounds_mm"] != [[0.0, 0.0, low], [37.0, 21.0, high]]:
            raise RuntimeError(
                f"Incorrect independent native control bounds for {name}: {value}"
            )


manifest = load(root / "Preparation.json")
preferences = {
    key: App.ConfigGet(key)
    for key in ("UserAppData", "UserParameter", "SystemParameter")
}
if not all(
    Path(value).resolve().is_relative_to(instance) for value in preferences.values()
):
    raise RuntimeError(f"FreeCAD preferences escaped isolated profile: {preferences}")
assert (
    bytes.fromhex(path_sha(App.__file__)).hex()
    == "e6d9c7609613c4f8247b8157386ea27adffa102b3e1f8c5b9b0b0e912e0bfde0"
)
assert not App.listDocuments()
report = {
    "phase": phase,
    "source_revision": manifest["revision"],
    "preparation_sha256": path_sha(root / "Preparation.json"),
    "session": instance.name,
    "started_utc": datetime.now(timezone.utc).isoformat(),
    "pid": os.getpid(),
    "process_start": process_start(),
    "python": {
        "path": sys.executable,
        "sha256": path_sha(sys.executable),
        "version": sys.version,
    },
    "native_version": list(App.Version()),
    "native_modules": {
        name: {"path": module.__file__, "sha256": path_sha(module.__file__)}
        for name, module in (
            ("FreeCAD", App),
            ("Part", Part),
            ("Sketcher", Sketcher),
            ("Spreadsheet", Spreadsheet),
        )
    },
    "native_library": actual_library("FreeCADApp.dll"),
    "config": preferences,
    "cases": {},
    "controls": {},
}
previous = load(root / "Native-edit.json") if phase == "reopen" else None
if previous:
    assert (
        previous["pid"] != report["pid"]
        and previous["process_start"] != report["process_start"]
        and previous["session"] != report["session"]
    )
else:
    (root / "Restored").mkdir()
report["controls"]["before"] = control("IndependentBefore")
for name, package in manifest["packages"].items():
    try:
        report["controls"][name] = native_extrusion_control(
            "Native" + name.title(), package["reversed"], name == "symmetric"
        )
    except Exception as error:
        report["controls"][name] = {"error": error_record(error)}
    write(root / f"Native-{phase}.json", report)
native_controls(
    report["controls"],
    {
        "before": (-5, 11),
        "forward": (-5, 11),
        "reversed": (-11, 5),
        "symmetric": (-8, 8),
    },
)
for name, package in manifest["packages"].items():
    inspect_one(name, package, report, previous)
    write(root / f"Native-{phase}.json", report)
report["controls"]["after"] = control("IndependentAfter")
report["documents_after_close"] = sorted(App.listDocuments())
native_controls(report["controls"], {"after": (-5, 11)})
report["ended_utc"] = datetime.now(timezone.utc).isoformat()
write(root / f"Native-{phase}.json", report)
print(
    json.dumps(
        {
            "phase": phase,
            "pid": report["pid"],
            "process_start": report["process_start"],
            "report_sha256": path_sha(root / f"Native-{phase}.json"),
            "case_errors": {
                name: value["error"]["message"]
                for name, value in report["cases"].items()
                if "error" in value
            },
            "remaining_documents": report["documents_after_close"],
        },
        sort_keys=True,
    ),
    flush=True,
)
