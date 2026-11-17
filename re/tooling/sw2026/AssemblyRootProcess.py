from __future__ import annotations

import codecs
import hashlib
import json
import sys
from base64 import b64encode
from pathlib import Path

ROOT = Path(sys.argv[1])
for directory in (ROOT, ROOT / "src", ROOT / "re/tooling/sw2026", ROOT / "re/tooling/sw2026/serial"):
    sys.path.insert(0, str(directory))

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from Classes import registry
from ExternalFileView import read_self_reference, self_reference_fields, self_reference_summary
from Streams import load_rooted, store_rooted
from builders.AssemblyDocument import CONFIG, DEFINITION, MANAGER, MATES, METADATA, MODEL_HEADER, RESOLVED, construct_assembly_bundle, construct_empty_assembly
from builders.Definition import definition_stream
from defs.ConfigPart import load_config, store_config_state
from defs.Definition import load_definition
from defs.ResolvedCore import load_resolved, store_resolved_state
from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt

REGISTRY = registry()
CODECS = tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))


def _inspect_occurrences(*, model, model_header, top_header, configuration, read):
    directory = tuple(item["o"] for item in model_header["f30"]["items"])
    references = tuple(item["o"] for item in model["f68"]["list"]["items"])
    rows = tuple(item["o"] for item in configuration["fce8"])
    return {
        "header_component_totals": [top_header["fc4"], model_header["fc4"]],
        "configuration_component_total": configuration["f4b0"],
        "directory": [self_reference_fields(node) for node in directory],
        "directory_headers_agree": [self_reference_fields(row["o"]) for row in top_header["f30"]["items"]] == [self_reference_fields(node) for node in directory],
        "directory_slots": [index for index, entry in read.table.items() if entry[0] == "obj" and entry[1] in directory],
        "bounds": [model["f1a18"], model["f1a20"]],
        "occurrences": [{
            "id": ref["f08"], "name": ref["f18"]["f08"], "ordinal": ref["f4b4"],
            "child_configuration": ref["f3c0"], "transform": ref["f360"], "local_bounds": ref["f370"],
            "directory_index": directory.index(ref["f3b0"]), "has_backlink": ref["f4f8"]["f50"] is ref,
            "update_stamps": {key: ref[key] for key in ("f3e0", "f3e8", "f3f0", "f3f4", "f3f8")},
        } for ref in references],
        "configuration_self_first": bool(rows) and rows[0]["f10"] is None,
        "occurrence_configurations": [_inspect_occurrence_configuration(row) for row in rows[1:]],
    }


def _inspect_occurrence_configuration(row):
    component = row["f10"]
    path = component["f20"]
    target = path["f08"]["f08"][0]["o"]
    owner_file = component["f40"]
    return {
        "feature_id": target["f44"], "name": target["f38"]["f08"], "child_configuration": row["f28"],
        "has_backlink": target["f50"] is not None, "has_serialized_owner": component["owner"] is not None,
        "parent_identity_shared": all(target["f10"][key] is owner_file["shared"][key] for key in ("h10", "h18")),
        "owner_file": self_reference_fields(owner_file),
        "chain_count": path["f08"]["n"], "chain_mode": path["f24"], "chain_stamp": component["f30"],
    }


def inspect_root(assembly):
    streams = assembly.streams
    config, manager_bytes, resolved, definition = (streams[key] for key in (CONFIG, MANAGER, RESOLVED, DEFINITION))
    blob = build_sldprt(streams)
    archive = SldprtArchive.from_bytes(blob)
    decoded, read = load_config(archive.require(CONFIG), REGISTRY, 19000, archive=archive, name=CONFIG)
    restored, replay = store_config_state(decoded, REGISTRY, 19000)
    model = decoded.roots[0]
    decoded_mgr, _ = load_rooted(archive.require(MANAGER), REGISTRY, 1, 19000)
    restored_mgr = store_rooted(decoded_mgr, REGISTRY, 19000)
    resolved_doc, resolved_ar = load_resolved(archive.require(RESOLVED), REGISTRY, 19000, archive=archive, name=RESOLVED, seed=read.map_state())
    restored_res, resolved_replay = store_resolved_state(resolved_doc, REGISTRY, 19000, seed=read.map_state())
    raw_mates = archive.require(MATES)
    decoded_definition, _ = load_definition(archive.require(DEFINITION), REGISTRY, 19000)
    ui_doc = decoded_definition.head
    restored_definition = definition_stream(registry=REGISTRY, document=ui_doc)
    metadata = {}
    top_header = None
    for name in METADATA:
        data = archive.require(name)
        document, _ = load_rooted(data, REGISTRY, 1, 19000)
        metadata[name] = not document.tail and store_rooted(document, REGISTRY, 19000) == data
        if name in ("Header2", MODEL_HEADER):
            metadata[name] = metadata[name] and document.roots[0]["fec"] == int(name == MODEL_HEADER)
        if name == "Header2":
            top_header = document.roots[0]
    configuration = decoded_mgr.roots[0]["f360"]
    result = {
        "model_class": model.cls, "name": model["f18"]["f08"],
        "root_bytes": len(config), "root_sha256": hashlib.sha256(config).hexdigest(),
        "reconstructed_bytes_identical": config == restored and not decoded.tail,
        "maps_consistent": assembly.config_map_count == read.count == replay.count,
        "component_model_binding": model["f990"]["owner"] is model,
        "unit_class": model["f9b8"].cls, "relation_class": model["f9d0"].cls,
        "analysis_units_missing": model["f9c0"] is None,
        "manager_bytes_identical": manager_bytes == restored_mgr and not decoded_mgr.tail,
        "configuration_class": configuration.cls,
        "configuration_name": configuration["f18"]["f08"],
        "resolved_types": [node.cls for node in resolved_doc.roots],
        "live_section_flag": next(node["f378"] for node in resolved_doc.roots if node.cls == "moLiveSectionFolder_c"),
        "resolved_bytes_identical": resolved == restored_res and not resolved_doc.tail,
        "empty_mates_linked": len(raw_mates) == 6 and int.from_bytes(raw_mates[4:], "little") == 0 and int.from_bytes(raw_mates[:4], "little", signed=True) == assembly.resolved_map_count == resolved_ar.count == resolved_replay.count,
        "definition_class": ui_doc.cls, "definition_journal": ui_doc["ffd8"]["f18"]["f08"],
        "definition_bytes_identity": restored_definition == definition and not decoded_definition.tail,
        "save_as_part_fraction": ui_doc["f1b48"]["f10"],
        "component_total": model["f1560"],
        "stream_count": len(archive.streams),
        "stream_hashes": {name: hashlib.sha256(archive.require(name)).hexdigest() for name in sorted(archive.streams)},
        "metadata_roundtrips": metadata,
        **self_reference_summary(decoded.head["model_header"], top_header, read),
        "blob": b64encode(blob).decode("ascii"),
        "model_code_reads": AUDIT.ModuleReads, "denied_reads": AUDIT.DeniedReads,
        "complete_assembly_emitted": False, "native_acceptance": False,
    }
    if model["f1560"]:
        result.update(_inspect_occurrences(model=model, model_header=decoded.head["model_header"], top_header=top_header, configuration=configuration, read=read))
    return result


def inspect_bundle(request):
    bundle = construct_assembly_bundle(registry=REGISTRY, request=request)
    result = inspect_root(bundle.assembly)
    child = build_sldprt(bundle.child.streams)
    child_summary = read_self_reference(SldprtArchive.from_bytes(child), REGISTRY)
    result.update(child={
        "blob": b64encode(child).decode("ascii"), "sha256": hashlib.sha256(child).hexdigest(),
        **child_summary,
    })
    return result


REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()
RESULT = inspect_bundle(REQUEST) if "occurrences" in REQUEST else inspect_root(construct_empty_assembly(registry=REGISTRY, request=REQUEST))
print(json.dumps(RESULT, allow_nan=False))
