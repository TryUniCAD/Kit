from __future__ import annotations

from base64 import b64encode
import codecs
from hashlib import sha256
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PlanarMateEndpointProcess import AUDIT, read_state, require, select_endpoints
from PlanarMateWrapperProcess import inspect_detached, inspect_wrapper

from AssemblyMates import load_mate_list, store_mate_list
from Classes import registry
from Core import DOCUMENT_VERSION_2026
from Streams import load_rooted, store_rooted
from builders.AssemblyDocument import CONFIG, MANAGER, MATES, MODEL_HEADER, RESOLVED, construct_assembly_bundle
from builders.Metadata import boolean, fields
from defs.ConfigPart import store_config_state
from defs.ResolvedCore import store_resolved_state
from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt


def digest(payload):
    return sha256(payload).hexdigest()


def checked_root(archive, rules, name):
    payload = archive.require(name)
    parsed, _ = load_rooted(payload, rules, 1, DOCUMENT_VERSION_2026)
    require(not parsed.tail and store_rooted(parsed, rules, DOCUMENT_VERSION_2026) == payload,
            f"{name} does not re-encode exactly")
    result, = parsed.roots
    return result


def creation_log(*, header, mate, timestamp):
    require(header["f08"] == mate["f08"] + 1 and header["fc4"] == 2,
            "the header must advance its persistent ID independently of occurrence count")
    log, = (row["o"] for row in header["f20"]["items"] if row["o"]["f48"] == mate["f08"])
    stamp, = (row["o"] for row in log["items"])
    require(log["f50"] == mate["f18"]["f08"] and stamp["f18"] == timestamp,
            "the header must carry the mate's own creation log")
    return {"object_id": log["f48"], "name": log["f50"], "timestamp": stamp["f18"]}


def check_mate(*, assembly_bytes, bundle, request, rules):
    archive = SldprtArchive.from_bytes(assembly_bytes)
    config, resolved, inherited = read_state(bundle, rules)
    model, model_header = config.roots[0], config.head["model_header"]
    namespace = request["bundle"]
    spec, = namespace["mates"]
    top_header = checked_root(archive, rules, "Header2")
    checked_root(archive, rules, MODEL_HEADER)
    manager = checked_root(archive, rules, MANAGER)
    configuration = manager["f360"]
    payload = archive.require(MATES)
    with rules.track_usage("load", MATES, sources=archive.streams) as loaded:
        (mate,), reader = load_mate_list(payload, rules, DOCUMENT_VERSION_2026, resolved_map=inherited)
    with rules.track_usage("store", MATES) as stored:
        require(store_mate_list((mate,), rules, DOCUMENT_VERSION_2026, resolved_map=inherited) == payload,
                "the complete coincident mate did not re-encode exactly")
    for usage in (loaded.snapshot(), stored.snapshot()):
        require(usage["completed"] and not usage["provisional_schemas"] and not usage["missing_schemas"],
                "the mate list exercised an unqualified serializer")
    group, = (node for node in resolved.roots if node.cls == "moMateGroup_c")
    require(not group["f60"]["list"]["items"] and not group["f4e8"] and not group["discarded_manager_records"],
            "the mate must be serialized solely in the separate mate list")
    require(mate.cls == "moMateCoincident" and mate["f18"]["f08"] == spec["name"]
            and mate["f3b4"] == 1 and mate["f3b8"] == 0,
            "the complete mate lost its authored alignment or initial solver state")
    require(model["fd48"] == model["fd48#wire"] == 2 and configuration["f85c"] == mate["f08"]
            and configuration["f4b0"] == 2 and configuration["f860"] == model_header["f40"],
            "the assembly counter, configuration progress or occurrence count differs")
    occurrences = [row["o"] for row in model["f68"]["list"]["items"]]
    require([row["f408"] for row in occurrences] == [int(index == spec["fixed_occurrence"]) for index in range(2)]
            and all(row["f400"] == 3 for row in occurrences), "fixed input and cold solve status must be independent")
    timestamp = spec.get("created_at", namespace["assembly"]["provenance"]["modified_at"])
    logs = [creation_log(header=header, mate=mate, timestamp=timestamp) for header in (top_header, model_header)]
    filetime = ((mate["f2a4"] & 0xFFFFFFFF) << 32) | (mate["f2a0"] & 0xFFFFFFFF)
    require(filetime == (timestamp + 11644473600) * 10_000_000, "mate registration FILETIME differs")
    selections = select_endpoints(bundle=bundle, owner=model, selectors=spec["endpoints"])
    wrappers = []
    for index, ((occurrence, endpoint), attached, detached) in enumerate(zip(selections, mate["f410"], mate["f3c8"], strict=True)):
        require(detached["k"] == index, "the detached list lost its ordered selection key")
        wrappers.append({
            "resolved": inspect_wrapper(wrapper=attached["o"], owner=model, occurrence=occurrence,
                                        endpoint=endpoint, selection=(mate["f08"], index, index)),
            "detached": inspect_detached(wrapper=detached["o"], owner=model, endpoint=endpoint,
                                         model_header=model_header, configuration=configuration),
        })
    config_bytes, seed = store_config_state(config, rules, DOCUMENT_VERSION_2026)
    resolved_bytes, final = store_resolved_state(resolved, rules, DOCUMENT_VERSION_2026, seed=seed)
    require(config_bytes == archive.require(CONFIG) and resolved_bytes == archive.require(RESOLVED)
            and final.count == inherited.count, "the model archive changed its resolved map or bytes")
    return {
        "mate_id": mate["f08"], "mate_name": mate["f18"]["f08"], "group_id": group["f08"],
        "mate_fields": {key: mate[key] for key in ("f0c", "f3b4", "f3b8", "f2a4", "f2a0", "f2b8", "f2bc")},
        "fixed_occurrence": spec["fixed_occurrence"], "configuration_highest_id": configuration["f85c"],
        "creation_logs": logs, "next_wrapper_id": model["fd48"], "config_map_next_index": seed.count,
        "resolved_map_next_index": inherited.count, "mate_map_next_index": reader.count,
        "mate_list_bytes": len(payload), "logical_round_trips": [CONFIG, RESOLVED, MATES, "Header2", MODEL_HEADER, MANAGER],
        "wrappers": wrappers,
    }


def artifact(payload, streams):
    require(SldprtArchive.from_bytes(payload).streams == streams, "physical container changed generated streams")
    return {
        "sha256": digest(payload), "bytes": len(payload), "artifact_base64": b64encode(payload).decode("ascii"),
        "streams": {name: {"bytes": len(data), "sha256": digest(data)} for name, data in sorted(streams.items())},
    }


def main():
    request = fields(json.load(sys.stdin), "coincident mate bundle", ("bundle",), ("include_xml_metadata",))
    metadata = boolean(request.get("include_xml_metadata", False), "assembly XML metadata")
    require(len(request["bundle"].get("mates", ())) == 1, "the guarded process requires one authored mate")
    tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
    rules = registry()
    AUDIT.BeginBuild()
    bundle = construct_assembly_bundle(registry=rules, request=request["bundle"], include_xml_metadata=metadata)
    assembly_bytes, child_bytes = (build_sldprt(item.streams) for item in (bundle.assembly, bundle.child))
    result = {
        "schema": "kit.sw2026.generated-coincident-mate-bundle.v1", "native_acceptance": False,
        "heldout_inputs_tested": 0, "writer_output_count": 2,
        "inspection": check_mate(assembly_bytes=assembly_bytes, bundle=bundle, request=request, rules=rules),
        "assembly": artifact(assembly_bytes, bundle.assembly.streams),
        "child": artifact(child_bytes, bundle.child.streams),
        "input_runtime_file_access_attempts": len(AUDIT.DeniedReads),
    }
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
