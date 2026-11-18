from __future__ import annotations

from base64 import b64decode
from codecs import lookup
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(sys.argv[1])
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/tooling/sw2026"), str(ROOT / "re/tooling/sw2026/serial")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from Classes import registry
from Core import Obj
from builders.Part import construct_part
from defs.ConfigPart import direct_list_items
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from interchange.serialization.Deserialize import FromData

REGISTRY = registry()
CODECS = tuple(lookup(value) for value in ("utf-16-le", "utf-8", "latin-1"))
REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    built, inputs = REQUEST["build"], REQUEST["request"]
    document = FromData(inputs["document"])
    values = inputs["settings"]
    system, provenance, definition = values["system"], values["provenance"], values["definition"]
    require(document.units == "mm" and len(document.sketches) == len(document.feature_timeline) == 1,
            "independent mathematical counterpart requires its explicitly modeled millimetre rectangle")
    sketch, feature = document.sketches[0], document.feature_timeline[0]
    vertices = tuple((entity.geometry.start.x * 0.001, entity.geometry.start.y * 0.001) for entity in sketch.entities)
    authored = {"name": document.metadata["name"], "configuration_name": document.configurations[0].name,
                "sketch_name": sketch.name, "origin_name": system["origin_name"], "plane_axis": "z",
                "extrusion_name": feature.name, "vertices_m": vertices,
                "depth_m": feature.definition.length.value * 0.001, "density_kg_m3": values["density_kg_m3"]}
    authored["rectangle_dimensions"] = inputs["rectangle_dimensions"]
    source = {name: provenance[name] for name in ("author", "company", "created_at", "modified_at", "comment", "originating_build_code", "license_origin")}
    presentation = {"plane_names": system["planes"], "units": values["document_units"], "styles": values["styles"],
                    "hatch_name": values["hatch_name"], "drafting_standard": definition["drafting_standard"],
                    "journal_name": definition["journal_name"], "tessellation": definition["tessellation"],
                    "detail_flags": definition["detail_flags"], "system_preference_7a": definition["system_preference_7a"],
                    "design_intent": values["design_intent"], "selected_leader": values["selected_leader"],
                    "cjk_saved": provenance["cjk_saved"], "folder_names": dict(system["folders"]),
                    "folder_order": [row[0] for row in system["folders"]], "cabinet_name": system["cabinet_name"]}
    candidate = construct_part(registry=REGISTRY, document=authored, provenance=source, presentation=presentation,
                               target=values["target"], output=values["output"], rectangle_anchor="corner")
    require(candidate.model["f9d8"] is candidate.model["fa48"] is candidate.model["fa50"] is None,
            "mathematical reference no longer selects the documented inactive-list route")
    for field in ("f9d8", "fa48", "fa50"):
        candidate.model[field] = Obj("suObList", {"n": 0, "items": []})
    config_bytes, config = WriteConfigMut(candidate.model, 19000, candidate.model_header, ReadItems=direct_list_items)
    manager = ReadCmgrMut(candidate.streams["Contents/CMgr"], 19000)
    context = {"model_compressed_stream": 1, "model_is_part": 1, "cmgr_f658": manager.RootValue.FieldsValue["f658"]}
    resolved, resolved_graph = WriteResolMut(candidate.features, None, 19000, config.MapValue, context)
    actual = dict(candidate.streams)
    actual["Contents/Config-0"], actual["Contents/Config-0-ResolvedFeatures"] = config_bytes, resolved
    require(actual.keys() == built["streams"].keys(), "mathematical counterpart stream set differs")
    comparisons = {stream: {"bytes": len(data), "sha256": sha256(data).hexdigest(),
                            "same_as_independent_research": data == b64decode(built["streams"][stream]["data"], validate=True)}
                   for stream, data in actual.items()}
    require(all(row["same_as_independent_research"] for row in comparisons.values()), "complete SDK candidate differs from independent neutral mathematical construction")
    require(candidate.next_id == built["next_id"] and config.MapValue.CounterValue == built["config_map_counter"] and
            resolved_graph.MapValue.CounterValue == built["resolved_map_counter"], "independent allocation and map counters differ")
    return {"passed": True, "scope": "independent neutral corner anchored rectangle counterpart without saved CAD input",
            "streams": comparisons, "feature_count": len(candidate.features), "next_id": candidate.next_id,
            "explicit_active_list_initialization": ["f9d8", "fa48", "fa50"],
            "config_map_counter": config.MapValue.CounterValue, "resolved_map_counter": resolved_graph.MapValue.CounterValue,
            "runtime_input_file_reads": len(AUDIT.DeniedReads), "native_acceptance": False, "public_writer_qualified": False}


print(json.dumps(main(), sort_keys=True, allow_nan=False))
