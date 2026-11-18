from base64 import b64decode
from codecs import lookup
from hashlib import sha256
import json
from pathlib import Path
import sys
import os

ROOT = Path(sys.argv[1])
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/tooling/sw2026"), str(ROOT / "re/tooling/sw2026/serial")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from Classes import registry
from Core import Obj
import builders.AssemblyDocument as AssemblyDocument
import builders.AssemblyMateEndpoint as MateEndpointBuilder
from builders.ConfigurationHeader import configuration_manager_header, configuration_manager_header_stream
from builders.Part import construct_part
from SdkReferenceFrame import ReferenceFrame
from defs.ConfigPart import direct_list_items
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt
from interchange.serialization.Deserialize import FromData

REGISTRY = registry()
CODECS = tuple(lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()


def require(value, message):
    if not value:
        raise ValueError(message)


def construct_child(inputs):
    document = FromData(inputs["document"])
    values = inputs["settings"]
    system, provenance, definition = values["system"], values["provenance"], values["definition"]
    sketch, feature = document.sketches[0], document.feature_timeline[0]
    vertices = tuple((entity.geometry.start.x * 0.001, entity.geometry.start.y * 0.001) for entity in sketch.entities)
    authored = {"name": document.metadata["name"], "configuration_name": document.configurations[0].name,
                "sketch_name": sketch.name, "origin_name": system["origin_name"], "plane_axis": "z",
                "extrusion_name": feature.name, "vertices_m": vertices,
                "depth_m": feature.definition.length.value * 0.001, "density_kg_m3": values["density_kg_m3"]}
    if "rectangle_dimensions" in inputs:
        authored["rectangle_dimensions"] = inputs["rectangle_dimensions"]
    source = {name: provenance[name] for name in ("author", "company", "created_at", "modified_at", "comment", "originating_build_code", "license_origin")}
    presentation = {"plane_names": system["planes"], "units": values["document_units"], "styles": values["styles"],
                    "hatch_name": values["hatch_name"], "drafting_standard": definition["drafting_standard"], "journal_name": definition["journal_name"],
                    "tessellation": definition["tessellation"], "detail_flags": definition["detail_flags"], "system_preference_7a": definition["system_preference_7a"],
                    "design_intent": values["design_intent"], "selected_leader": values["selected_leader"], "cjk_saved": provenance["cjk_saved"],
                    "folder_names": dict(system["folders"]), "folder_order": [row[0] for row in system["folders"]], "cabinet_name": system["cabinet_name"]}
    result = construct_part(registry=REGISTRY, document=authored, provenance=source, presentation=presentation, target=values["target"], output=values["output"])
    for field in ("f9d8", "fa48", "fa50"):
        result.model[field] = Obj("suObList", {"n": 0, "items": []})
    config_bytes, config = WriteConfigMut(result.model, 19000, result.model_header, ReadItems=direct_list_items)
    resolved_bytes, _ = WriteResolMut(result.features, None, 19000, config.MapValue, {"model_compressed_stream": 1, "model_is_part": 1, "cmgr_f658": 0})
    child_streams = dict(result.streams)
    child_streams.update({"Contents/Config-0": config_bytes, "Contents/Config-0-ResolvedFeatures": resolved_bytes})
    return result, child_streams


def construct_parent(request, child):
    value = request["assembly"]
    system, provenance = value["system"], value["provenance"]
    child_system = request["child"]["settings"]["system"]
    specs = request["mates"] if "mates" in request else (request["mate"],)
    source = {name: provenance[name] for name in ("author", "company", "created_at", "modified_at", "comment", "originating_build_code", "license_origin")}
    presentation = {"styles": value["styles"], "units": value["units"], "definition": value["definition"], "language_id": value["styles"]["language_id"],
                    "cjk_saved": provenance["cjk_saved"], "assembly_features": {"plane_names": system["planes"], "cabinet_name": system["cabinet_name"], "folder_names": dict(system["folders"])}}
    for spec in specs:
        if spec["kind"] == "distance":
            presentation.update(design_intent=spec["design_intent"], selected_leader=spec["selected_leader"])
    authored = {"name": value["name"], "configuration_name": value["configuration_name"], "origin_name": system["origin_name"], "mate_group_name": system["mate_group_name"],
                "provenance": source, "presentation": presentation, "target": value["target"], "output": value["output"]}
    mates = []
    for spec in specs:
        endpoints = ([{"occurrence": row["occurrence"], "datum": child_system["planes"][row["axis"]]} for row in spec["endpoints"]]
                     if "endpoints" in spec else [{"occurrence": index, "datum": child_system["planes"][spec["axis"]]} for index in range(2)])
        fixed = request["fixed_occurrence"] if "endpoints" in spec else spec["fixed_occurrence"]
        mate = {"kind": spec["kind"], "name": spec["name"], "alignment": "aligned", "fixed_occurrence": fixed, "created_at": provenance["created_at"],
                "endpoints": endpoints}
        if spec["kind"] == "distance":
            mate["distance_m"] = spec["distance_m"]
        mates.append(mate)
    occurrences = tuple((row["name"], ReferenceFrame(origin=tuple(row["origin"]), u=tuple(row["u"]), v=tuple(row["v"]))) for row in request["occurrences"])
    original = AssemblyDocument.configuration_manager
    captured = []

    def manager(**values):
        result = original(**values)
        captured.append(result)
        return result

    AssemblyDocument.configuration_manager = manager
    prior_frame = MateEndpointBuilder.PlaneFrame
    MateEndpointBuilder.PlaneFrame = ReferenceFrame
    try:
        result = AssemblyDocument._construct_assembly(registry=REGISTRY, request=authored, child=child, occurrences=occurrences, mate_requests=tuple(mates), include_xml_metadata=True)
    finally:
        AssemblyDocument.configuration_manager = original
        MateEndpointBuilder.PlaneFrame = prior_frame
    manager_header = configuration_manager_header(manager=captured[0], saved_at=value["output"]["saved_at"])
    streams = dict(result.streams)
    streams["Contents/CMgrHdr2"] = configuration_manager_header_stream(registry=REGISTRY, header=manager_header)
    return streams

def main():
    request, built = REQUEST["request"], REQUEST["build"]
    child, child_streams = construct_child(request["child"])
    parent_streams = construct_parent(request, child)
    comparisons = {}
    for kind, streams in (("assembly", parent_streams), ("child", child_streams)):
        require(streams.keys() == built[kind]["streams"].keys(), "independent generated stream roles differ")
        comparisons[kind] = {name: {"bytes": len(data), "sha256": sha256(data).hexdigest(), "byte_identity": data == b64decode(built[kind]["streams"][name]["data"], validate=True)} for name, data in streams.items()}
        if not all(row["byte_identity"] for row in comparisons[kind].values()):
            failed = [name for name, row in comparisons[kind].items() if not row["byte_identity"]]
            raise ValueError("independent " + kind + " generated stream differs: " + repr(failed))
        blob = BuildSldprt([(name, streams[name]) for name in built[kind]["stream_order"]], FormatVersion=4)
        require(sha256(blob).hexdigest() == built[kind]["sha256"], "independent complete generated container differs")
    return {"passed": True, "worker_pid": os.getpid(), "scope": "complete independent mathematical assembly and child composer from authored neutral values",
            "streams": comparisons, "same_as_independent_research": True, "runtime_input_file_reads": len(AUDIT.DeniedReads),
            "native_acceptance": False, "public_writer_qualified": False}


print(json.dumps(main(), sort_keys=True, allow_nan=False))
