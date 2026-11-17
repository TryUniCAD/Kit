from __future__ import annotations

import argparse
from itertools import product
import json
from math import isclose
from pathlib import Path

from CheckDrawingDefinitions import (
    check_header,
    checked_artifacts,
    checked_bytes,
    compare_numeric,
    compare_sheet,
    digest,
    nodes,
    reencode,
    require,
    view_transform,
)
from Classes import registry
from builders.Views import standard_views
from convert import open_document
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Drawing.Identity.DrawingIdentity import CheckDrawLane
from interchange.document import CadDocument


SPEC = Path(__file__).resolve().parents[1] / "DrawingProjectionSpecs01.json"
SPEC_SHA256 = "acb78b422358773320a6601d38bef8e17107f268e8912574d1c23a558584a03c"
ORACLE_SHA256 = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
VIEW_FLAGS = ("f610", "f614", "f618", "f61c", "f1010", "f1020", "f1028", "f102c", "f1030")
RAW_RECT = ("f718", "f720", "f728", "f730")
GEOMETRY_RECT = ("f738", "f740", "f748", "f750")
BORDER_RECT = ("f6d8", "f6e0", "f6e8", "f6f0")


def rotation_matrix(transform):
    if not transform["has_matrix"]:
        return (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    return tuple(transform["f08"][f"m{index}"] for index in range(9))


def native_context_qualified(private):
    phase_rows = [*private["controls"], *(phase for case in private["cases"] for phase in case["phases"])]
    births = {
        (phase["oracle_identity"]["process_id"], phase["oracle_identity"]["process_creation_filetime"])
        for phase in phase_rows
    }
    return (
        len(births) == len(phase_rows) == 10
        and all(phase["oracle_identity"]["sha256"] == ORACLE_SHA256
                and phase["oracle_identity"]["file_version"] == "34.5.2.0604" for phase in phase_rows)
    )


def check_sdk_layout(source, report):
    document = open_document(source, source_format="solidworks.slddrw", strict=False, include_brep=False)
    drawing = document.drawing
    sheet, = drawing.sheets
    view, = sheet.views
    reference, = drawing.model_refs
    require(drawing.active_sheet_id == sheet.id and reference.id == view.model_ref_id, "SDK view ownership differs")
    require(view.orientation_name == report["orientation"] and view.scale_ratio == tuple(report["scale_ratio"]),
            "SDK orientation or scale differs from native")
    compare_numeric("SDK view position", [view.position.x, view.position.y], report["position_m"])
    compare_numeric("SDK view outline", view.outline, report["border_outline"])
    transform = report["model_to_view"]
    bounds = report["model_box"]
    corners = tuple(product(*[(bounds[index + 6], bounds[index + 3]) for index in range(3)]))
    for point in corners:
        expected = [sum(point[j] * transform[index + j * 3] for j in range(3)) * transform[12] + transform[9 + index]
                    for index in range(3)]
        compare_numeric("SDK transformed vertex", view.model_to_sheet.TransformPoint(point), expected)
    center = tuple(report["cached_model_center"])
    compare_numeric("SDK model centre in the sheet", view.model_to_sheet.TransformPoint(center), [*report["position_m"], 0.0])
    restored = CadDocument.from_dict(json.loads(json.dumps(document.to_dict())))
    require(restored.drawing == drawing, "neutral JSON changed the drawing layout")
    return {"point_probes": len(corners) + 1, "neutral_json_round_trip": True}


def audit_case(root, case, spec, rules, canonical, check_sdk):
    source, observed, reopened = checked_artifacts(root, case)
    archive = SldprtArchive.from_bytes(source)
    require(CheckDrawLane(archive) == 19000, "drawing archive version differs")
    definition = archive.require("Contents/Definition")
    header_bytes = archive.require("Header2")
    model, map_count = reencode(definition, rules, archive)
    header, header_map_count = check_header(header_bytes, rules)
    semantic_check_count = compare_sheet(model, header, observed, reopened)
    drawing_view, = [node for node in nodes(model["f1430"]) if node.cls == "moAbsoluteView"]
    view = observed["view"]
    request = spec["view"]
    require(view["orientation"] == request["orientation"] == drawing_view["f1018"], "drawing view orientation differs")
    require(isclose(view["scale"], request["scale"], rel_tol=1e-9), "drawing view scale differs")
    compare_numeric("authored position", view["position_m"], request["position_m"])
    archived_rotation = rotation_matrix(drawing_view["f5e0"])
    canonical_matrix = canonical[view["orientation"]]
    report = {
        "case": case["name"],
        "source_sha256": case["native_sha256"],
        "native_record_sha256": case["record_sha256"],
        "definition": {"bytes": len(definition), "map_next": map_count, "exact": True, "sha256": digest(definition)},
        "header": {"bytes": len(header_bytes), "map_next": header_map_count, "exact": True, "sha256": digest(header_bytes)},
        "native_comparison_checks": semantic_check_count,
        "orientation": view["orientation"],
        "scale_decimal": view["scale"],
        "scale_ratio": [drawing_view["f780"], drawing_view["f788"]],
        "scale_flags": {key: drawing_view[key] for key in VIEW_FLAGS},
        "model_to_view": view_transform(drawing_view),
        "canonical_rotation": canonical_matrix,
        "canonical_rotation_matches": all(isclose(a, b, rel_tol=1e-9, abs_tol=1e-12)
                                          for a, b in zip(archived_rotation, canonical_matrix, strict=True)),
        "position_m": view["position_m"],
        "edited_position_m": reopened["edited"]["view"]["position_m"],
        "sheet_dimensions_m": observed["sheet_properties"][5:7],
        "model_box": [drawing_view["f600"][f"b{index}"] for index in range(10)],
        "cached_model_center": [drawing_view["f648"][axis] for axis in "xyz"],
        "raw_outline": [drawing_view[key] for key in RAW_RECT],
        "geometry_outline": [drawing_view[key] for key in GEOMETRY_RECT],
        "border_outline": [drawing_view[key] for key in BORDER_RECT],
    }
    if check_sdk:
        report["sdk_layout"] = check_sdk_layout(source, report)
    return report


def main():
    parser = argparse.ArgumentParser(description="Correlate disclosed scaled drawing fields with qualified native observations")
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--source-lock-sha256", required=True)
    parser.add_argument("--check-sdk", action="store_true")
    args = parser.parse_args()
    specs = json.loads(checked_bytes(SPEC, SPEC_SHA256))["cases"]
    lock = json.loads(checked_bytes(args.corpus / "SourceLock.json", args.source_lock_sha256))
    require(lock["schema"] == "kit.sw2026.drawing-source-lock.v1" and lock["passed"] and lock["pinned_inputs_immutable"]
            and lock["control_results"] == [True, True] and lock["distinct_processes"] == 10
            and lock["writer_output_count"] == 0 and lock["specs_sha256"] == SPEC_SHA256,
            "drawing source lock is not qualified")
    require(len(lock["cases"]) == len(specs) and all(case["split"] == "discovery" and case["passed"] and case["name"] == spec["name"]
            for case, spec in zip(lock["cases"], specs, strict=True)), "unexpected drawing source cases")
    private = json.loads(checked_bytes(args.corpus / "PrivateInspection.json", lock["private_inspection_sha256"]))
    require(native_context_qualified(private), "drawing source native process identities differ")
    canonical = {row["o"]["f358"]: rotation_matrix(row["o"]["f368"]) for row in standard_views(detail_standard=1)}
    rules = registry()
    reports = [audit_case(args.corpus, case, spec, rules, canonical, args.check_sdk)
               for case, spec in zip(lock["cases"], specs, strict=True)]
    print(json.dumps({
        "schema": "kit.sw2026.drawing-view-projection-observations.v1",
        "source_lock_sha256": args.source_lock_sha256,
        "source_spec_sha256": SPEC_SHA256,
        "cases": reports,
        "heldout_inputs_read": 0,
        "writer_outputs": 0,
        "native_acceptance": False,
    }, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
