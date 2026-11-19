from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from math import isclose
from pathlib import Path
import platform
import zlib

from builders.EmptyPartition import PARTITION_KIND, PMARK_KIND, SOLIDWORKS_2026, WORLD_KIND
from convert.Geometry.Parasolid import DecodePartData, EncodePartData, ParaHeaderData, ParaStream
from convert.adapters.solidworks.Container.Container import SldprtArchive
from para.Partition import HEADER, SCHEMAS, decode_active, references, terminate, write_node
from para.rectangle.Attributes import Field, Owner, RECTANGLE_DEFINITION_BY_NAME, actions


DISCLOSED_SHA256 = "13f1ef12ab727323a826ead989087079f44e9b24a4326aa9b65be61c9d81f325"
LOCAL_STREAM = "Config-0-FeatureBodies/LocalBodies"
MODEL_SCHEMA = SOLIDWORKS_2026.schema
MODEL_DESCRIPTION = f": TRANSMIT FILE created by modeller version {SOLIDWORKS_2026.modeller_version}"
BODY, SHELL, FACE, LOOP, EDGE, FIN, VERTEX, REGION, POINT = 12, 13, 14, 15, 16, 17, 18, 19, 29
ATTRIBUTE_LIST, POINTER_BLOCK, DEFINITION_NAME, DEFINITION, ATTRIBUTE = 70, 74, 79, 80, 81
SOLID_BODY = 1
OWNER_TYPES = {BODY: Owner.BODY, FACE: Owner.FACE, EDGE: Owner.EDGE}
SLOT_TYPES = {Field.INT: 82, Field.REAL: 83, Field.CHAR: 84, Field.UNICODE: 98}
EXPECTED_BOUNDS_M = ((-0.0025, -0.0245, 0.004), (0.0165, 0.0025, 0.017))
OWNING_SOURCES = (
    "re/tooling/sw2026/imported_body_source/LocalBodyKernel.py",
    "re/tooling/sw2026/para/Partition.py",
    "re/tooling/sw2026/para/Schema.py",
    "re/tooling/sw2026/para/rectangle/Attributes.py",
    "src/convert/Geometry/Parasolid.py",
    "src/convert/adapters/solidworks/Container/Container.py",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def object_at(nodes, index, kind):
    value = nodes.get(index)
    require(value is not None and value.kind == kind, f"slot {index} does not resolve as {SCHEMAS[kind].name}")
    return value


def paired_chain(nodes, head, kind, following, preceding):
    seen = set()
    prior = 0
    while head:
        require(head not in seen, f"loop in {SCHEMAS[kind].name}.{following} chain")
        node = object_at(nodes, head, kind)
        require(node.fields[preceding] == prior, f"nonreciprocal {SCHEMAS[kind].name}.{preceding}")
        seen.add(head)
        prior, head = head, node.fields[following]
    return seen


def active_ownership(nodes, body):
    nonresident = 0
    for node in nodes.values():
        for field in SCHEMAS[node.kind].current:
            if field.encoding != "p":
                continue
            value = node.fields[field.name]
            for target in value if field.count else (value,):
                if not target or target in nodes:
                    continue
                require(node.kind == DEFINITION and field.name == "next" and field.pointer_class == DEFINITION,
                        f"unresolved pointer in {SCHEMAS[node.kind].name}.{field.name}")
                nonresident += 1
    reachable, pending = set(), [body.index]
    while pending:
        current = pending.pop()
        if current not in reachable:
            reachable.add(current)
            pending.extend(target for target in references(nodes[current]) if target in nodes)
    require(reachable == nodes.keys(), "resident nodes escape the local BODY graph")
    return nonresident


def solid_ownership(nodes, body):
    region_ids = paired_chain(nodes, body.fields["region"], REGION, "next", "previous")
    regions = {nodes[index].fields["type"]: nodes[index] for index in region_ids}
    require(len(region_ids) == 2 and set(regions) == {"S", "V"}, "local solid requires its solid and void regions")
    require(region_ids == {node.index for node in nodes.values() if node.kind == REGION},
            "local region escapes the BODY chain")
    shells = {}
    for kind, region in regions.items():
        shell = object_at(nodes, region.fields["shell"], SHELL)
        require(region.fields["body"] == body.index and shell.fields["region"] == region.index,
                "local region and shell ownership differ")
        require(shell.fields["body"] == (body.index if kind == "S" else 0), "unexpected solid or void shell owner")
        shells[kind] = shell
    solid, void = shells["S"], shells["V"]
    require({solid.index, void.index} == {node.index for node in nodes.values() if node.kind == SHELL}
            and body.fields["shell"] == solid.index, "primary boundary shell differs")
    faces = {node.index for node in nodes.values() if node.kind == FACE}
    require(paired_chain(nodes, solid.fields["face"], FACE, "next", "previous") == faces
            and paired_chain(nodes, void.fields["front_face"], FACE, "next_front", "previous_front") == faces,
            "solid and void shell face chains differ")
    for kind, head in ((EDGE, "edge"), (VERTEX, "vertex")):
        boundary = paired_chain(nodes, body.fields[head], kind, "next", "previous")
        require(boundary == {node.index for node in nodes.values() if node.kind == kind},
                f"local {head} escapes the BODY chain")
    for node in nodes.values():
        values = node.fields
        if node.kind == FACE:
            require((values["shell"], values["front_shell"]) == (solid.index, void.index)
                    and object_at(nodes, values["loop"], LOOP).fields["face"] == node.index,
                    "face does not bind its two shells and local loop")
        elif node.kind in (EDGE, VERTEX):
            require(values["owner"] == body.index, "boundary entity does not belong to the local BODY")
        elif node.kind == FIN:
            forward = object_at(nodes, values["forward"], FIN)
            reverse = object_at(nodes, values["other"], FIN)
            require(forward.fields["backward"] == node.index and forward.fields["loop"] == values["loop"]
                    and reverse.fields["other"] == node.index and reverse.fields["edge"] == values["edge"],
                    "local fin does not preserve loop and edge identity")


def verify_declaration(nodes, definition):
    fields = definition.fields
    name = object_at(nodes, fields["identifier"], DEFINITION_NAME).fields["string"]
    known = RECTANGLE_DEFINITION_BY_NAME.get(name)
    require(known is not None, f"no shared declaration for local attribute {name}")
    expected = (known.type_id, actions(known.action), tuple(int(index in known.owners) for index in range(17)),
                tuple(map(int, known.fields)))
    actual = tuple(fields[key] for key in ("type_id", "actions", "legal_owners", "fields"))
    require(actual == expected, f"shared declaration differs for {name}")
    return known


def attribute_ownership(nodes, body):
    definitions = {node.index: verify_declaration(nodes, node) for node in nodes.values() if node.kind == DEFINITION}
    require(len({known.name for known in definitions.values()}) == len(definitions),
            "local definition names are repeated")
    by_owner, by_type = defaultdict(set), defaultdict(set)
    signatures, owner_counts = Counter(), Counter()
    for node in nodes.values():
        if node.kind != ATTRIBUTE:
            continue
        fields = node.fields
        definition = object_at(nodes, fields["definition"], DEFINITION)
        known = definitions[definition.index]
        owner = nodes.get(fields["owner"])
        require(owner is not None and OWNER_TYPES.get(owner.kind) in known.owners,
                f"invalid local attribute owner for {known.name}")
        require(len(fields["fields"]) == len(known.fields), f"wrong local slot count for {known.name}")
        slots = []
        for code, target in zip(known.fields, fields["fields"], strict=True):
            if target:
                require(code in SLOT_TYPES, f"unproven nonnull {known.name} pointer slot")
                slots.append(SCHEMAS[object_at(nodes, target, SLOT_TYPES[code]).kind].name)
            else:
                slots.append("null")
        by_owner[owner.index].add(node.index)
        by_type[definition.index].add(node.index)
        owner_kind = SCHEMAS[owner.kind].name
        signatures[known.name, owner_kind, tuple(slots)] += 1
        owner_counts[owner_kind] += 1

    for node in nodes.values():
        if "attributes_features" in node.fields:
            group = paired_chain(nodes, node.fields["attributes_features"], ATTRIBUTE, "next", "previous")
            require(group == by_owner.get(node.index, set()), "local owner chain misses its actual attributes")
    listing = object_at(nodes, body.fields["attribute_chains"], ATTRIBUTE_LIST).fields
    block_index = listing["list_block"]
    block = object_at(nodes, block_index, POINTER_BLOCK).fields
    require(listing["owner"] == body.index and listing["list_type"] == 4
            and not listing["next"] and not listing["previous"]
            and listing["finger_block"] == block_index and not block["next_block"], "unproven local type list shape")
    count = block["n_entries"]
    entries = block["entries"]
    require(0 < count <= len(entries) and listing["list_length"] == count
            and listing["block_length"] == len(entries) and not any(entries[count:]), "local attribute heads count differs")
    checked_types = set()
    for head in entries[:count]:
        definition_index = object_at(nodes, head, ATTRIBUTE).fields["definition"]
        chain = paired_chain(nodes, head, ATTRIBUTE, "next_of_type", "previous_of_type")
        require(definition_index not in checked_types and chain == by_type[definition_index],
                "local type chain crosses declarations or misses owners")
        checked_types.add(definition_index)
    require(checked_types == definitions.keys(), "not every local declaration has its own type chain")
    return {
        "attribute_count": sum(signatures.values()),
        "attribute_count_by_owner_kind": dict(owner_counts),
        "owner_chain_count": len(by_owner),
        "type_chain_count": len(checked_types),
        "declared_attribute_count": len(definitions),
        "shared_declaration_matches": len(definitions),
        "slot_profiles": [{"attribute": name, "owner_kind": owner, "slot_kinds": slots, "count": count}
                          for (name, owner, slots), count in sorted(signatures.items())],
    }


def audit_nodes(nodes):
    indexed = {node.index: node for node in nodes}
    require(nodes and len(indexed) == len(nodes) and all(index > 0 for index in indexed), "invalid local transmit slots")
    body = nodes[0]
    require(body.kind == BODY and body.fields["owner"] == 0 and body.fields["body_type"] == SOLID_BODY
            and sum(node.kind == BODY for node in nodes) == 1, "local transmit must start with one ownerless BODY")
    require(not any(node.kind in (WORLD_KIND, PARTITION_KIND, PMARK_KIND) for node in nodes),
            "local transmit cannot contain active WORLD or history")
    nonresident = active_ownership(indexed, body)
    solid_ownership(indexed, body)
    attributes = attribute_ownership(indexed, body)
    return {
        "body_index": body.index, "body_owner": body.fields["owner"], "body_type": body.fields["body_type"],
        "resident_nodes": len(nodes), "resident_nodes_reachable_from_body": len(nodes),
        "node_kinds": dict(sorted(Counter(SCHEMAS[node.kind].name for node in nodes).items())),
        "nonresident_pointer_counts": {"ATTRIB_DEF.next": nonresident} if nonresident else {},
        "attributes": attributes,
    }


def decode_local(payload):
    header = ParaHeaderData(payload)
    require(header is not None and header.schema == MODEL_SCHEMA and header.description == MODEL_DESCRIPTION,
            "unrecognized bare local BODY transmit header")
    return decode_active(payload[header.body_offset:]), header.body_offset


def _render_local(nodes):
    body = bytearray(HEADER)
    seen = set()
    for node in nodes:
        write_node(body, node, seen)
    terminate(body)
    return ParaStream(body, MODEL_SCHEMA, MODEL_DESCRIPTION.encode("ascii"))


def encode_closed_local(nodes):
    observation = audit_nodes(nodes)
    require(not observation["nonresident_pointer_counts"], "fresh local encoding requires closed definition links")
    return _render_local(nodes)


def fingerprint(data):
    return {"bytes": len(data), "sha256": sha256(data).hexdigest()}


def measure_disclosed(path):
    source = path.read_bytes()
    require(sha256(source).hexdigest() == DISCLOSED_SHA256, "disclosed local BODY source hash differs")
    stream = SldprtArchive.from_bytes(source).streams[LOCAL_STREAM]
    payload, = DecodePartData(stream, LOCAL_STREAM)
    end = payload.wrapper_offset + payload.stored_size
    require(end == len(stream), "disclosed local BODY wrapper does not cover the stream tail")
    original_frame = stream[payload.wrapper_offset:end]
    nodes, header_size = decode_local(payload.data)
    graph = audit_nodes(nodes)
    points = [node.fields["pvec"] for node in nodes if node.kind == POINT]
    axes = tuple(zip(*points, strict=True))
    bounds = tuple(tuple(bound(axis) for axis in axes) for bound in (min, max))
    require(len(points) == 8 and len(axes) == 3 and all(
        isclose(actual, expected, rel_tol=0, abs_tol=1e-12)
        for observed, planned in zip(bounds, EXPECTED_BOUNDS_M, strict=True)
        for actual, expected in zip(observed, planned, strict=True)
    ), "kernel points disagree with the independent disclosed box")
    regenerated = _render_local(nodes)
    require(regenerated == payload.data, "typed local BODY changed the raw transmit")
    compressed = EncodePartData(regenerated)
    require(compressed == original_frame, "typed local BODY changed the compressed wrapper")
    repository = Path(__file__).resolve().parents[4]
    return {
        "schema": "kit.sw2026.imported-local-body-kernel.v1",
        "source": fingerprint(source),
        "source_build_reported_by_oracle_owner": "SOLIDWORKS 2026 SP05.2 34.5.2.0604",
        "owning_sources_sha256": {name: sha256((repository / name).read_bytes()).hexdigest() for name in OWNING_SOURCES},
        "scope": "Disclosed native file. In-memory typed replay and ownership audit, with no writer acceptance.",
        "stream": {"name": LOCAL_STREAM, **fingerprint(stream)},
        "sample_byte_offsets": {"wrapper": payload.wrapper_offset, "magic": payload.magic_offset,
                                "compressed": payload.compressed_offset, "wrapper_end": end},
        "transmit": {"schema": MODEL_SCHEMA, "description": MODEL_DESCRIPTION, "header_bytes": header_size,
                     "active_body": fingerprint(regenerated[header_size:]), "raw": fingerprint(regenerated),
                     "raw_byte_exact": True, "zlib_bytes": payload.compressed_size,
                     "wrapper": fingerprint(compressed), "compressed_wrapper_byte_exact": True},
        "graph": graph,
        "point_bounds_m": bounds,
        "expected_bounds_m": EXPECTED_BOUNDS_M,
        "kit_writer_outputs": 0,
        "native_writer_acceptance": False,
        "runtime": {"python": platform.python_version(), "zlib": zlib.ZLIB_RUNTIME_VERSION},
    }


def main():
    parser = argparse.ArgumentParser(description="Measure the disclosed native imported BODY transmit in memory")
    parser.add_argument("disclosed_source", type=Path)
    arguments = parser.parse_args()
    print(json.dumps(measure_disclosed(arguments.disclosed_source), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
