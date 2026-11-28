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
from downstream.CheckFaceOperands import read_operands
from downstream.CheckPrismFaceConstructors import authored_prism
from downstream.Components import read_component_body, write_component_body
from downstream.FaceRegistration import fresh_face_registration
from downstream.PrismFaceStore import prism_face_store_fields
from downstream.Storage import ConfigurationCache, cache_path, store_part_caches
from para.Partition import read_partition
from para.Tracking import filetime_ticks
from para.concentric.CylinderFace import words


def read_identity_rows(cache, table="f340"):
    return [
        (entry["key"], *(entry["object"].FieldsValue[k] for k in ("f08", "f0c", "f10", "high", "low")))
        for entry in cache.FieldsValue[table]
    ]


def main():
    parser = ArgumentParser()
    parser.add_argument("variant", choices=(1, 2), type=int)
    args = parser.parse_args()
    for codec in ("utf-8", "utf-16le", "utf-16be", "latin-1", "cp1252"):
        lookup(codec)
    classes = registry()
    attempted = []
    active = True

    def guard(event, arguments):
        if active and event in ("open", "subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect"):
            attempted.append(event)
            raise RuntimeError("face registration performed runtime operation: " + event)

    addaudithook(guard)
    try:
        _, archive, allocation = authored_prism(args.variant, classes)
        fields, _ = prism_face_store_fields(archive, allocation, special_id_map_present=False)
        partition = read_partition(archive.require(KPartitionStream))
        epoch = filetime_ticks(1820018000 + 31 * args.variant, 3864305)
        registration = fresh_face_registration(partition, allocation, fields, epoch)
        witness = collector_body(fields | {"f340": registration})
        raw = write_component_body(witness)[0]
        streams = store_part_caches(archive.streams, (ConfigurationCache(0, True, False, True, witness, False),))
        output = BuildSldprt(streams, FormatVersion=4)
        result = SldprtArchive.from_bytes(output)
        assert result.streams == streams and all(result.require(name) == data for name, data in archive.streams.items())
        decoded, mapping = read_component_body(result.require(cache_path(0)))
        assert write_component_body(decoded)[0] == raw

        actual, _ = read_operands(partition)
        node_ids = {item.index: item.fields["node_id"] for item in partition.nodes if item.kind == 14}
        nodes = {item.index: item for item in partition.nodes}
        body, = (item for item in partition.nodes if item.kind == 12)
        actual_atom, = words(nodes, body, "ATOM_ID_2001", 1)
        time_high, time_low = unpack(">II", pack(">Q", epoch))
        expected = [
            (identifier, index, actual_atom, native_id, time_high, time_low)
            for index, (identifier, native_id) in enumerate(sorted((value, node_ids[key]) for key, value in actual.items()))
        ]
        assert read_identity_rows(decoded) == expected
        assert decoded.FieldsValue["f380"] == [] and epoch != allocation.updated

        changed = fresh_face_registration(partition, allocation, fields, epoch + 1)
        revised = read_identity_rows(collector_body(fields | {"f340": changed}))
        assert all(left[:-1] == right[:-1] and left[-1] + 1 == right[-1]
                   for left, right in zip(expected, revised, strict=True))
    finally:
        active = False
    print(dumps({
        "passed": True, "variant": args.variant, "native_runs": 0, "runtime_io_attempts": len(attempted),
        "cache_filetime": epoch, "allocation_filetime": allocation.updated, "face_identity_rows": expected,
        "map_counter": mapping.CounterValue, "cache_sha256": sha256(raw).hexdigest(),
        "container_sha256": sha256(output).hexdigest(), "scope": "generated face lookup table and separate cache clock",
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
