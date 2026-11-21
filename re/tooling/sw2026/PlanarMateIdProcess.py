from __future__ import annotations

import codecs
from hashlib import sha256
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PlanarMateEndpointProcess import AUDIT, read_state, require, select_endpoints
from PlanarMateWrapperProcess import encode

from Classes import registry
from Core import DOCUMENT_VERSION_2026, Load
from builders.AssemblyDocument import CONFIG, construct_assembly_bundle
from builders.AssemblyMateEndpoint import register_planar_wrapper_ids, resolved_planar_wrapper
from builders.Metadata import fields, sequence
from builders.Model import PersistentIds, model_feature
from defs.ConfigPart import load_config, store_config_state
from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt


def registered_mate(*, name, group, endpoints, allocator, target):
    mate = model_feature(cls="moMateCoincident", owner=group, allocator=allocator, name=name, **target)
    mate["f410"] = [{"o": resolved_planar_wrapper(endpoint=endpoint)} for endpoint in endpoints]
    return mate


def wrapper_ids(wrappers):
    return [[wrapper[key] for key in ("f74", "f78", "f7c")] for wrapper in wrappers]


def main():
    request = fields(json.load(sys.stdin), "planar wrapper assignments", ("bundle", "endpoints", "mate_names"))
    names = tuple(sequence(request["mate_names"], "mate names"))
    require(len(names) == 2 and names[0] != names[1], "the assignment probe requires two named mates")
    tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
    rules = registry()
    version = DOCUMENT_VERSION_2026
    AUDIT.BeginBuild()
    bundle = construct_assembly_bundle(registry=rules, request=request["bundle"])
    config, resolved, inherited = read_state(bundle, rules)
    owner, header = config.roots[0], config.head["model_header"]
    group, = [node for node in resolved.roots if node.cls == "moMateGroup_c"]
    group["owner"] = owner
    selections = select_endpoints(bundle=bundle, owner=owner, selectors=request["endpoints"])
    endpoints = tuple(endpoint for _, endpoint in selections)
    allocator = PersistentIds(next_id=header["f08"])
    target = request["bundle"]["assembly"]["target"]
    mates = [
        registered_mate(name=name, group=group, allocator=allocator, endpoints=order, target=target)
        for name, order in zip(names, (endpoints, tuple(reversed(endpoints))), strict=True)
    ]
    original = bundle.assembly.streams[CONFIG]
    require(store_config_state(config, rules, version)[0] == original and owner["fd48"] == 0,
            "the probe must use a fresh exact configuration with an empty reference counter")
    for mate in mates:
        register_planar_wrapper_ids(mate=mate)
    wrappers = tuple(row["o"] for mate in mates for row in mate["f410"])
    expected = [[mate["f08"], 2 * index + ordinal, ordinal]
                for index, mate in enumerate(mates) for ordinal in range(2)]
    require(wrapper_ids(wrappers) == expected and owner["fd48"] == 4,
            "successive mates must allocate separately from their local endpoint ordinals")
    register_planar_wrapper_ids(mate=mates[0])
    require(wrapper_ids(wrappers) == expected and owner["fd48"] == 4, "retry consumed a previously allocated ID")

    rejected = registered_mate(name=names[0], group=group, allocator=allocator, endpoints=endpoints, target=target)
    first = rejected["f410"][0]["o"]
    rejected["f410"][1]["o"] = None
    try:
        register_planar_wrapper_ids(mate=rejected)
    except ValueError:
        require(first["f78"] == -12345 and owner["fd48"] == 4, "invalid wrapper left a partial allocation")
    else:
        raise ValueError("an invalid wrapper received a reference ID")

    payload, count = encode(wrappers, inherited, rules)
    reader = Load(payload, inherited.count, rules, version, seed=inherited)
    decoded = [reader.obj() for _ in wrappers]
    require(not reader.left() and reader.count == count and wrapper_ids(decoded) == expected
            and encode(decoded, inherited, rules) == (payload, count), "wrapper IDs did not re-encode exactly")
    config_bytes, config_map = store_config_state(config, rules, version)
    candidate = SldprtArchive.from_bytes(build_sldprt({**bundle.assembly.streams, CONFIG: config_bytes}))
    checked, _ = load_config(config_bytes, rules, version, archive=candidate, name=CONFIG)
    require(checked.roots[0]["fd48"] == checked.roots[0]["fd48#wire"] == 4,
            "Config-0 did not carry the advanced wrapper counter")
    differences = [offset for offset, (before, after) in enumerate(zip(original, config_bytes, strict=True)) if before != after]
    require(len(differences) == 1 and config_map.count == bundle.assembly.config_map_count,
            "the wrapper counter unexpectedly changed other Config-0 bytes or map identities")
    print(json.dumps({
        "schema": "kit.sw2026.planar-wrapper-reference-ids.v1", "native_acceptance": False, "writer_output_count": 0,
        "heldout_inputs_tested": 0, "input_runtime_file_access_attempts": len(AUDIT.DeniedReads),
        "ids": expected, "next_reference_id": checked.roots[0]["fd48"], "config_byte_offset": differences[0],
        "config_map_next_index": config_map.count, "wrapper_map_next_index": count,
        "wrapper_archive_bytes": len(payload), "wrapper_archive_sha256": sha256(payload).hexdigest(),
        "retry_preserved_ids": True, "invalid_input_left_state_unchanged": True,
    }, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
