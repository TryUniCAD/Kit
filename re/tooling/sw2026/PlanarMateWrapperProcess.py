from __future__ import annotations

import codecs
from hashlib import sha256
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PlanarMateEndpointProcess import AUDIT, read_state, require, select_endpoints

from Classes import registry
from Core import DOCUMENT_VERSION_2026, Load, Store
from builders.AssemblyDocument import construct_assembly_bundle
from builders.AssemblyMateEndpoint import resolved_planar_wrapper
from builders.Metadata import fields


def encode(records, inherited, rules):
    archive = Store(inherited.count, rules, DOCUMENT_VERSION_2026, seed=inherited)
    for wrapper in records:
        archive.obj(wrapper)
    return bytes(archive.out), archive.count


def inspect_wrapper(*, wrapper, owner, occurrence, endpoint):
    require(wrapper.cls == "moPlaneRef_w", "resolved endpoint lost its concrete wrapper class")
    require((wrapper["f74"], wrapper["f78"], wrapper["f7c"]) == (-12345, -12345, -12345),
            "the pre-selection wrapper must retain its unassigned identity")
    require(wrapper["f68"] == 1 and wrapper["f50"] == 0 and wrapper["f60"] is None,
            "resolved wrapper lost its valid fresh plane state")
    require(wrapper["f0c"] == endpoint.configuration_id and wrapper["f188"] == dict.fromkeys("xyz", 0.0),
            "resolved wrapper changed its selected configuration or default point")
    require(wrapper["has_f10"] == wrapper["has_f18"] == 1,
            "resolved wrapper omitted an actual placement transform")
    require(all(wrapper[key] == value for key, value in endpoint.resolved_geometry.items()),
            "resolved wrapper geometry or child stamp differs")
    plane = wrapper["f58"]
    chain = plane["f58"]
    link, = (row["o"] for row in chain["f20"]["f08"]["f08"])
    require(chain["owner"] is owner and link is occurrence["f4f8"] and link["f50"] is occurrence,
            "resolved wrapper lost its assembly occurrence alias")
    require(plane["ff0"] == endpoint.component_plane["ff0"] and plane["f100"] == endpoint.component_plane["f100"],
            "resolved wrapper changed its registered datum")
    return {"occurrence_id": occurrence["f08"], "datum": plane["ff0"], "configuration_id": wrapper["f0c"],
            "initial_rigid_status": wrapper["f50"], "selection": [wrapper["f74"], wrapper["f78"], wrapper["f7c"]]}


def main():
    request = fields(json.load(sys.stdin), "resolved planar wrappers", ("bundle", "endpoints"))
    tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
    rules = registry()
    AUDIT.BeginBuild()
    bundle = construct_assembly_bundle(registry=rules, request=request["bundle"])
    owner, inherited = read_state(bundle, rules)
    selections = select_endpoints(bundle=bundle, owner=owner, selectors=request["endpoints"])
    wrapped = [resolved_planar_wrapper(endpoint=endpoint) for _, endpoint in selections]
    payload, count = encode(wrapped, inherited, rules)
    reader = Load(payload, inherited.count, rules, DOCUMENT_VERSION_2026, seed=inherited)
    decoded = [reader.obj() for _ in selections]
    rows = [inspect_wrapper(wrapper=wrapper, owner=owner, occurrence=occurrence, endpoint=endpoint)
            for wrapper, (occurrence, endpoint) in zip(decoded, selections, strict=True)]
    require(not reader.left() and reader.count == count and encode(decoded, inherited, rules) == (payload, count),
            "resolved wrappers did not consume and re-encode exactly")
    print(json.dumps({
        "schema": "kit.sw2026.generated-resolved-planar-wrapper.v1", "native_acceptance": False,
        "heldout_inputs_tested": 0, "writer_output_count": 0,
        "input_runtime_file_access_attempts": len(AUDIT.DeniedReads),
        "wrapper_archive_bytes": len(payload), "wrapper_archive_sha256": sha256(payload).hexdigest(),
        "inherited_map_next_index": inherited.count, "wrapper_map_next_index": count, "wrappers": rows,
    }, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
