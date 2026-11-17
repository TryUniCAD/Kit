from __future__ import annotations

import argparse
import json
import math
import ntpath
from io import BytesIO
from pathlib import Path

from CheckDrawingDefinitions import DISCLOSED, SOURCE_LOCK, checked_artifacts, compare_numeric, digest, require
from convert import available_adapters, open_document, write_document
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from interchange import CadDocument


def check_layout(document, expected):
    drawing = document.drawing
    require(drawing is not None and len(drawing.sheets) == 1, "expected one portable drawing sheet")
    sheet = drawing.sheets[0]
    require(drawing.active_sheet_id == sheet.id and sheet.name == expected["sheet"], "drawing sheet identity differs from the native readback")
    properties = expected["sheet_properties"]
    require(sheet.scale_ratio == tuple(properties[2:4]), "drawing sheet scale differs from the native readback")
    require(math.isclose(sheet.width, properties[5], abs_tol=1e-12) and math.isclose(sheet.height, properties[6], abs_tol=1e-12), "drawing paper size differs from the native readback")
    view = expected["view"]
    if view is None:
        require(not sheet.views and not drawing.model_refs, "empty drawing produced an external model or view")
        return
    require(len(sheet.views) == 1 and len(drawing.model_refs) == 1, "expected one portable drawing view and model")
    stored = sheet.views[0]
    reference = drawing.model_refs[0]
    require(stored.model_ref_id == reference.id and stored.name == view["name"], "native view identity was lost")
    require(stored.configuration_name == view["configuration"], "native model configuration was lost")
    require(ntpath.normcase(ntpath.normpath(reference.source_path)) == ntpath.normcase(ntpath.normpath(view["resolved_reference_path"])), "native external model path differs from the oracle path")
    require((stored.position.x, stored.position.y) == tuple(view["position_m"]), "drawing view position differs from the native readback")
    require(stored.outline == tuple(view["outline_m"]), "drawing view outline differs from the native readback")
    require(stored.orientation_name == view["orientation"], "resolved view orientation differs from the native readback")
    require(stored.scale_ratio is not None and stored.model_to_sheet is not None, "resolved view has no scale or native transform")
    compare_numeric("resolved view scale", [stored.scale_ratio[0] / stored.scale_ratio[1]], [view["scale"]])
    values = view["model_to_view"]
    expected_rows = tuple(
        tuple(values[column * 3 + row] * values[12] for column in range(3)) + (values[9 + row],)
        for row in range(3)
    ) + ((0.0, 0.0, 0.0, 1.0),)
    compare_numeric("resolved model-to-sheet transform", stored.model_to_sheet.Values, [value for row in expected_rows for value in row])


def check_case(root, case):
    native, authored, _ = checked_artifacts(root, case)
    name = case["name"]
    source_path = root / name / "author" / (name + ".SLDDRW")
    try:
        open_document(native)
    except SldprtFormat as error:
        require("strict SOLIDWORKS drawing reading is unavailable" in str(error), "drawing reached the wrong strict reader")
    else:
        raise ValueError("unqualified native drawing passed strict open")
    document = open_document(native, strict=False)
    explicit = open_document(source_path, source_format="solidworks.slddrw", strict=False)
    require(document.drawing == explicit.drawing, "drawing layout differs between path and byte sources")
    require(document.source.format_id == "solidworks.slddrw" and document.source.sha256 == digest(native), "drawing source identity differs")
    require(not document.configurations and not document.bodies, "drawing fabricated design data")
    require(len(document.diagnostics) == 1 and document.diagnostics[0].code == "slddrw.layout_inspection", "drawing inspection omissions were not reported")
    check_layout(document, authored)
    wire = document.to_json(indent=None)
    require(CadDocument.from_json(wire) == document, "drawing JSON lost typed layout fields")
    neutral = BytesIO()
    write_document(document, neutral, destination_format="interchange.json")
    require(open_document(neutral.getvalue()) == document, "public neutral output lost drawing data")
    rejected = BytesIO()
    try:
        write_document(document, rejected, destination_format="freecad.fcstd")
    except ValueError as error:
        require("does not support typed drawings" in str(error) and not rejected.getvalue(), "unsupported CAD output was not rejected before writing")
    else:
        raise ValueError("a part writer accepted drawing data")
    return {
        "name": name,
        "source_sha256": digest(native),
        "neutral_json_sha256": digest(wire.encode("utf-8")),
        "views": 0 if authored["view"] is None else 1,
    }


def main():
    parser = argparse.ArgumentParser(description="Check the SDK layout inspector on the three disclosed drawing cases")
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--source-lock", type=Path, default=SOURCE_LOCK)
    options = parser.parse_args()
    lock_bytes = options.source_lock.read_bytes()
    locked_cases = {case["name"]: case for case in json.loads(lock_bytes)["cases"] if case["name"] in DISCLOSED}
    info = [row for row in available_adapters() if "solidworks.slddrw" in row.aliases]
    require(len(info) == 1 and ".slddrw" in info[0].extensions, "drawing adapter is absent from public discovery")
    result = {
        "schema": "kit.sw2026.drawing-sdk-layout.v2",
        "source_lock_sha256": digest(lock_bytes),
        "definition_view_properties": True,
        "strict_reader_qualified": False,
        "native_writer_qualified": False,
        "cases": [check_case(options.corpus, locked_cases[name]) for name in DISCLOSED],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
