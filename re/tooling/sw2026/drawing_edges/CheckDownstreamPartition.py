from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from json import dumps
from struct import pack
from sys import addaudithook
from uuid import NAMESPACE_URL, uuid5

from FreshCylinderInput import make_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from para.DownstreamIds import EDGE_DEFINITION, FACE_DEFINITION, allocate_fresh_downstream, owned_solid_chains
from para.Partition import frame_payloads, read_partition, write_payloads
from para.cylinder.CylinderTopology import generated_cylinder
from para.cylinder.ProjectCylinder import project_cylinder
from para.rectangle.Allocate import Ref, allocate_marks
from para.rectangle.CheckProjection import control, schedule
from para.rectangle.Geometry import plan_rectangle
from para.rectangle.RectangleAttributes import Appearance
from para.rectangle.RectanglePartition import complete_topology, project_rectangle


def prepare_prism(session, variant):
    name = f"DownstreamPrism{variant}"
    limits = (2.375 * variant, -7.125, 32.25 + variant, 11.875, 6.25 + 1.75 * variant)
    child = control(name, limits, (0, 1, 2, 3), dimensioned=True)
    plan = plan_rectangle(child, session)
    appearance = Appearance((113, 54, 192), 0.125, None)
    topology, _ = complete_topology(plan.topology)

    def project(allocation):
        return project_rectangle(child, plan, appearance, downstream=allocation).partition

    return name, topology, project


def prepare_cylinder(session, variant):
    name = f"DownstreamCylinder{variant}"
    document = make_document({
        "name": name, "axis": "z", "plane": "Front Plane",
        "center_mm": (2.25 * variant, -6.75), "radius_mm": 2.625 + variant,
        "depth_mm": 14.5 + 3.25 * variant, "driver": "diameter", "reversed": False,
    })
    GetDocumentCaps(document)
    candidate = PrepareNative(document, BytesIO(), session.update_second, WriteOptions(
        values={"final_destination": f"C:\\KitResearch\\{name}.SLDPRT"},
    ))
    draft = generated_cylinder(candidate, allocate_marks(session))
    topology, _ = complete_topology(draft.nodes)

    def project(allocation):
        return project_cylinder(candidate, session, downstream=allocation).partition

    return name, topology, project


def inspect_attributes(partition):
    nodes = {node.index: node for node in partition.nodes}
    matching = {}
    for attribute in partition.nodes:
        if attribute.kind != 81:
            continue
        definition = nodes[attribute.fields["definition"]]
        name = nodes[definition.fields["identifier"]].fields["string"]
        if name not in (FACE_DEFINITION, EDGE_DEFINITION):
            continue
        owner = nodes[attribute.fields["owner"]]
        assert owner.kind == (14 if name == FACE_DEFINITION else 16)
        assert len(attribute.fields["fields"]) == 3
        first, second, third = attribute.fields["fields"]
        assert second == third == 0
        assert nodes[first].kind == 82
        key = (name, owner.fields["node_id"])
        assert key not in matching
        matching[key] = nodes[first].fields["values"]
    return matching


def number_words(owner):
    ordered = tuple(owner.encode("ascii"))
    modulus = 1_000_000_009
    high, low = tuple(
        sum(unit * pow(base, index, modulus) for index, unit in enumerate(ordered)) % modulus
        for base in (32771, 32779)
    )
    return high, low


def run(case, variant):
    from codecs import lookup
    for encoding in ("utf-16-le", "utf-16-be", "cp1252", "utf-8"):
        lookup(encoding)
    seconds = 1818198000 + variant * 117
    fraction = 843165 * variant
    session = schedule(1739 + 103 * variant, 24, 1, 0, 3, 1, 1, seconds, fraction)
    name, topology, project = (prepare_prism if case == "prism" else prepare_cylinder)(session, variant)
    owner = uuid5(NAMESPACE_URL, "urn:kit:solidworks:downstream:" + name)
    high, low = number_words(str(owner))
    filetime = (seconds + 11644473600) * 10_000_000 + fraction
    by_reference = {node.ref: node.fields["node_id"] for node in topology if node.kind in (14, 16)}
    attempts = []
    active = True

    def guard(event, values):
        if active and event in {"open", "subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect"}:
            attempts.append(event)
            raise RuntimeError("unexpected runtime operation: " + event)

    addaudithook(guard)
    try:
        faces, edges = owned_solid_chains(topology)
        assert owned_solid_chains(tuple(reversed(topology))) == (faces, edges)
        allocation = allocate_fresh_downstream(faces, edges, owner, seconds, fraction, is_assembly=False)
        baseline = frame_payloads(write_payloads(project(None)))
        emitted = project(allocation)
        raw = frame_payloads(write_payloads(emitted))
        assert frame_payloads(write_payloads(project(allocation))) == raw
        decoded = read_partition(raw)
        assert decoded == emitted and frame_payloads(write_payloads(decoded)) == raw
        actual = inspect_attributes(decoded)
        assert allocation.archive_owner_fields == (str(owner), high, low)
        assert allocation.next_id == len(faces) + len(edges) + 1
        typed_lookup = {
            (definition, by_reference[member.ref]): i
            for definition, members, start in ((FACE_DEFINITION, faces, 1), (EDGE_DEFINITION, edges, len(faces) + 1))
            for i, member in enumerate(members, start)
        }
        assert set(actual) == set(typed_lookup)
        for key, identifier in typed_lookup.items():
            assert pack("<6i", *actual[key]) == pack("<IQIQ", identifier, filetime, 0, (high << 32) | low)
        forged = replace(allocation, edges=((Ref("foreign-edge"), allocation.edges[0][1]), *allocation.edges[1:]))
        try:
            project(forged)
        except ValueError as error:
            assert str(error) == "downstream identities must follow the actual linked part topology and owner"
        else:
            raise AssertionError("unowned downstream edge was written")
        reordered = replace(allocation, edges=tuple(reversed(allocation.edges)))
        try:
            project(reordered)
        except ValueError as error:
            assert str(error) == "downstream identities must follow the actual linked part topology and owner"
        else:
            raise AssertionError("downstream edge table ignored the topology order")
        bad_edge = replace(edges[-1], fields={**edges[-1].fields, "next": edges[0].ref})
        bad_topology = tuple(bad_edge if node.ref == bad_edge.ref else node for node in topology)
        try:
            owned_solid_chains(bad_topology)
        except ValueError as error:
            assert str(error) == "downstream topology chain has an invalid or foreign member"
        else:
            raise AssertionError("cyclic topology was admitted")
    finally:
        active = False
    assert not attempts
    return {
        "case": case, "variant": variant, "neutral_shape_name": name,
        "owner_guid": str(owner), "owner_hash": allocation.key, "filetime": filetime,
        "face_count": len(faces), "edge_count": len(edges), "next_id": allocation.next_id,
        "edge_node_ids": [by_reference[edge.ref] for edge in edges],
        "allocated_edge_ids": [identifier for _, identifier in allocation.edges],
        "partition_bytes": len(raw), "partition_sha256": sha256(raw).hexdigest(),
        "baseline_sha256": sha256(baseline).hexdigest(),
        "same_process_repeat_exact": True, "active_and_rollback_round_trip_exact": True,
        "independent_word_comparisons": len(actual),
        "rejected_foreign_edge": True, "rejected_cyclic_chain": True, "rejected_reordered_edge_table": True,
        "independent_of_topology_storage_order": True,
        "runtime_io_attempts": len(attempts), "native_launches": 0,
        "scope": "generated single-body partition using explicit linked topology",
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("shape", choices=("prism", "cylinder"))
    parser.add_argument("variant", type=int, choices=(1, 2))
    args = parser.parse_args()
    print(dumps(run(args.shape, args.variant), indent=2, sort_keys=True))
