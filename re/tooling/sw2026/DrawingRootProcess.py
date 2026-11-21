from __future__ import annotations

import codecs
import hashlib
import json
import sys
from base64 import b64encode
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
for path in (ROOT, ROOT / "src", ROOT / "re/tooling/sw2026", ROOT / "re/tooling/sw2026/serial"):
    sys.path.insert(0, str(path))

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from Classes import registry
from Core import Load
from builders.DrawingDocument import construct_blank_drawing
from defs.Definition import load_definition
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt
from convert.adapters.solidworks.Drawing.Definition.Projection import JoinConcept
from convert.adapters.solidworks.Drawing.Definition import ReadConcept
from convert.adapters.solidworks.Drawing.ReadDrawing import ReadDrawing


def digest(data):
    return hashlib.sha256(data).hexdigest()


def nodes(owner):
    return [row["o"] for row in owner["f60"]["list"]["items"]]


def header_identity(header):
    reference = header["f38"]
    identity = reference["shared"]
    return reference["refcfg"], identity["h10"]["f08"], identity["h18"]["f08"], identity["f20"], identity["f28"]


def check_core(blob, construction, rules, request):
    archive = SldprtArchive.from_bytes(blob)
    if archive.streams != construction.streams:
        raise ValueError("generated container changed a logical drawing stream")
    definition, read = load_definition(archive.require("Contents/Definition"), rules, 19000)
    header_reader = Load(archive.require("Header2"), 1, rules, 19000)
    header = header_reader.obj()
    model = definition.head["model"]
    sheet = model["f1430"]
    root_nodes, children = nodes(model), nodes(sheet)
    if read.left() or header_reader.left() or read.count != construction.definition_map_count:
        raise ValueError("generated drawing did not exhaust its definition or header")
    if root_nodes[-1] is not sheet or model["f990"]["owner"] is not model or model["f16a8"]["f18"] is not model:
        raise ValueError("generated drawing lost its model, active sheet or manager owner references")
    if header["f08"] != model["fa8"]["f08"] or header["f08"] != 1 + max(node["f08"] for node in [model, *root_nodes, *children]):
        raise ValueError("drawing headers disagree on the next persistent ID")
    expected_identity = ({"f08": "", "f10": -1}, request["name"], request["output"]["path_name"], 4, request["provenance"]["created_at"])
    if header_identity(header) != expected_identity or header_identity(model["fa8"]) != expected_identity:
        raise ValueError("drawing headers disagree on the authored self-reference identity")
    readback = ReadDrawing(archive, blob, request["name"] + ".SLDDRW", ReadOptions(strict=False))
    layout, = readback.drawing.sheets
    settings = request["sheet"]
    if layout.name != settings["name"] or layout.scale_ratio != (settings["scale_numerator"], settings["scale_denominator"]) or layout.views or readback.drawing.model_refs:
        raise ValueError("drawing SDK inspection differs from the authored unlinked sheet")
    return {
        "definition_next_map_index": read.count, "next_persistent_id": header["f08"], "layout_width_m": layout.width,
        "layout_height_m": layout.height, "layout_scale_ratio": list(layout.scale_ratio),
        "root_child_classes": [node.cls for node in root_nodes], "sheet_child_classes": [node.cls for node in children],
    }


def main():
    request = json.load(sys.stdin)
    tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
    rules = registry()
    AUDIT.BeginBuild()
    construction = construct_blank_drawing(registry=rules, request=request)
    blob = build_sldprt(construction.streams)
    inspection = check_core(blob, construction, rules, request)
    report = {
        "schema": "kit.sw2026.blank-drawing-construction.v1", "native_acceptance": False,
        "input_runtime_file_access_attempts": len(AUDIT.DeniedReads), "native_sha256": digest(blob), "native_bytes": len(blob),
        "streams": {name: {"sha256": digest(data), "bytes": len(data)} for name, data in construction.streams.items()},
        "inspection": inspection, "artifact_base64": b64encode(blob).decode("ascii"),
    }
    print(json.dumps(report, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
