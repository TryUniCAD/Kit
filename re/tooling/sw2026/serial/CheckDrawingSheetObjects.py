from __future__ import annotations

import argparse
import json
from pathlib import Path

from CheckDrawingDefinitions import DISCLOSED, SOURCE_LOCK, checked_artifacts, digest, nodes, require
from Classes import registry
from Core import Load, Obj, Store
from defs.Definition import load_definition
from convert.adapters.solidworks.Container.Container import SldprtArchive

from builders.DrawingSheet import DrawingSheet
from builders.DrawingSheetObjects import empty_drawing_sheet, sheet_ui_sketch
from builders.Model import PersistentIds, unit_component


def inspect_sheet(sheet, ui_sketch):
    plane, profile, folder = nodes(sheet)[:3]
    require((plane.cls, profile.cls, folder.cls) == ("moRefPlane_c", "moProfileFeature_c", "moDetailFolder_c"),
            "sheet support nodes are not in native insertion order")
    require(sheet["f408"] is profile and sheet["f390"] is folder, "sheet support pointers lost node aliases")
    support = profile["pd_f78"]
    require(support["ff8"] is plane and support["ff0"] == {"f00": -1, "f08": 2592000} and support["f100"] == 0,
            "sheet plane reference must retain its pre-insertion handle and actual plane alias")
    require(plane["f08"] >= 0 and plane["f6dc"] == 4 and plane["f6f8"].cls == "moAbsoluteRefPlnData_c",
            "sheet plane must use an allocated absolute reference")
    scale = sheet["f3f8"] / sheet["f400"]
    data, sketch = plane["f6f8"], profile["pd_f80"]
    require(data["f20"]["f70"] == profile["pd_ff0"]["f70"] == 1.0 / scale and ui_sketch["f80"]["f70"] == scale,
            "sheet support frames differ from the native scale directions")
    require(ui_sketch["profile_feature_id"] == profile["f08"], "drawing UI sketch refers to a different feature")
    require((data["f54"], data["f58"]) == (1, 2) and tuple(data[f"b{i}"] for i in range(4)) == (0.0809, -0.0809, 0.05, -0.05),
            "sheet plane lacks the native XY axes or empty border defaults")
    require(sketch["f128"] == sketch["f188"] == 0 and folder["has_fd98"] == folder["fde8"] == 0,
            "sheet profile or detail folder has populated state")
    require(not any(value["n"] for value in folder.f.values() if isinstance(value, dict) and "n" in value),
            "drawing detail folder contains unsupported detail items")
    return plane, profile, folder


def inspect_disclosed(*, corpus, case, rules):
    saved, _, _ = checked_artifacts(corpus, case)
    archive = SldprtArchive.from_bytes(saved)
    definition, _ = load_definition(archive.require("Contents/Definition"), rules, 19000)
    model = definition.head["model"]
    sheet = model["f1430"]
    ui = definition.head["fac0"]
    plane, profile, folder = inspect_sheet(sheet, ui)
    component = profile["pd_f78"]["f58"]
    require(component is not model["f990"] and component["owner"] is model, "sheet profile must hold its copied self component")
    return {
        "name": case["name"], "source_sha256": digest(saved),
        "child_classes": [plane.cls, profile.cls, folder.cls],
        "inline_plane_id": profile["pd_f78"]["ff0"]["f00"],
        "model_scale": plane["f6f8"]["f20"]["f70"], "ui_scale": ui["f80"]["f70"],
        "viewport_present": bool(sheet["has_f430"]),
        "node_flags": [node["f28"] for node in (sheet, plane, profile, folder)],
        "plane_feature_stamp": plane["f29c"], "profile_data_stamp": profile["pd_f2a0"],
    }


def inspect_constructed(*, settings, first_id, rules):
    model = Obj("moDrawing_c")
    model["f990"] = unit_component(owner=model)
    allocator = PersistentIds(next_id=first_id)
    names = ("Authored sheet plane", "Editable sheet sketch", "Drawing details")
    sheet = empty_drawing_sheet(settings=settings, owner=model, allocator=allocator, plane_name=names[0],
                                profile_name=names[1], detail_name=names[2], created_at=1453000000,
                                date_code=2026306, parasolid_version=370108)
    ui = sheet_ui_sketch(settings=settings, sheet=sheet)
    writer = Store(1, rules, 19000, {"owner_is_drawing": 1})
    writer.bind_direct_objects((model,))
    writer.obj(sheet)
    writer.obj(ui)
    encoded = bytes(writer.out)
    reader = Load(encoded, 1, rules, 19000, {"owner_is_drawing": 1})
    decoded_model = Obj("moDrawing_c")
    reader.bind_direct_objects((decoded_model,))
    decoded, decoded_ui = reader.obj(), reader.obj()
    require(reader.left() == 0 and reader.count == writer.count, "sheet graphs did not consume their exact archive extent")
    children = inspect_sheet(decoded, decoded_ui)
    require(children[1]["pd_f78"]["f58"]["owner"] is decoded_model, "sheet sketch loses its drawing owner after loading")
    ids = [node["f08"] for node in (decoded, *children)]
    require(ids == list(range(first_id, allocator.next_id)), "sheet feature IDs do not follow their insertion order")
    require([node["f18"]["f08"] for node in (decoded, *children)] == [settings.name, *names], "sheet names changed after loading")
    require(not decoded["has_f430"] and decoded["f368_marker"] == 0xFFFF, "fresh sheet must carry empty viewport and annotation state")
    require(all(decoded[key] == value for key, value in settings.authored_fields().items()), "authored sheet settings changed after loading")
    return {
        "bytes": len(encoded), "sha256": digest(encoded), "map_next_index": reader.count,
        "first_id": first_id, "next_persistent_id": allocator.next_id, "sheet_scale": settings.scale,
        "length_unit": settings.length_unit, "viewport_present": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Check generated empty sheet support objects and disclosed native aliases")
    parser.add_argument("corpus", type=Path)
    args = parser.parse_args()
    lock = SOURCE_LOCK.read_bytes()
    cases = {case["name"]: case for case in json.loads(lock)["cases"] if case["name"] in DISCLOSED}
    settings = [
        DrawingSheet(name="Metric Sheet", paper_size="ansi-a-landscape", scale_numerator=3,
                     scale_denominator=2, length_unit="mm", custom_property_view="Primary"),
        DrawingSheet(name="Inch Sheet Revision", paper_size="ansi-a-landscape", scale_numerator=2,
                     scale_denominator=7, length_unit="in", custom_property_view="Original"),
    ]
    rules = registry()
    result = {
        "schema": "kit.sw2026.drawing-sheet-objects.v1", "source_lock_sha256": digest(lock),
        "disclosed": [inspect_disclosed(corpus=args.corpus, case=cases[name], rules=rules) for name in DISCLOSED],
        "generated_subgraph": [inspect_constructed(settings=value, first_id=id_base, rules=rules)
                               for value, id_base in zip(settings, (11, 40), strict=True)],
        "native_acceptance": False,
    }
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
