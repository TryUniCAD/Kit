from __future__ import annotations

import argparse
import hashlib
import json
import math
import ntpath
from pathlib import Path

from Classes import registry
from Core import Load, Store
from defs.Definition import load_definition
from convert.adapters.solidworks.Container.Container import SldprtArchive


SOURCE_LOCK = Path(__file__).resolve().parents[3] / "solidworks/v2026/heldout/DrawingSourceLock01.json"
DISCLOSED = ("D00EmptySheet", "D01FrontView", "D02MovedFrontView")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked_bytes(path, sha256):
    data = path.read_bytes()
    require(digest(data) == sha256, f"locked digest differs for {path.name}")
    return data


def checked_artifacts(root, case):
    name = case["name"]
    author = root / name / "author"
    saved = checked_bytes(author / (name + ".SLDDRW"), case["native_sha256"])
    require(len(saved) == case["native_bytes"], f"locked length differs for {name}")
    record = json.loads(checked_bytes(author / "Record.json", case["record_sha256"][0]))
    reopened = json.loads(checked_bytes(root / name / "fresh-reopen" / "Record.json", case["record_sha256"][1]))
    require(record["passed"] and reopened["passed"] and reopened["drawing_result"]["source_immutable"], f"native source phase failed for {name}")
    return saved, record["drawing_result"]["saved"], reopened["drawing_result"]


def reencode(data, registry_value, archive):
    document, reader = load_definition(data, registry_value, 19000, archive=archive, name="Contents/Definition")
    require(document.head.cls == "uiDrawingDoc_c" and not document.tail and not reader.left(), "Definition did not consume the complete drawing")
    store = Store(1, registry_value, 19000)
    registry_value.run_store("uiModelDoc_c.Serialize", store, document.head.f, document.head)
    registry_value.run_store("uiDrawingDoc_c.Serialize.own", store, document.head.f, document.head)
    require(bytes(store.out) == data and store.count == reader.count, "drawing Definition failed its exact round trip")
    return document.head["model"], reader.count


def check_header(data, registry_value):
    archive = Load(data, 1, registry_value, 19000)
    header = archive.obj()
    require(header.cls == "moHeader_c" and not archive.left(), "drawing Header2 requires a complete moHeader_c")
    store = Store(1, registry_value, 19000)
    store.obj(header)
    require(bytes(store.out) == data and store.count == archive.count, "drawing Header2 failed its exact round trip")
    return header, archive.count


def nodes(owner):
    return [item["o"] for item in owner["f60"]["list"]["items"]]


def compare_numeric(label, actual, expected):
    for value, target in zip(actual, expected, strict=True):
        require(math.isclose(value, target, rel_tol=1e-9, abs_tol=1e-12), f"decoded {label} differs from the native authoring record")


def view_transform(view):
    record = view["f5e0"]
    matrix = [record["f08"][f"m{index}"] for index in range(9)] if record["has_matrix"] else [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
    return [*matrix, *(record[key] for key in ("f58", "f60", "f68", "f70"))]


def compare_view(model, view, expected, header):
    require(view["f18"]["f08"] == expected["name"] and view["f1018"] == expected["orientation"], "decoded drawing view name or orientation differs")
    compare_numeric("view position", [view["f778"]["x"], view["f778"]["y"]], expected["position_m"])
    compare_numeric("view scale", [view["f780"] / view["f788"]], [expected["scale"]])
    compare_numeric("view outline", [view[key] for key in ("f6d8", "f6e0", "f6e8", "f6f0")], expected["outline_m"])
    compare_numeric("view transform", view_transform(view), expected["model_to_view"][:13])
    references = model["fa8"]["f30"]["items"]
    properties = model["f16a8"]
    require(len(references) == 1 and len(properties["f08"]) == 1 and properties["f18"] is model, "drawing reference manager ownership differs")
    reference = view["f5d8"]
    entry = references[0]["o"]
    require(reference["f3b0"] is entry and properties["f08"][0]["model"]["f3b0"] is entry, "view and property manager did not reuse the same native external directory entry")
    stem = ntpath.splitext(ntpath.basename(expected["resolved_reference_path"]))[0]
    require(entry["shared"]["h10"]["f08"] == stem and entry["shared"]["f20"] == 2, "drawing resolves to the wrong native part")
    require(reference["f3c0"]["f08"] == expected["configuration"], "drawing view references the wrong part configuration")
    require(header["bboxflag"] != 0, "drawing Header2 has no view bounds")
    low_x, low_y, high_x, high_y = expected["outline_m"]
    radius = math.hypot(high_x - low_x, high_y - low_y) / 2
    compare_numeric("drawing header bounds", [header["bbox"][f"b{index}"] for index in range(10)], [*expected["position_m"], 0.0, high_x, high_y, 0.0, low_x, low_y, 0.0, radius])
    return 30


def compare_sheet(model, header, authored, reopened):
    sheets = [node for node in nodes(model) if node.cls == "moDrSheet"]
    require(len(sheets) == 1 and model["f1430"] is sheets[0], "drawing active sheet ownership differs")
    sheet = sheets[0]
    require(sheet["f18"]["f08"] == authored["sheet"], "decoded sheet name differs")
    measured = authored["sheet_properties"]
    compare_numeric("sheet properties", [sheet[key] for key in ("f39c", "f3c0", "f3f8", "f400", "f3f0", "f3e8")], [measured[index] for index in (0, 1, 2, 3, 5, 6)])
    views = [node for node in nodes(sheet) if node.cls in ("moAbsoluteView", "moDrView")]
    expected = authored["view"]
    require(header["f38"]["shared"]["f20"] == 4 and model["fa8"]["f38"]["shared"]["f20"] == 4, "drawing headers carry the wrong native kind")
    if expected is None:
        require(not views and not header["bboxflag"] and model["fa8"]["f30"] is None, "empty drawing contains model view state")
        return 6
    require(len(views) == 1 and views[0].cls == "moAbsoluteView" and reopened.get("edited") is not None, "expected one editable native model view")
    return 6 + compare_view(model, views[0], expected, header)


def check_case(registry_value, root, case):
    saved, authored, reopened = checked_artifacts(root, case)
    archive = SldprtArchive.from_bytes(saved)
    require(archive.format_version == 4 and "_MO_VERSION_19000/History" in archive.streams, "drawing requires its pinned native container and archive version")
    definition = archive.require("Contents/Definition")
    header_data = archive.require("Header2")
    model, model_map = reencode(definition, registry_value, archive)
    header, header_map = check_header(header_data, registry_value)
    checks = compare_sheet(model, header, authored, reopened)
    return {
        "name": case["name"], "native_sha256": case["native_sha256"], "semantic_numeric_checks": checks,
        "streams": {
            "Contents/Definition": {"sha256": digest(definition), "bytes": len(definition), "map_next_index": model_map, "exact": True, "tail_bytes": 0},
            "Header2": {"sha256": digest(header_data), "bytes": len(header_data), "map_next_index": header_map, "exact": True, "tail_bytes": 0},
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check the typed archive fields of disclosed, hash-locked drawing sources")
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--source-lock", type=Path, default=SOURCE_LOCK)
    args = parser.parse_args(argv)
    lock_bytes = args.source_lock.read_bytes()
    lock = json.loads(lock_bytes)
    require(lock["schema"] == "kit.sw2026.drawing-source-lock.v1" and lock["passed"] and lock["heldout_results_sealed"] and lock["control_results"] == [True, True], "the native drawing source lock did not qualify")
    cases = [case for case in lock["cases"] if case["split"] == "discovery"]
    require(tuple(case["name"] for case in cases) == DISCLOSED and all(case["passed"] for case in cases), "unexpected disclosed drawing source members")
    registry_value = registry()
    reports = [check_case(registry_value, args.corpus, case) for case in cases]
    print(json.dumps({
        "schema": "kit.sw2026.drawing-definition-check.v1", "source_lock_sha256": digest(lock_bytes),
        "source_revision": lock["source_revision"], "cases": reports,
        "heldout_payloads_or_observations_read": False, "writer_output_count": 0, "native_writer_acceptance": False,
    }, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
