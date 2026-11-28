from argparse import ArgumentParser
from codecs import lookup
from collections import Counter, defaultdict
from dataclasses import replace
from hashlib import sha256
from json import dumps
from struct import pack
from sys import addaudithook
from uuid import NAMESPACE_URL, uuid5

from downstream.Body import PREFIX
from downstream.CacheInputs import initial_prefix, prepare_part_cache_inputs
from drawing_edges.CheckDownstreamPartition import inspect_attributes, prepare_cylinder, prepare_prism
from para.DownstreamIds import EDGE_DEFINITION, FACE_DEFINITION
from para.Partition import frame_payloads, read_partition, write_payloads
from para.rectangle.CheckProjection import schedule


def assert_incidence(original, plan, measured):
    attributes = inspect_attributes(measured)
    nodes = {node.index: node for node in measured.nodes}
    owners = {node.ref: node.fields["node_id"] for node in original if node.kind in (14, 16)}
    linked = defaultdict(Counter)
    roles = defaultdict(dict)
    for fin in measured.nodes:
        if fin.kind != 17:
            continue
        edge = nodes[fin.fields["edge"]]
        face = nodes[nodes[fin.fields["loop"]].fields["face"]]
        edge_id = attributes[(EDGE_DEFINITION, edge.fields["node_id"])][0]
        face_id = attributes[(FACE_DEFINITION, face.fields["node_id"])][0]
        linked[edge_id][face_id] += 1
        role = {"+": 0, "-": 1}[fin.fields["sense"]]
        assert role not in roles[edge_id]
        roles[edge_id][role] = face_id
    assert len(linked) == len(plan.incidence)
    for row in plan.incidence:
        assert attributes[(EDGE_DEFINITION, owners[row.edge])][0] == row.downstream_id
        assert tuple(attributes[(FACE_DEFINITION, owners[face])][0] for face in row.faces) == row.face_ids
        assert linked[row.downstream_id] == Counter(row.face_ids)
        assert tuple(sorted(roles[row.downstream_id].items())) == row.face_role_ids
    return sum(sum(count.values()) for count in linked.values())


def run(kind, variant):
    for encoding in ("utf-16-le", "utf-16-be", "cp1252", "utf-8"):
        lookup(encoding)
    second = 1818198000 + variant * 117
    ticks = 843165 * variant
    session = schedule(1739 + 103 * variant, 24, 1, 0, 3, 1, 1, second, ticks)
    name, topology, project = (prepare_prism if kind == "prism" else prepare_cylinder)(session, variant)
    owner = uuid5(NAMESPACE_URL, "urn:kit:solidworks:downstream:" + name)
    events = []
    active = True

    def guard(event, args):
        if active and event in ("open", "subprocess.Popen", "socket.connect"):
            events.append(event)
            raise RuntimeError("external operation during downstream cache input proof")

    addaudithook(guard)
    try:
        plan = prepare_part_cache_inputs(topology, owner, second, ticks)
        assert prepare_part_cache_inputs(tuple(reversed(topology)), owner, second, ticks) == plan
        by_ref = {node.ref: node for node in topology}
        reverse_first = tuple(
            replace(node, fields={**node.fields, "halfedge": by_ref[node.fields["halfedge"]].fields["other"]})
            if node.kind == 16 else node for node in topology
        )
        reversed_plan = prepare_part_cache_inputs(reverse_first, owner, second, ticks)
        assert reversed_plan.allocation == plan.allocation
        for current, reverse in zip(plan.incidence, reversed_plan.incidence, strict=True):
            assert current.face_ids == reverse.face_ids[::-1]
            assert current.face_role_ids == reverse.face_role_ids
        raw = frame_payloads(write_payloads(project(plan.allocation)))
        measured = read_partition(raw)
        assert frame_payloads(write_payloads(measured)) == raw
        assert frame_payloads(write_payloads(project(plan.allocation))) == raw
        incidence = assert_incidence(topology, plan, measured)
        assert incidence == 2 * len(plan.incidence)
        prefixes = {}
        for offset in (-480, 0, 330):
            prefix = initial_prefix(offset)
            calculated = pack("<8I", *(prefix[field] for field in PREFIX))
            independent = pack("<8I", 1, 19000, 2026306, 0, 0, 101, 101, 631152000 - offset * 60)
            assert calculated == independent
            prefixes[str(offset)] = prefix["f28"]

        fin = next(node for node in topology if node.kind == 17)
        loop = next(node for node in topology if node.kind == 15)
        attempts = {
            "self_linked_edge": replace(fin, fields={**fin.fields, "other": fin.ref}),
            "invalid_loop_owner": replace(loop, fields={**loop.fields, "face": fin.ref}),
            "invalid_backlink": replace(fin, fields={**fin.fields, "backward": 0}),
            "equal_fin_senses": replace(fin, fields={**fin.fields, "sense": by_ref[fin.fields["other"]].fields["sense"]}),
        }
        controls = {}
        for fault, substitute in attempts.items():
            altered = tuple(substitute if node.ref == substitute.ref else node for node in topology)
            try:
                prepare_part_cache_inputs(altered, owner, second, ticks)
            except ValueError as error:
                controls[fault] = str(error)
            else:
                raise AssertionError(f"accepted {fault}")
    finally:
        active = False
    print(dumps({
        "passed": True, "profile": kind, "variant": variant,
        "face_allocations": len(plan.allocation.faces), "edge_allocations": len(plan.allocation.edges),
        "independent_incidence_checks": incidence,
        "independent_left_right_checks": incidence, "reversed_first_fin_checks": len(plan.incidence),
        "next_id": plan.allocation.next_id, "constructor_time_words": prefixes,
        "partition_bytes": len(raw), "partition_sha256": sha256(raw).hexdigest(),
        "negative_refusals": controls, "runtime_io_attempts": len(events),
        "native_runs": 0, "cache_emitted": False,
    }, sort_keys=True, indent=2))


def main():
    parser = ArgumentParser()
    parser.add_argument("profile", choices=("prism", "cylinder"))
    parser.add_argument("variant", type=int, choices=(1, 2))
    values = parser.parse_args()
    run(values.profile, values.variant)


if __name__ == "__main__":
    main()
