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
from Streams import load_rooted
from builders.AssemblyDocument import MANAGER, construct_assembly_bundle
from builders.AssemblyMateEndpoint import detached_planar_wrapper, resolved_planar_wrapper
from builders.Metadata import boolean, fields


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


def inspect_detached(*, wrapper, owner, endpoint, model_header, configuration):
    require(wrapper.cls == "moPlaneRef_w" and wrapper["f08"] == model_header["f40"] and wrapper["f0c"] == configuration["f08"],
            "detached wrapper lost the actual assembly header or configuration")
    require(wrapper["f68"] == 1 and wrapper["f50"] == 0 and wrapper["has_f10"] == wrapper["has_f18"] == 0,
            "detached wrapper retained an occurrence transform or invalid plane state")
    require([wrapper[key] for key in ("f74", "f78", "f7c")] == [-12345] * 3,
            "detached wrapper must retain its unassigned identity")
    require(all(wrapper[key] == value for key, value in endpoint.detached_geometry.items()),
            "detached wrapper geometry differs from the world-space plane")
    reference = wrapper["f58"]
    component, plane = reference["f58"], reference["ff8"]
    require(component.cls == "moUnitComponent_c" and component["owner"] is owner and component is not owner["f990"],
            "detached reference must own a separate unit component for the containing assembly")
    require(reference["ff0"] == {"f00": -1, "f08": 2592000} and reference["f100"] == 0,
            "detached reference must keep the absolute plane unregistered")
    require(reference["f9c"] == endpoint.component_plane["ff0"]["f00"],
            "detached reference lost the original registered datum ID")
    data = plane["f6f8"]
    require(plane.cls == "moRefPlane_c" and plane["f08"] == -1 and plane["f18"] is None and data.cls == "moAbsoluteRefPlnData_c",
            "detached reference did not retain its anonymous absolute plane")
    require(data["root"] == wrapper["fd0"] and data["normal"] == wrapper["fe8"] and data["f20"] == wrapper["f100"]
            and [data["f54"], data["f58"]] == [1, 2],
            "detached absolute plane differs from the constructor state and world geometry")
    require(all(data[f"b{index}"] == 0.0 for index in range(4)), "detached plane has nonzero surface bounds")
    return {"original_datum_id": reference["f9c"], "anonymous_datum": reference["ff0"], "assembly_configuration_id": wrapper["f0c"],
            "assembly_update_stamp": wrapper["f08"], "world_origin": data["root"], "world_normal": data["normal"]}


def main():
    request = fields(json.load(sys.stdin), "planar wrappers", ("bundle", "endpoints"), ("include_detached",))
    include_detached = boolean(request.get("include_detached", False), "detached wrapper selection")
    tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
    rules = registry()
    AUDIT.BeginBuild()
    bundle = construct_assembly_bundle(registry=rules, request=request["bundle"])
    config, _, inherited = read_state(bundle, rules)
    owner, model_header = config.roots[0], config.head["model_header"]
    selections = select_endpoints(bundle=bundle, owner=owner, selectors=request["endpoints"])
    wrapped = [resolved_planar_wrapper(endpoint=endpoint) for _, endpoint in selections]
    detached = []
    if include_detached:
        manager, _ = load_rooted(bundle.assembly.streams[MANAGER], rules, 1, DOCUMENT_VERSION_2026)
        configuration = manager.roots[0]["f360"]
        target = request["bundle"]["assembly"]["target"]
        detached = [detached_planar_wrapper(endpoint=endpoint, model_header=model_header, configuration=configuration, **target)
                    for _, endpoint in selections]
    wrapped = detached + wrapped
    payload, count = encode(wrapped, inherited, rules)
    reader = Load(payload, inherited.count, rules, DOCUMENT_VERSION_2026, seed=inherited)
    decoded = [reader.obj() for _ in wrapped]
    detached_rows = []
    if include_detached:
        detached_rows = [inspect_detached(wrapper=wrapper, owner=owner, endpoint=endpoint, model_header=model_header, configuration=configuration)
                         for wrapper, (_, endpoint) in zip(decoded[:len(detached)], selections, strict=True)]
    rows = [inspect_wrapper(wrapper=wrapper, owner=owner, occurrence=occurrence, endpoint=endpoint)
            for wrapper, (occurrence, endpoint) in zip(decoded[len(detached):], selections, strict=True)]
    require(not reader.left() and reader.count == count and encode(decoded, inherited, rules) == (payload, count),
            "resolved wrappers did not consume and re-encode exactly")
    print(json.dumps({
        "schema": "kit.sw2026.generated-" + ("paired" if include_detached else "resolved") + "-planar-wrapper.v1",
        "native_acceptance": False,
        "heldout_inputs_tested": 0, "writer_output_count": 0,
        "input_runtime_file_access_attempts": len(AUDIT.DeniedReads),
        "wrapper_archive_bytes": len(payload), "wrapper_archive_sha256": sha256(payload).hexdigest(),
        "inherited_map_next_index": inherited.count, "wrapper_map_next_index": count, "wrappers": rows,
        **({"detached_wrappers": detached_rows} if detached_rows else {}),
    }, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
