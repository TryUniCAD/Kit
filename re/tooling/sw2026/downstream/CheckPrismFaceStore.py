from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from json import dumps
from sys import addaudithook

from Classes import registry
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from downstream.CheckCollectedSurfaceClones import surface_owner
from downstream.CheckCollectorProjection import collector_body
from downstream.CheckFaceOperands import read_operands
from downstream.CheckPrismFaceConstructors import authored_prism, check_graph
from downstream.Components import read_component_body, write_component_body
from downstream.PrismFaceStore import ordinary_surface_description, prism_face_keys, prism_face_store_fields
from downstream.Storage import ConfigurationCache, cache_path, store_part_caches
from para.Partition import read_partition
from para.concentric.CylinderFace import words


def partition_keys(archive):
    partition = read_partition(archive.require(KPartitionStream))
    identifiers, related = read_operands(partition)
    nodes = {item.index: item for item in partition.nodes}
    descriptions = {
        number: ",".join(str(word) for word in words(nodes, nodes[index], "FACE_ID_2001", 2))
        for index, number in identifiers.items()
    }
    keys = []
    for number, (neighbors, _) in sorted(related.items()):
        real_faces = neighbors[:-1]
        alternate = tuple(real_faces[i] for i in (0, 2, 1, 3, 4))
        encoded = (
            ("s," + "".join(descriptions[face] for face in order)).encode("ascii")
            for order in (real_faces, alternate)
        )
        hashes = tuple(sum(byte * pow(32771, i, 1_000_000_009) for i, byte in enumerate(data)) % 1_000_000_009
                       for data in encoded)
        keys.append((number, *hashes))
    return descriptions, tuple(keys)


def swapped_copy(row):
    new = row["object"]
    original = new.FieldsValue["fe8"]
    slots = original.FieldsValue["f10"]
    alternate = [slots[i] for i in (0, 2, 1, 3, 4, 5)]
    ref = ArchiveNode(original.ClassValue, original.FieldsValue | {"f10": alternate})
    return row | {"object": ArchiveNode(new.ClassValue, new.FieldsValue | {"fe8": ref})}


def check_collected_surfaces(decoded, descriptions):
    fields = decoded.FieldsValue
    reps = tuple(member["object"] for member in fields["f40"])
    assert [ordinary_surface_description(rep) for rep in reps] == [descriptions[key] for key in sorted(descriptions)]
    assert len(reps) == 6
    owners = tuple(surface_owner(rep) for rep in reps)
    assert len({id(owner) for owner in owners}) == 6
    assert all(owner.FieldsValue["f78"] == -1 and owner.FieldsValue["f60"] == 0 for owner in owners)
    for handle in ("h10", "h18"):
        assert len({id(owner.FieldsValue["shared"][handle]) for owner in owners}) == 1
    by_description = dict(zip(map(ordinary_surface_description, reps), reps, strict=True))
    shared_slots = 0
    for row in fields["f48"]:
        reference = row["object"].FieldsValue["fe8"].FieldsValue
        for slot in reference["f10"]:
            representation = slot["f08"]
            if representation is not None:
                assert representation is by_description[ordinary_surface_description(representation)]
                shared_slots += 1
    return shared_slots


def main():
    cli = ArgumentParser()
    cli.add_argument("variant", type=int, choices=(1, 2))
    args = cli.parse_args()
    for codec in ("utf-8", "utf-16le", "utf-16be", "latin-1", "cp1252"):
        lookup(codec)
    classes = registry()
    attempted = []
    active = True

    def guard(event, arguments):
        if active and event in ("open", "subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect"):
            attempted.append(event)
            raise RuntimeError("face store performed runtime operation: " + event)

    addaudithook(guard)
    try:
        path, archive, allocation = authored_prism(args.variant, classes)
        fields, keys = prism_face_store_fields(archive, allocation, special_id_map_present=False)
        available, expected = partition_keys(archive)
        assert tuple((key.row_id, key.original, key.swapped) for key in keys) == expected

        graph = collector_body(fields)
        raw, serialized_map = write_component_body(graph)
        streams = store_part_caches(archive.streams, (ConfigurationCache(0, True, False, True, graph, False),))
        output = BuildSldprt(streams, FormatVersion=4)
        readback = SldprtArchive.from_bytes(output)
        assert readback.streams == streams and readback.require(cache_path(0)) == raw
        assert all(readback.require(name) == values for name, values in archive.streams.items())
        decoded, mapped = read_component_body(raw)
        assert write_component_body(decoded)[0] == raw and serialized_map.CounterValue == mapped.CounterValue
        assert prism_face_keys(decoded.FieldsValue["f48"]) == keys
        atom, rows, reps = check_graph(decoded, archive, path)
        shared_slots = check_collected_surfaces(decoded, available)
        original = fields["f48"][0]
        refused = 0
        for copy in (original, swapped_copy(original)):
            try:
                prism_face_keys((original, copy))
            except ValueError:
                refused += 1
            else:
                raise AssertionError("face store accepted an earlier original or alternate-key collision")
    finally:
        active = False
    print(dumps({
        "passed": True, "variant": args.variant, "atom": atom, "native_runs": 0,
        "scope": "generated prism collector and face rows in the scoped no-collision path",
        "rows": rows, "surface_slots": reps, "collector_members": len(available), "collision_refusals": refused,
        "collector_backed_slots": shared_slots,
        "map_counter": mapped.CounterValue, "preserved_part_streams": len(archive.streams),
        "keys": expected, "body_sha256": sha256(raw).hexdigest(), "part_sha256": sha256(output).hexdigest(),
        "runtime_io_attempts": len(attempted),
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
