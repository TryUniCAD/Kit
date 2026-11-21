from __future__ import annotations

from base64 import b64decode
import codecs
from hashlib import sha256
import json
from math import isclose
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
TOOLS = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
sys.path.extend((str(TOOLS), str(TOOLS / "serial")))

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit
from Classes import registry
from builders.DrawingFrontBundle import construct_front_bundle
from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt
from interchange.serialization.Deserialize import FromData
from PrepareScaledDrawing import prediction


AUDIT = BuildAudit(TOOLS / "serial/defs")
sys.addaudithook(AUDIT.InspectEvent)


def require(value, message):
    if not value:
        raise ValueError(message)


def request(job):
    drawing = FromData(job["drawing_document"])
    sheet, = drawing.Sheets
    view, = sheet.Views
    child, values = FromData(job["part"]["document"]), job["part"]["settings"]
    sketch, feature = child.sketches[0], child.feature_timeline[0]
    system, provenance, definition = values["system"], values["provenance"], values["definition"]
    authored = {"name": child.metadata["name"], "configuration_name": child.configurations[0].name,
                "sketch_name": sketch.name, "origin_name": system["origin_name"], "plane_axis": "z",
                "extrusion_name": feature.name,
                "vertices_m": [(entity.geometry.start.x * .001, entity.geometry.start.y * .001) for entity in sketch.entities],
                "depth_m": feature.definition.length.value * .001, "density_kg_m3": values["density_kg_m3"]}
    source = {name: provenance[name] for name in ("author", "company", "created_at", "modified_at", "comment", "originating_build_code", "license_origin")}
    presentation = {"plane_names": system["planes"], "units": values["document_units"], "styles": values["styles"],
                    "hatch_name": values["hatch_name"], "drafting_standard": definition["drafting_standard"],
                    "journal_name": definition["journal_name"], "tessellation": definition["tessellation"],
                    "detail_flags": definition["detail_flags"], "system_preference_7a": definition["system_preference_7a"],
                    "design_intent": values["design_intent"], "selected_leader": values["selected_leader"],
                    "cjk_saved": provenance["cjk_saved"], "folder_names": dict(system["folders"]),
                    "folder_order": [row[0] for row in system["folders"]], "cabinet_name": system["cabinet_name"]}
    native, options, drawing_provenance = job["native"], job["native"]["options"], job["native"]["provenance"]
    return {"part": {"document": authored, "provenance": source, "presentation": presentation, "target": values["target"], "output": values["output"]},
            "drawing": {"name": options["name"], "sheet": {"name": sheet.EntityName, "paper_size": "ansi-a-landscape",
                          "scale_numerator": int(sheet.ScaleRatio[0]), "scale_denominator": int(sheet.ScaleRatio[1]),
                          "length_unit": options["units"]["length_unit"], "custom_property_view": options["property_view"]},
                        "sheet_names": options["sheet_names"], "folder_names": options["folder_names"],
                        "provenance": {**{name: drawing_provenance[name] for name in ("author", "company", "created_at", "modified_at", "comment", "originating_build_code", "license_origin")}, "block_identity": options["block_identity"]},
                        "presentation": {"styles": options["styles"], "units": options["units"], "definition": native["ui"],
                                         "auto_dim_text_link": options["auto_dim_text_link"], "language_id": drawing_provenance["language_id"], "cjk_saved": drawing_provenance["cjk_saved"]},
                        "target": options["target"], "output": native["output"]},
            "view": {"name": view.EntityName, "orientation": view.OrientationName,
                     "position": [view.PositionValue.XCoord, view.PositionValue.YCoord], "scale": view.ScaleRatio[0], "supports": job["support_names"]}}


def main():
    job = json.load(sys.stdin)
    built = job["build"]
    rules = registry()
    tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
    AUDIT.BeginBuild()
    mapped = request(job["request"])
    independent = construct_front_bundle(registry=rules, request=mapped)
    payload = build_sldprt(independent.streams)
    actual = SldprtArchive.from_bytes(b64decode(built["artifact_base64"], validate=True)).streams
    require(actual == independent.streams, "SDK linked drawing differs from independent research stream construction: " + repr([name for name in actual if actual[name] != independent.streams.get(name)]))
    require(payload == b64decode(built["artifact_base64"], validate=True), "SDK linked drawing compressed container differs")
    predicted = prediction(mapped)
    expected = predicted["expected"]["view"]
    require(predicted["corner_count"] == 8, "linked corner predictor lost a prism corner")
    require(all(isclose(left, right, rel_tol=1e-10, abs_tol=1e-12) for left, right in zip(built["outline_m"], expected["outline_m"], strict=True)), "linked independent projected corner outline differs")
    rotation, offset = expected["model_to_view"][:9], expected["model_to_view"][9:12]
    scale = expected["scale"]
    effective = 1.0 if abs(scale - 1.0) <= 1e-8 else scale
    matrix = [value for axis in range(3) for value in (*[effective * rotation[index * 3 + axis] for index in range(3)], offset[axis])]
    matrix.extend((0.0, 0.0, 0.0, 1.0))
    require(all(isclose(left, right, rel_tol=1e-10, abs_tol=1e-12) for left, right in zip(built["model_to_sheet"], matrix, strict=True)), "linked independent canonical transform differs")
    require(not AUDIT.DeniedReads, "linked counterpart attempted runtime input access")
    return {"passed": True, "all_logical_streams_identical": True, "container_identical": True,
            "independent_corner_projection": True, "independent_canonical_frame": True, "corner_count": 8,
            "artifact_sha256": sha256(payload).hexdigest(), "definition_map_next_index": independent.definition_map_count,
            "streams": {name: {"bytes": len(data), "sha256": sha256(data).hexdigest()} for name, data in sorted(independent.streams.items())},
            "runtime_input_file_access_attempts": len(AUDIT.DeniedReads), "native_acceptance": False,
            "heldout_inputs_read": 0, "public_writer_enabled": False}


if __name__ == "__main__":
    print(json.dumps(main(), sort_keys=True, allow_nan=False))
