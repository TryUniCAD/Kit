from __future__ import annotations

import codecs
from hashlib import sha256
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
for directory in (ROOT, ROOT / "src", ROOT / "re/tooling/sw2026", ROOT / "re/tooling/sw2026/serial"):
    sys.path.insert(0, str(directory))

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from Classes import registry
from Core import DOCUMENT_VERSION_2026, Load, Obj, Store
from builders.AssemblyDocument import CONFIG, RESOLVED, construct_assembly_bundle
from builders.AssemblyMateEndpoint import planar_mate_endpoint
from builders.Metadata import fields, integer, sequence
from defs.ConfigPart import load_config
from defs.ResolvedCore import load_resolved
from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt


XFORM = "mgXform_c.restore"
POINT = "mgPoint_c.restore"
VECTOR = "mgVector_c.restore"
DETACHED = (
    ("fb0", "f64"), ("fb8", "f64"), ("fc0", "f64"), ("fc8", "f64"),
    ("fd0", POINT), ("fe8", VECTOR), ("f100", XFORM),
)
RECORDS = (("f08", "i32"), ("f10", XFORM), ("f18", XFORM), *DETACHED)


def require(check, message):
    if not check:
        raise ValueError(message)


def write_geometry(archive, schemas, geometry):
    for key, schema in schemas:
        if schema in ("i32", "f64"):
            archive.prim(schema, geometry[key])
            continue
        record = Obj(schema, geometry[key])
        archive.registry.run_store(schema, archive, record.f, record)


def read_geometry(archive, schemas):
    result = {}
    for key, schema in schemas:
        if schema in ("i32", "f64"):
            result[key] = archive.prim(schema)
            continue
        record = Obj(schema)
        archive.registry.run_load(schema, archive, record.f, record)
        result[key] = record.f
    return result


def encode(endpoints, inherited, rules):
    archive = Store(inherited.count, rules, DOCUMENT_VERSION_2026, seed=inherited)
    for selected, resolved, detached in endpoints:
        archive.obj(selected)
        write_geometry(archive, RECORDS, resolved)
        write_geometry(archive, DETACHED, detached)
    return bytes(archive.out), archive.count


def read_state(bundle, rules):
    archive = SldprtArchive.from_bytes(build_sldprt(bundle.assembly.streams))
    config, initial = load_config(archive.require(CONFIG), rules, DOCUMENT_VERSION_2026, archive=archive, name=CONFIG)
    resolved, final = load_resolved(archive.require(RESOLVED), rules, DOCUMENT_VERSION_2026,
                                    archive=archive, name=RESOLVED, seed=initial.map_state())
    require(not config.tail and not resolved.tail, "the generated assembly seed graph did not consume exactly")
    return config.roots[0], final.map_state()


def decode_endpoint(archive, expected, reference, owner):
    selected = archive.obj()
    chain = selected["f58"]
    path = chain["f20"]
    link, = (row["o"] for row in path["f08"]["f08"])
    require(selected.cls == "moCompRefPlane_c" and selected["ff8"] is None
            and chain.cls == "moChainComponent_c" and chain["owner"] is owner,
            "selected mate datum lost its chain or assembly owner")
    require(link is reference["f4f8"] and link["f50"] is reference and link["f44"] == reference["f08"],
            "mate path lost the inherited occurrence or external-feature alias")
    require(path["f20"] == path["f24"] == 0 and path["f40"]["f10"] == -1 and path["f08"]["n"] == 1,
            "the generated one-hop chain changed its constructor conditions")
    require(selected["ff0"] == expected.component_plane["ff0"] and selected["f100"] == expected.component_plane["f100"],
            "mate path lost the selected child datum or creation time")

    resolved = read_geometry(archive, RECORDS)
    detached = read_geometry(archive, DETACHED)
    wanted = {key: expected.resolved_geometry[key] for key, _ in RECORDS}
    fallback = {key: expected.detached_geometry[key] for key, _ in DETACHED}
    require(resolved == wanted and detached == fallback, "the selected plane geometry changed on readback")
    return selected, resolved, detached


def select_endpoints(*, bundle, owner, selectors):
    selectors = tuple(sequence(selectors, "mate endpoint selections"))
    require(len(selectors) == 2, "the endpoint probe requires exactly two selections")
    occurrences = [row["o"] for row in owner["f68"]["list"]["items"]]
    datums = {node["f18"]["f08"]: node for node in bundle.child.features if node.get("_principal_axis")}
    selected = []
    for selector in selectors:
        inputs = fields(selector, "mate endpoint", ("occurrence", "datum"), ("created_at",))
        ordinal = integer(inputs["occurrence"], "occurrence ordinal", low=0, high=len(occurrences) - 1)
        reference = occurrences[ordinal]
        datum = datums.get(inputs["datum"])
        require(datum is not None, "the selected datum does not exist in the generated child")
        endpoint = planar_mate_endpoint(assembly=owner, occurrence=reference, child=bundle.child, datum=datum, created_at=inputs.get("created_at"))
        selected.append((reference, endpoint))
    require(selected[0][0] is not selected[1][0], "the two selections must exercise distinct occurrence identities")
    return selected


def main():
    request = fields(json.load(sys.stdin), "planar mate endpoint probe", ("bundle", "endpoints"))
    rules = registry()
    tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
    AUDIT.BeginBuild()
    bundle = construct_assembly_bundle(registry=rules, request=request["bundle"])
    owner, inherited = read_state(bundle, rules)
    selected = select_endpoints(bundle=bundle, owner=owner, selectors=request["endpoints"])
    data, next_index = encode(((row.component_plane, row.resolved_geometry, row.detached_geometry) for _, row in selected), inherited, rules)
    reader = Load(data, inherited.count, rules, DOCUMENT_VERSION_2026, seed=inherited)
    decoded = [decode_endpoint(reader, row, reference, owner) for reference, row in selected]
    require(not reader.left() and reader.count == next_index, "endpoint mini-archive map did not consume exactly")
    require(encode(decoded, inherited, rules) == (data, next_index), "decoded endpoints did not re-encode exactly")
    print(json.dumps({
        "schema": "kit.sw2026.generated-planar-mate-endpoint-graph.v2",
        "native_acceptance": False, "heldout_inputs_tested": 0,
        "input_runtime_file_access_attempts": len(AUDIT.DeniedReads),
        "endpoint_archive_bytes": len(data), "endpoint_archive_sha256": sha256(data).hexdigest(),
        "inherited_map_next_index": inherited.count, "endpoint_map_next_index": next_index,
        "endpoints": [{
            "occurrence_id": reference["f08"], "datum_id": endpoint.component_plane["ff0"]["f00"],
            "datum_created_at": endpoint.component_plane["ff0"]["f08"],
            "resolved_geometry": endpoint.resolved_geometry,
            "detached_geometry": endpoint.detached_geometry,
        } for reference, endpoint in selected],
    }, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
