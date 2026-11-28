from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from json import dumps
from struct import pack, unpack
from sys import addaudithook

from Classes import registry
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from downstream.CheckCollectorProjection import collector_body
from downstream.CheckEdgeRegistrationOrder import native_order
from downstream.CheckFaceRegistration import read_identity_rows
from downstream.CheckPrismEdgeConstructors import check_retained_rows, partition_edge_roles
from downstream.CheckPrismFaceConstructors import authored_prism
from downstream.Components import read_component_body, write_component_body
from downstream.EdgeRegistration import fresh_edge_registration
from downstream.FaceRegistration import fresh_face_registration
from downstream.PrismEdgeConstructors import prism_edge_constructor_fields
from downstream.Storage import ConfigurationCache, cache_path, store_part_caches
from para.Partition import read_partition
from para.Tracking import filetime_ticks
from para.concentric.CylinderFace import words


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
            raise RuntimeError("prism cache registration performed runtime operation: " + event)

    addaudithook(guard)
    try:
        _, archive, allocation = authored_prism(args.variant, classes)
        partition = read_partition(archive.require(KPartitionStream))
        fields, _ = prism_edge_constructor_fields(archive, allocation, special_id_map_present=False)
        clock = filetime_ticks(1820018000 + 31 * args.variant, 3864305)
        face_rows = fresh_face_registration(partition, allocation, fields, clock)
        edge_rows = fresh_edge_registration(partition, allocation, fields, clock)
        witness = collector_body(fields | {"f340": face_rows, "f380": edge_rows})
        raw, encoded_map = write_component_body(witness)
        streams = store_part_caches(archive.streams, (ConfigurationCache(0, True, False, True, witness, False),))
        output = BuildSldprt(streams, FormatVersion=4)
        restored = SldprtArchive.from_bytes(output)
        assert restored.streams == streams and restored.require(cache_path(0)) == raw
        assert all(restored.require(name) == values for name, values in archive.streams.items())
        decoded, mapping = read_component_body(restored.require(cache_path(0)))
        assert write_component_body(decoded)[0] == raw and mapping.CounterValue == encoded_map.CounterValue

        roles = partition_edge_roles(partition, allocation)
        ids = native_order([number for number, _, _ in roles], "i32")
        assert ids["final_bucket_count"] == 64 and ids["serialized_key_order"] == [row["key"] for row in edge_rows]
        nodes = {item.index: item for item in partition.nodes}
        body, = (item for item in nodes.values() if item.kind == 12)
        atom, = words(nodes, body, "ATOM_ID_2001", 1)
        high, low = unpack(">II", pack(">Q", clock))
        expected = [(number, ordinal, atom, node, high, low)
                    for ordinal, (number, node, _) in enumerate(roles)]
        assert read_identity_rows(decoded, "f380") == expected
        assert [row[-2:] for row in read_identity_rows(decoded)] == [(high, low)] * 6
        check_retained_rows(decoded, roles, atom)
        next_tick = fresh_edge_registration(partition, allocation, fields, clock + 1)
        revised = read_identity_rows(collector_body(fields | {"f380": next_tick}), "f380")
        assert all(left[:-1] == right[:-1] and left[-1] + 1 == right[-1]
                   for left, right in zip(expected, revised, strict=True))
    finally:
        active = False
    print(dumps({
        "passed": True, "variant": args.variant, "native_runs": 0, "runtime_io_attempts": len(attempts),
        "scope": "ordinary prism retained face and edge rows with registered identities, before the late pass",
        "cache_filetime": clock, "allocation_filetime": allocation.updated, "edge_lookup_rows": expected,
        "edge_lookup_bucket_count": ids["final_bucket_count"], "final_buckets": ids["final_buckets_in_store_order"],
        "map_counter": mapping.CounterValue, "cache_sha256": sha256(raw).hexdigest(),
        "container_sha256": sha256(output).hexdigest(), "preserved_part_streams": len(archive.streams),
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
