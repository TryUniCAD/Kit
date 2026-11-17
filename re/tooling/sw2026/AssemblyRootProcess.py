from __future__ import annotations

import codecs
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
for directory in (ROOT, ROOT / "src", ROOT / "re/tooling/sw2026", ROOT / "re/tooling/sw2026/serial"):
    sys.path.insert(0, str(directory))

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from Classes import registry
from Streams import StreamDoc, load_rooted, store_rooted
from builders.Assembly import initial_assembly_features, initial_assembly_model, initial_configuration, store_empty_mates
from builders.Definition import assembly_definition, definition_stream
from builders.Metadata import header
from builders.Model import PersistentIds, configuration_manager
from builders.Styles import detail_definitions
from builders.Units import unit_table_profile
from defs.ConfigPart import load_config, store_config_state
from defs.Definition import load_definition
from defs.ResolvedCore import load_resolved, store_resolved_state
from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt

REGISTRY = registry()
CODECS = tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
CONFIG = "Contents/Config-0"
HEADER = CONFIG + "-ModelHeader"
RESOLVED = CONFIG + "-ResolvedFeatures"
MATES = CONFIG + "-MatesList"
MANAGER = "Contents/CMgr"
DEFINITION = "Contents/Definition"


def inspect_root(request):
    name, presentation, provenance = (request[key] for key in ("name", "presentation", "provenance"))
    ids = PersistentIds()
    root = initial_assembly_model(name=name, allocator=ids, detail_definitions=detail_definitions(**presentation["styles"]), document_units=unit_table_profile(**presentation["units"]))
    created, modified = (provenance[key] for key in ("created_at", "modified_at"))
    target = request["target"]
    manager = configuration_manager(owner=root, names=[request["configuration_name"]], updated_at=modified, configuration_builder=initial_configuration, **target)
    features = initial_assembly_features(owner=root, allocator=ids, created_at=created, origin_name=request["origin_name"], mate_group_name=request["mate_group_name"], **presentation["assembly_features"], **target)
    rev = {"object_id": root["f08"], "name": name, "stamps": [{"status": 0, "user_index": 0, "company_index": 0, "timestamp": created, "comment": provenance["comment"]}]}
    history = header(next_id=ids.next_id, user_names=[provenance["author"]], company_names=[provenance["company"]], revision_logs=[rev], created_at=created, modified_at=modified, updated_at=modified, model_present=True, component_count=0, update_stamp=101, body_stamp=101, license_flags=0, license_type=0)
    config, state = store_config_state(StreamDoc(CONFIG, {"direct": 0}, [root]), REGISTRY, 19000)
    report_header = store_rooted(StreamDoc("rooted", {"base": 1}, [history]), REGISTRY, 19000)
    manager_bytes = store_rooted(StreamDoc("rooted", {"base": 1}, [manager]), REGISTRY, 19000)
    context = {"model_compressed_stream": 1, "model_is_part": 0, "cmgr_f658": manager["f658"]}
    feature_doc = StreamDoc("resolved", {"base": state.count, "context": context}, features)
    resolved, final_map = store_resolved_state(feature_doc, REGISTRY, 19000, seed=state)
    mates = store_empty_mates(registry=REGISTRY, resolved_map=final_map, mate_group=features[-1])
    document_options = dict(presentation["definition"])
    document_options["tessellation"] = tuple(document_options["tessellation"])
    definition = definition_stream(registry=REGISTRY, document=assembly_definition(**document_options))
    archive = SldprtArchive.from_bytes(build_sldprt({CONFIG: config, HEADER: report_header, MANAGER: manager_bytes, RESOLVED: resolved, MATES: mates, DEFINITION: definition}))
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
    return {
        "model_class": model.cls, "name": model["f18"]["f08"],
        "root_bytes": len(config), "root_sha256": hashlib.sha256(config).hexdigest(),
        "reconstructed_bytes_identical": config == restored and not decoded.tail,
        "maps_consistent": state.count == read.count == replay.count,
        "component_model_binding": model["f990"]["owner"] is model,
        "unit_class": model["f9b8"].cls, "relation_class": model["f9d0"].cls,
        "analysis_units_missing": model["f9c0"] is None,
        "manager_bytes_identical": manager_bytes == restored_mgr and not decoded_mgr.tail,
        "configuration_class": decoded_mgr.roots[0]["f360"].cls,
        "configuration_name": decoded_mgr.roots[0]["f360"]["f18"]["f08"],
        "resolved_types": [node.cls for node in resolved_doc.roots],
        "live_section_flag": next(node["f378"] for node in resolved_doc.roots if node.cls == "moLiveSectionFolder_c"),
        "resolved_bytes_identical": resolved == restored_res and not resolved_doc.tail,
        "empty_mates_linked": len(raw_mates) == 6 and int.from_bytes(raw_mates[4:], "little") == 0 and int.from_bytes(raw_mates[:4], "little", signed=True) == final_map.count == resolved_ar.count == resolved_replay.count,
        "definition_class": ui_doc.cls, "definition_journal": ui_doc["ffd8"]["f18"]["f08"],
        "definition_bytes_identity": restored_definition == definition and not decoded_definition.tail,
        "save_as_part_fraction": ui_doc["f1b48"]["f10"],
        "component_total": model["f1560"],
        "stream_count": len(archive.streams),
        "model_code_reads": AUDIT.ModuleReads, "denied_reads": AUDIT.DeniedReads,
        "complete_assembly_emitted": False, "native_acceptance": False,
    }


REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()
print(json.dumps(inspect_root(REQUEST), allow_nan=False))
