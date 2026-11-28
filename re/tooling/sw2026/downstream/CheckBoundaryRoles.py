from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from json import dumps
from sys import addaudithook
from uuid import NAMESPACE_URL, uuid5

from downstream.BoundaryRoles import prepare_boundary_roles
from downstream.CacheInputs import prepare_part_cache_inputs
from drawing_edges.CheckDownstreamPartition import inspect_attributes, prepare_cylinder, prepare_prism
from para.DownstreamIds import EDGE_DEFINITION, FACE_DEFINITION
from para.Partition import frame_payloads, read_partition, write_payloads
from para.rectangle.CheckProjection import schedule



def read_coordinates(partition):
    nodes = {node.index: node for node in partition.nodes}
    attrs = inspect_attributes(partition)
    old = []
    roles = {}
    for node in partition.nodes:
        if node.kind == 81:
            definition = nodes[node.fields["definition"]]
            name = nodes[definition.fields["identifier"]].fields["string"]
            if name == "EDGE_PERM_ID_2001":
                old.append(node.index)
        if node.kind != 17 or node.fields["sense"] != "+":
            continue
        edge = nodes[node.fields["edge"]]
        identifier = attrs[(EDGE_DEFINITION, edge.fields["node_id"])][0]
        other = nodes[node.fields["other"]]
        previous = nodes[nodes[node.fields["backward"]].fields["other"]]
        following = nodes[nodes[node.fields["forward"]].fields["other"]]
        rows = []
        for key, owner in enumerate((node, other, previous, following)):
            face = nodes[nodes[owner.fields["loop"]].fields["face"]]
            rows.append((key, attrs[(FACE_DEFINITION, face.fields["node_id"])][0]))
        roles[identifier] = tuple(rows)
    return old, roles


def main():
    cli = ArgumentParser()
    cli.add_argument("shape", choices=("prism", "cylinder"))
    cli.add_argument("variant", type=int, choices=(1, 2))
    args = cli.parse_args()
    for encoding in ("utf-8", "cp1252", "utf-16le", "utf-16be"):
        lookup(encoding)
    stamp = 1818198000 + args.variant * 117
    ticks = 843165 * args.variant
    session = schedule(1739 + 103 * args.variant, 24, 1, 0, 3, 1, 1, stamp, ticks)
    name, topology, project = (prepare_prism if args.shape == "prism" else prepare_cylinder)(session, args.variant)
    owner = uuid5(NAMESPACE_URL, "urn:kit:solidworks:downstream:" + name)
    events = []
    enabled = True

    def guard(event, args):
        if enabled and event in ("open", "socket.connect", "subprocess.Popen"):
            events.append(event)
            raise RuntimeError("unexpected external operation during boundary role replay")

    addaudithook(guard)
    try:
        plan = prepare_part_cache_inputs(topology, owner, stamp, ticks)
        output = frame_payloads(write_payloads(project(plan.allocation)))
        partition = read_partition(output)
        predicted_by_edge = prepare_boundary_roles(topology, plan, partition, special_id_map_present=False)
        predicted = {row.downstream_id: predicted_by_edge[row.edge] for row in plan.incidence}
        old_attr, readback = read_coordinates(partition)
        assert not old_attr
        assert predicted == readback
        assert len(readback) == len(plan.incidence)
        if args.shape == "cylinder":
            assert all(rows[1][1] == rows[2][1] == rows[3][1] for rows in readback.values())
        nodes = {node.index: node for node in partition.nodes}
        attr_name = next(nodes[nodes[attr.fields["definition"]].fields["identifier"]]
                         for attr in partition.nodes if attr.kind == 81
                         and nodes[nodes[attr.fields["definition"]].fields["identifier"]].fields["string"] == EDGE_DEFINITION)
        edited = replace(attr_name, fields={**attr_name.fields, "string": "EDGE_PERM_ID_2001"})
        with_permanent_id = replace(partition, nodes=tuple(
            edited if node.index == edited.index else node for node in partition.nodes
        ))
        without_edge = next(node.index for node in partition.nodes if node.kind == 16)
        foreign_partition = replace(partition, nodes=tuple(node for node in partition.nodes if node.index != without_edge))
        for forbidden, special in ((partition, True), (with_permanent_id, False), (foreign_partition, False)):
            try:
                prepare_boundary_roles(topology, plan, forbidden, special_id_map_present=special)
            except ValueError:
                pass
            else:
                raise AssertionError("accepted a different boundary role context")
    finally:
        enabled = False
    print(dumps({
        "passed": True, "shape": args.shape, "variant": args.variant,
        "edge_role_rows": len(readback), "boundary_roles_read_back": 2 * len(readback),
        "selected_persistent_edge_attributes": len(old_attr), "negative_refusals": 3, "runtime_io_attempts": len(events),
        "native_runs": 0, "scope": "generated partition without any installed permanent edge identifier",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
