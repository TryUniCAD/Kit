from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from json import dumps
from sys import addaudithook
from uuid import NAMESPACE_URL, uuid5

from downstream.FaceOperands import single_loop_face_operands
from drawing_edges.CheckDownstreamPartition import inspect_attributes, prepare_prism
from para.DownstreamIds import FACE_DEFINITION, allocate_fresh_downstream, owned_solid_chains
from para.Partition import frame_payloads, read_partition, write_payloads
from para.rectangle.CheckProjection import schedule


def read_operands(partition):
    nodes = {node.index: node for node in partition.nodes}
    attributes = inspect_attributes(partition)
    identifiers = {
        node.index: attributes[(FACE_DEFINITION, node.fields["node_id"])][0]
        for node in partition.nodes if node.kind == 14
    }
    output = {}
    for face, number in identifiers.items():
        loop = nodes[nodes[face].fields["loop"]]
        origin = loop.fields["halfedge"]
        index = origin
        previous = set()
        related = [number]
        while index not in previous:
            previous.add(index)
            fin = nodes[index]
            partner = nodes[fin.fields["other"]]
            related.append(identifiers[nodes[partner.fields["loop"]].fields["face"]])
            index = fin.fields["forward"]
        assert index == origin
        related.append(None)
        output[number] = (
            tuple(related),
            tuple((slot, owner) for slot, owner in enumerate(related) if owner is not None and owner < number),
        )
    return identifiers, output


def main():
    parser = ArgumentParser()
    parser.add_argument("variant", type=int, choices=(1, 2))
    args = parser.parse_args()
    for encoding in ("utf-8", "utf-16le", "utf-16be", "cp1252", "latin-1"):
        lookup(encoding)
    second = 1818197000 + 243 * args.variant
    fraction = 833710 * args.variant
    session = schedule(1492 + 318 * args.variant, 24, 1, 0, 3, 1, 1, second, fraction)
    name, topology, project = prepare_prism(session, args.variant)
    owner = uuid5(NAMESPACE_URL, "urn:kit:solidworks:downstream:face:" + name)
    attempts = []
    active = True

    def guard(event, arguments):
        if active and event in ("open", "subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect"):
            attempts.append(event)
            raise RuntimeError("unexpected runtime operation: " + event)

    addaudithook(guard)
    try:
        faces, edges = owned_solid_chains(topology)
        allocation = allocate_fresh_downstream(faces, edges, owner, second, fraction, is_assembly=False)
        raw = frame_payloads(write_payloads(project(allocation)))
        partition = read_partition(raw)
        rows = single_loop_face_operands(partition, allocation, second, special_id_map_present=False)
        permuted = replace(partition, nodes=tuple(reversed(partition.nodes)))
        assert single_loop_face_operands(permuted, allocation, second, special_id_map_present=False) == rows
        identifiers, expected = read_operands(partition)
        projected = {
            row.downstream_id: (
                tuple(None if node is None else identifiers[node.index] for node in row.inline_faces),
                row.initial_role_values,
            )
            for row in rows
        }
        assert projected == expected
        assert tuple(projected) == tuple(range(1, len(faces) + 1))
        assert len(edges) == sum(len(role_map) for _, role_map in projected.values())
        assert not rows[0].initial_role_values
        assert all(row.inline_faces[0] is row.face and row.inline_faces[-1] is None
                   and len(row.inline_faces) == 6 for row in rows)

        broken = next(node for node in partition.nodes if node.kind == 17)
        broken_partition = replace(partition, nodes=tuple(
            replace(node, fields=node.fields | {"other": node.index}) if node is broken else node
            for node in partition.nodes
        ))
        refused = 0
        for proposed, special in ((partition, True), (broken_partition, False)):
            try:
                single_loop_face_operands(proposed, allocation, second, special_id_map_present=special)
            except ValueError:
                refused += 1
            else:
                raise AssertionError("face operands accepted a special map or invalid fin")
    finally:
        active = False
    print(dumps({
        "passed": True, "variant": args.variant, "faces": len(faces), "edges": len(edges),
        "face_operands": projected, "slots": sum(len(values) for values, _ in projected.values()),
        "prefix_role_values": sum(len(roles) for _, roles in projected.values()),
        "partition_sha256": sha256(raw).hexdigest(), "invalid_inputs_refused": refused,
        "runtime_io_attempts": len(attempts), "native_runs": 0,
        "scope": "ordinary one-loop face operands and initial role maps from generated topology",
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
