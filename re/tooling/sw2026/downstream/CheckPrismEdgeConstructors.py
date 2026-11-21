from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from json import dumps
from operator import attrgetter
from sys import addaudithook

from Classes import registry
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from downstream.CheckCollectorProjection import collector_body
from downstream.CheckPrismFaceConstructors import authored_prism
from downstream.CheckPrismFaceStore import check_collected_surfaces, partition_keys
from downstream.Components import read_component_body, write_component_body
from downstream.EdgeOperands import prism_edge_operands
from downstream.FaceRegistration import fresh_face_registration
from downstream.PrismEdgeConstructors import prism_edge_constructor_fields, prism_edge_keys
from downstream.Storage import ConfigurationCache, cache_path, store_part_caches
from para.DownstreamIds import owned_solid_chains
from para.Partition import read_partition
from para.Tracking import filetime_ticks
from para.concentric.CylinderFace import words


def partition_edge_roles(partition, allocation):
    nodes = {item.index: item for item in partition.nodes}
    faces, edges = owned_solid_chains(partition.nodes, identity=attrgetter("index"))
    face_ids = {face.index: number for face, (_, number) in zip(faces, allocation.faces, strict=True)}
    vertex_faces = {}
    edge_fins = {}
    for fin in (item for item in nodes.values() if item.kind == 17):
        face = nodes[fin.fields["loop"]].fields["face"]
        edge_fins.setdefault(fin.fields["edge"], {})[fin.fields["sense"]] = (fin, face)
        vertex_faces.setdefault(fin.fields["vertex"], set()).add(face)
    rows = []
    for edge, (_, number) in zip(edges, allocation.edges, strict=True):
        positive, left = edge_fins[edge.index]["+"]
        negative, right = edge_fins[edge.index]["-"]
        start, = vertex_faces[negative.fields["vertex"]] - {left, right}
        end, = vertex_faces[positive.fields["vertex"]] - {left, right}
        assert {left, right} <= vertex_faces[negative.fields["vertex"]]
        assert {left, right} <= vertex_faces[positive.fields["vertex"]]
        rows.append((number, edge.fields["node_id"], tuple(face_ids[face] for face in (left, right, start, end))))
    return tuple(rows)


def kernel_edge_keys(roles, descriptions):
    expected = []
    for number, _, faces in roles:
        left, right, start, end = (descriptions[face] for face in faces)
        candidates = ("s," + left + right + start + end, "s," + right + left + end + start)
        hashes = [
            sum(byte * pow(32771, index, 1_000_000_009) for index, byte in enumerate(text.encode("ascii")))
            % 1_000_000_009
            for text in candidates
        ]
        expected.append((number, *hashes))
    return tuple(expected)


def check_retained_rows(decoded, expected, atom):
    fields = decoded.FieldsValue
    surfaces = {
        row["word"]: row["object"].FieldsValue["fe8"].FieldsValue["f10"][0]["f08"]
        for row in fields["f48"]
    }
    units = [row["object"].FieldsValue["f58"] for row in fields["f48"]]
    zero_point = dict.fromkeys(("x", "y", "z"), 0.0)
    for row, (number, _, roles) in zip(fields["f60"], expected, strict=True):
        edge = row["object"]
        assert edge.ClassValue.NameValue == "moCompEdge_c" and row["word"] == number
        outer = edge.FieldsValue
        units.append(outer["f58"])
        assert (outer["f18"], outer["f1c"], outer["f68"], outer["f188"], outer["f18c"]) == (atom, atom, 0, 0, 0)
        assert outer["f158"] == outer["f170"] == zero_point and outer["f130"] == []
        reference = outer["fe8"]
        assert reference.ClassValue.NameValue == "moEdgeRef_c"
        data = reference.FieldsValue
        assert (data["f08"], data["f60"], data["f64"], data["fe8"], data["f70"]) == (4, 1, 0, 0x300, 0)
        assert (data["f28"], data["f30"], data["f40"], data["nd0"]) == (1e100, 1e100, None, 0)
        embedded = data["f18"]
        assert [(entry["key"], entry["value"]) for entry in embedded["f10"]] == list(enumerate(roles))
        assert (embedded["f20"], embedded["f38"], embedded["f40_0"], embedded["f40_1"]) == ([], 0, 0, 0)
        assert all(slot["f08"] is surfaces[face] for slot, face in zip(data["f10"], roles, strict=True))
    assert len({id(unit) for unit in units}) == len(units)


def check_collisions(row):
    component = row["object"]
    reference = component.FieldsValue["fe8"]
    slots = reference.FieldsValue["f10"]
    opposite = ArchiveNode(reference.ClassValue, reference.FieldsValue | {"f10": [slots[i] for i in (1, 0, 3, 2)]})
    revised = row | {"object": ArchiveNode(component.ClassValue, component.FieldsValue | {"fe8": opposite})}
    for candidate in (row, revised):
        try:
            prism_edge_keys((row, candidate))
        except ValueError as error:
            assert "noncollision" in str(error)
        else:
            raise AssertionError("edge store accepted an earlier original or anti key")


def main():
    parser = ArgumentParser()
    parser.add_argument("variant", choices=(1, 2), type=int)
    args = parser.parse_args()
    for codec in ("utf-8", "utf-16le", "utf-16be", "latin-1", "cp1252"):
        lookup(codec)
    classes = registry()
    attempts = []
    active = True

    def guard(event, arguments):
        if active and event in ("open", "subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect"):
            attempts.append(event)
            raise RuntimeError("edge constructor performed runtime operation: " + event)

    addaudithook(guard)
    try:
        _, archive, allocation = authored_prism(args.variant, classes)
        partition = read_partition(archive.require(KPartitionStream))
        fields, keys = prism_edge_constructor_fields(archive, allocation, special_id_map_present=False)
        receipt_roles = partition_edge_roles(partition, allocation)
        descriptions, _ = partition_keys(archive)
        expected_keys = kernel_edge_keys(receipt_roles, descriptions)
        assert tuple((key.row_id, key.original, key.anti) for key in keys) == expected_keys
        check_collisions(fields["f60"][0])
        permuted = replace(partition, nodes=tuple(reversed(partition.nodes)))
        assert prism_edge_operands(permuted, allocation, fields["f28"], special_id_map_present=False) == (
            prism_edge_operands(partition, allocation, fields["f28"], special_id_map_present=False)
        )

        construction_clock = filetime_ticks(1820018000 + 31 * args.variant, 3864305)
        f340 = fresh_face_registration(partition, allocation, fields, construction_clock)
        witness = collector_body(fields | {"f340": f340})
        raw, encoded_map = write_component_body(witness)
        streams = store_part_caches(archive.streams, (ConfigurationCache(0, True, False, True, witness, False),))
        output = BuildSldprt(streams, FormatVersion=4)
        readback = SldprtArchive.from_bytes(output)
        assert readback.streams == streams and readback.require(cache_path(0)) == raw
        assert all(readback.require(name) == values for name, values in archive.streams.items())
        decoded, mapping = read_component_body(readback.require(cache_path(0)))
        assert write_component_body(decoded)[0] == raw and mapping.CounterValue == encoded_map.CounterValue
        assert prism_edge_keys(decoded.FieldsValue["f60"]) == keys
        assert decoded.FieldsValue["f380"] == decoded.FieldsValue["f78"] == []
        assert check_collected_surfaces(decoded, descriptions) == 30
        nodes = {item.index: item for item in partition.nodes}
        body, = (item for item in nodes.values() if item.kind == 12)
        atom, = words(nodes, body, "ATOM_ID_2001", 1)
        check_retained_rows(decoded, receipt_roles, atom)
    finally:
        active = False
    print(dumps({
        "passed": True, "variant": args.variant, "atom": atom, "native_runs": 0,
        "scope": "ordinary prism mode-one edge rows after no-collision insertion, before the late pass",
        "edge_roles": receipt_roles, "edge_keys": expected_keys, "anti_or_original_collision_refusals": 2,
        "collector_backed_edge_slots": sum(len(row[2]) for row in receipt_roles),
        "face_lookup_rows": len(f340), "map_counter": mapping.CounterValue, "runtime_io_attempts": len(attempts),
        "preserved_part_streams": len(archive.streams), "body_sha256": sha256(raw).hexdigest(),
        "container_sha256": sha256(output).hexdigest(),
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
