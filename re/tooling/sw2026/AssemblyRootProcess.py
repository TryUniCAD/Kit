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
from Streams import load_rooted, store_rooted
from builders.AssemblyDocument import CONFIG, DEFINITION, MANAGER, MATES, METADATA, MODEL_HEADER, RESOLVED, construct_empty_assembly
from builders.Definition import definition_stream
from defs.ConfigPart import load_config, store_config_state
from defs.Definition import load_definition
from defs.ResolvedCore import load_resolved, store_resolved_state
from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt

REGISTRY = registry()
CODECS = tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))


def self_reference_fields(node):
    if node is None:
        return None
    definition = node["shared"]
    return {
        "class": node.cls,
        "path": definition["h18"]["f08"],
        "name": definition["h10"]["f08"],
        "creation_time": definition["f28"],
        "document_kind": definition["f20"],
        "configuration": node["refcfg"],
        "record": {key: node[key] for key in ("f48", "f4c", "f50", "f54", "f58", "f60", "f70", "f78")},
    }


def inspect_root(request):
    assembly = construct_empty_assembly(registry=REGISTRY, request=request)
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
    top_self = None
    model_self = decoded.head["model_header"]["f38"]
    for name in METADATA:
        data = archive.require(name)
        document, _ = load_rooted(data, REGISTRY, 1, 19000)
        metadata[name] = not document.tail and store_rooted(document, REGISTRY, 19000) == data
        if name in ("Header2", MODEL_HEADER):
            metadata[name] = metadata[name] and document.roots[0]["fec"] == int(name == MODEL_HEADER)
        if name == "Header2":
            top_self = self_reference_fields(document.roots[0]["f38"])
    own_reference = self_reference_fields(model_self)
    direct_slots = [index for index, entry in read.table.items() if entry[0] == "obj" and entry[1] is model_self]
    return {
        "model_class": model.cls, "name": model["f18"]["f08"],
        "root_bytes": len(config), "root_sha256": hashlib.sha256(config).hexdigest(),
        "reconstructed_bytes_identical": config == restored and not decoded.tail,
        "maps_consistent": assembly.config_map_count == read.count == replay.count,
        "component_model_binding": model["f990"]["owner"] is model,
        "unit_class": model["f9b8"].cls, "relation_class": model["f9d0"].cls,
        "analysis_units_missing": model["f9c0"] is None,
        "manager_bytes_identical": manager_bytes == restored_mgr and not decoded_mgr.tail,
        "configuration_class": decoded_mgr.roots[0]["f360"].cls,
        "configuration_name": decoded_mgr.roots[0]["f360"]["f18"]["f08"],
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
        "self_reference": own_reference,
        "self_reference_headers_agree": own_reference == top_self,
        "self_reference_direct_slots": direct_slots,
        "blob": b64encode(blob).decode("ascii"),
        "model_code_reads": AUDIT.ModuleReads, "denied_reads": AUDIT.DeniedReads,
        "complete_assembly_emitted": False, "native_acceptance": False,
    }


REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()
print(json.dumps(inspect_root(REQUEST), allow_nan=False))
