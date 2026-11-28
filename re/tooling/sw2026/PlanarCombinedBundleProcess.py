from __future__ import annotations

import codecs
import json
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parent))

from CoincidentMateBundleProcess import (
    AUDIT, CONFIG, DOCUMENT_VERSION_2026, MANAGER, MATES, MODEL_HEADER, PLANAR_MATE_CLASSES, RESOLVED,
    SldprtArchive, artifact, check_distance, checked_root, read_state, registry, require, select_endpoints,
)
from PlanarMateWrapperProcess import inspect_detached, inspect_wrapper
from AssemblyMates import load_mate_list, store_mate_list
from builders.AssemblyDocument import DEFINITION, construct_assembly_bundle
from builders.Metadata import boolean, fields
from defs.ConfigPart import store_config_state
from defs.ResolvedCore import store_resolved_state
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Container.Container import build_sldprt


def read_list(archive, rules, inherited):
    data = archive.require(MATES)
    with rules.track_usage("load", MATES, sources=archive.streams) as loaded:
        mates, reader = load_mate_list(data, rules, DOCUMENT_VERSION_2026, resolved_map=inherited)
    with rules.track_usage("store", MATES) as stored:
        require(store_mate_list(mates, rules, DOCUMENT_VERSION_2026, resolved_map=inherited) == data,
                "the generated combined mate graph must exactly re-encode")
    for usage in (loaded.snapshot(), stored.snapshot()):
        require(usage["completed"] and not usage["provisional_schemas"] and not usage["missing_schemas"],
                "the combined mate list used an unqualified serializer")
    return mates, reader.count


def expected_log(mate, timestamp):
    return (mate["f08"], mate["f18"]["f08"], timestamp)


def stored_mate_logs(header, mates):
    ids = {mate["f08"] for mate in mates}
    result = []
    for row in header["f20"]["items"]:
        record = row["o"]
        if record["f48"] not in ids:
            continue
        stamp, = (item["o"] for item in record["items"])
        result.append((record["f48"], record["f50"], stamp["f18"]))
    return result


def inspect_mate(*, request, mate, index, bundle, model, headers, configuration, occurrences, assembly):
    require(mate.cls == PLANAR_MATE_CLASSES[request["kind"]] and mate["f18"]["f08"] == request["name"]
            and mate["f3b4"] == 1 and mate["f3b8"] == 0, "a typed mate lost its exact authored order or solve state")
    model_header = headers[-1]
    timestamp = request.get("created_at", assembly["provenance"]["modified_at"])
    filetime = ((mate["f2a4"] & 0xFFFFFFFF) << 32) | (mate["f2a0"] & 0xFFFFFFFF)
    require(filetime == (timestamp + 11644473600) * 10_000_000, "a native mate lost its own creation time")
    attached = select_endpoints(bundle=bundle, owner=model, selectors=request["endpoints"])
    row = {"mate_id": mate["f08"], "mate_name": mate["f18"]["f08"], "class": mate.cls, "wrappers": []}
    for ordinal, ((occurrence, endpoint), resolved, detached) in enumerate(zip(attached, mate["f410"], mate["f3c8"], strict=True)):
        require(detached["k"] == ordinal, "the detached list lost its per-mate ordinal")
        row["wrappers"].append({
            "resolved": inspect_wrapper(wrapper=resolved["o"], owner=model, occurrence=occurrence,
                                        endpoint=endpoint, selection=(mate["f08"], 2 * index + ordinal, ordinal)),
            "detached": inspect_detached(wrapper=detached["o"], owner=model, endpoint=endpoint,
                                         model_header=model_header, configuration=configuration),
        })
    if request["kind"] == "distance":
        row["distance"] = check_distance(mate=mate, spec=request, presentation=assembly["presentation"],
                                          occurrences=occurrences, headers=headers)
    return row, expected_log(mate, timestamp)


def inspect_bundle(bundle, bytes_value, requests, rules):
    archive = SldprtArchive.from_bytes(bytes_value)
    config, resolved, inherited = read_state(bundle, rules)
    model, actual_header = config.roots[0], config.head["model_header"]
    headers = checked_root(archive, rules, "Header2"), actual_header
    checked_root(archive, rules, MODEL_HEADER)
    manager = checked_root(archive, rules, MANAGER)
    configuration = manager["f360"]
    group, = (node for node in resolved.roots if node.cls == "moMateGroup_c")
    require(not group["f60"]["list"]["items"] and not group["f4e8"] and not group["discarded_manager_records"],
            "resolved features must leave mate publication to the linked mate list")
    mates, final = read_list(archive, rules, inherited)
    authored = requests["mates"]
    occurrences = [row["o"] for row in model["f68"]["list"]["items"]]
    require(len(mates) == len(authored) and len({node["f08"] for node in mates}) == len(mates),
            "the typed mate count or persistent IDs differ")
    require(model["fd48"] == model["fd48#wire"] == 2 * len(mates) and configuration["f85c"] == mates[-1]["f08"]
            and configuration["f4b0"] == len(occurrences) and configuration["f860"] == actual_header["f40"],
            "combined mate counters do not reflect registration and actual occurrences")
    require([index for index, row in enumerate(occurrences) if row["f408"]] == [authored[0]["fixed_occurrence"]]
            and all(row["f400"] == 3 for row in occurrences), "the combined constraints lost the cold solve state or one fixed anchor")
    inspected = [
        inspect_mate(request=request, mate=mate, index=index, bundle=bundle, model=model,
                     headers=headers, configuration=configuration, occurrences=occurrences, assembly=requests["assembly"])
        for index, (request, mate) in enumerate(zip(authored, mates, strict=True))
    ]
    logs = [log for _, log in inspected]
    for header in headers:
        require(stored_mate_logs(header, mates) == logs and header["f08"] == mates[-1]["f08"] + 1
                and header["fc4"] == len(occurrences), "header mate logs or allocator progress differ")
    config_bytes, seed = store_config_state(config, rules, DOCUMENT_VERSION_2026)
    resolved_bytes, checked = store_resolved_state(resolved, rules, DOCUMENT_VERSION_2026, seed=seed)
    require(config_bytes == archive.require(CONFIG) and resolved_bytes == archive.require(RESOLVED)
            and checked.count == inherited.count, "combined mate registrations changed linked map readback")
    definition = archive.require(DEFINITION)
    require(WriteModelDef(ReadModelDef(definition, DOCUMENT_VERSION_2026).GraphValue).OutputValue == definition,
            "the assembly's document settings did not re-encode")
    return {"group_id": group["f08"], "occurrence_count": len(occurrences), "mate_count": len(mates),
            "next_wrapper_id": model["fd48"], "next_persistent_id": actual_header["f08"],
            "config_map_next_index": seed.count, "resolved_map_next_index": inherited.count, "mate_map_next_index": final,
            "length": len(archive.require(MATES)), "mate_logs": logs, "mates": [row for row, _ in inspected],
            "logical_round_trips": [CONFIG, RESOLVED, MATES, "Header2", MODEL_HEADER, MANAGER, DEFINITION]}


def generate(request):
    payload = fields(request, "combined mate bundle", ("bundle",), ("include_xml_metadata",))
    metadata = boolean(payload.get("include_xml_metadata", False), "assembly XML metadata")
    require(len(payload["bundle"].get("mates", ())) >= 2, "the combined process requires multiple explicit mates")
    tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
    rules = registry()
    AUDIT.BeginBuild()
    bundle = construct_assembly_bundle(registry=rules, request=payload["bundle"], include_xml_metadata=metadata)
    assembly, child = (build_sldprt(item.streams) for item in (bundle.assembly, bundle.child))
    return {"schema": "kit.sw2026.generated-combined-planar-mates.v1", "native_acceptance": False,
            "heldout_inputs_tested": 0, "writer_output_count": 2,
            "inspection": inspect_bundle(bundle, assembly, payload["bundle"], rules),
            "assembly": artifact(assembly, bundle.assembly.streams), "child": artifact(child, bundle.child.streams),
            "input_runtime_file_access_attempts": len(AUDIT.DeniedReads)}


if __name__ == "__main__":
    print(json.dumps(generate(json.load(sys.stdin)), sort_keys=True, allow_nan=False))
