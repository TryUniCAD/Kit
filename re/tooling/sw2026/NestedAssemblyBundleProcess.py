from __future__ import annotations

import codecs
import hashlib
import json
import sys
from base64 import b64encode
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
for directory in (ROOT, ROOT / "src", ROOT / "re/tooling/sw2026", ROOT / "re/tooling/sw2026/serial"):
    sys.path.insert(0, str(directory))

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from AssemblyMates import load_mate_list, store_mate_list
from Classes import registry
from Core import Obj
from Streams import load_rooted, store_rooted
from builders.AssemblyDocument import CONFIG, DEFINITION, MANAGER, MATES, METADATA, MODEL_HEADER, RESOLVED
from builders.AssemblyTargetState import target_update_stamps
from builders.ConfigurationHeader import CONFIGURATION_MANAGER_HEADER
from builders.Definition import definition_stream
from builders.NestedAssembly import construct_nested_bundle
from defs.ConfigPart import load_config, store_config_state
from defs.Definition import load_definition
from defs.ResolvedCore import load_resolved, store_resolved_state
from convert.adapters.solidworks.Assembly.Assembly import DecodeNativeAsm
from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt


REGISTRY = registry()
CODECS = tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
SOURCE_LOCK_SHA = "01d38c3a89af115cf41134701888fb987513e86506f6559401ee323d9bcdc202"


def require(value, message):
    if not value:
        raise ValueError(message)


def inspect_document(document):
    blob = build_sldprt(document.streams)
    archive = SldprtArchive.from_bytes(blob)
    config, config_ar = load_config(archive.require(CONFIG), REGISTRY, 19000, archive=archive, name=CONFIG)
    restored, stored = store_config_state(config, REGISTRY, 19000)
    resolved, resolved_ar = load_resolved(archive.require(RESOLVED), REGISTRY, 19000, archive=archive, name=RESOLVED, seed=config_ar.map_state())
    replay, replay_map = store_resolved_state(resolved, REGISTRY, 19000, seed=stored)
    require(not config.tail and not resolved.tail and restored == archive.require(CONFIG) and replay == archive.require(RESOLVED) and
            stored.count == config_ar.count == document.configuration_map_count, "generated configuration/resolved linked round trip failed")
    parsed = {}
    for stream in (*METADATA, MANAGER, CONFIGURATION_MANAGER_HEADER):
        data = archive.require(stream)
        decoded, _ = load_rooted(data, REGISTRY, 1, 19000)
        require(not decoded.tail and store_rooted(decoded, REGISTRY, 19000) == data, "generated rooted stream round trip failed")
        parsed[stream] = decoded
    model, = config.roots
    headers = (config.head["model_header"], parsed["Header2"].roots[0])
    manager = parsed[MANAGER].roots[0]
    header = parsed[CONFIGURATION_MANAGER_HEADER].roots[0]
    geometry, transform = target_update_stamps(document.model)
    require(header["f08"]["items"][0]["o"]["f50"] & 0xFFFFFFFF == geometry and
            header["f08"]["items"][0]["o"]["f4c"] & 0xFFFFFFFF == transform and
            all(node["fc4"] == document.expanded_count for node in headers), "generated target header count or stamps differ")
    result = {"bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(), "blob": b64encode(blob).decode("ascii"),
              "streams": {name: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()} for name, data in sorted(document.streams.items())},
              "model_class": model.cls, "model_name": model["f18"]["f08"], "configuration": manager["f360"]["f18"]["f08"],
              "path": document.model_header["f38"]["shared"]["h18"]["f08"], "target_geometry_stamp": geometry, "target_transform_stamp": transform,
              "configuration_map_count": config_ar.count, "resolved_map_count": resolved_ar.count, "roundtrips": 2 + len(parsed),
              "expanded_occurrences": document.expanded_count}
    if document.model.cls == "moPart_c":
        return result
    native_mates, _ = load_mate_list(archive.require(MATES), REGISTRY, 19000, resolved_map=resolved_ar.map_state())
    require(not native_mates and store_mate_list(native_mates, REGISTRY, 19000, resolved_map=replay_map) == archive.require(MATES), "generated empty mates round trip failed")
    definition, _ = load_definition(archive.require(DEFINITION), REGISTRY, 19000)
    require(not definition.tail and definition_stream(registry=REGISTRY, document=definition.head) == archive.require(DEFINITION), "generated assembly Definition round trip failed")
    refs = tuple(row["o"] for row in model["f68"]["list"]["items"])
    directory = tuple(row["o"] for row in headers[0]["f30"]["items"])
    require(len(refs) == model["f1560"] == len(document.references) and manager["f360"]["f4b0"] == document.expanded_count,
            "direct and expanded generated counts disagree with their owners")
    loaded = DecodeNativeAsm(archive)
    names = {entry.definition_id for entry in loaded.occurrence_paths}
    require(len(loaded.occurrence_paths) == document.expanded_count and len(loaded.definitions) == len(names) + 1 and
            len(loaded.files) == len(loaded.definitions), "generated XML closure differs from the expanded hierarchy")
    config_slots = {id(entry[1]): index for index, entry in config_ar.table.items() if entry[0] == "obj"}
    rows = []
    for ref, (generated, target) in zip(refs, document.references, strict=True):
        require(ref["f08"] == generated["f08"] and ref["f3b0"] in directory and ref["f4f8"]["f50"] is ref and
                resolved_ar.table[config_slots[id(ref)]][1] is ref, "generated resolved occurrence loses its direct map ownership")
        stamps = target_update_stamps(target.model)
        require((ref["f3f4"], ref["f3f8"]) == stamps and ref["f3e0"] == target.model_header["f40"] and
                ref["f3e8"] == target.model_header["f48"] and ref["f3c0"] == {"f08": target.configuration["f18"]["f08"], "f10": target.configuration["f08"]},
                "generated occurrence target state differs from its generated dependency")
        rows.append({"name": ref["f18"]["f08"], "feature_id": ref["f08"], "ordinal": ref["f4b4"], "target": target.model["f18"]["f08"],
                     "directory_index": directory.index(ref["f3b0"]), "f360": ref["f360"], "f370": ref["f370"],
                     "stamps": {key: ref[key] for key in ("f3e0", "f3e8", "f3f0", "f3f4", "f3f8")}})
    result.update(roundtrips=result["roundtrips"] + 2, direct_occurrences=len(refs), directory=[{
        "kind": node["shared"]["f20"], "target": node["shared"]["h10"]["f08"], "uses": node["f48"], "index": node["f78"],
        "slot": config_slots[id(node)], "f60": node["f60"], "f70": node["f70"], "configuration": node["refcfg"],
    } for node in directory], occurrences=rows, parent_bounds=[model["f1a18"], model["f1a20"]],
                  cmgr_occurrence_ids=[row["o"]["f10"]["f20"]["f08"]["f08"][0]["o"]["f44"] for row in manager["f360"]["fce8"][1:]],
                  xml={"definitions": len(loaded.definitions), "local_occurrence_rows": len(loaded.occurrences),
                       "expanded_occurrence_paths": len(loaded.occurrence_paths)},
                  resolved_feature_ids=[node["f08"] for node in resolved.roots if isinstance(node, Obj)])
    return result


REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()
BUNDLE = construct_nested_bundle(registry=REGISTRY, request=REQUEST)
DOCUMENTS = {name: inspect_document(document) for name, document in BUNDLE.documents.items()}
print(json.dumps({"schema": "kit.sw2026.generated-nested-assembly-bundle.v1", "source_lock_sha256": SOURCE_LOCK_SHA, "root": BUNDLE.root,
                  "documents": DOCUMENTS, "writer_output_count": len(DOCUMENTS), "heldout_inputs_tested": 0,
                  "input_runtime_file_access_attempts": len(AUDIT.DeniedReads), "native_acceptance": False}, allow_nan=False))
