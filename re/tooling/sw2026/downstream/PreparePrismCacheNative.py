from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from json import dumps
from pathlib import Path, PureWindowsPath
from sys import addaudithook

from Classes import registry
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from downstream.CheckCollectorProjection import collector_body
from downstream.CheckPrismFaceConstructors import authored_prism
from downstream.Components import read_component_body, write_component_body
from downstream.EdgeRegistration import fresh_edge_registration
from downstream.FaceRegistration import fresh_face_registration
from downstream.PrismEdgeConstructors import prism_edge_constructor_fields
from downstream.Storage import ConfigurationCache, cache_path, store_part_caches
from para.Partition import read_partition
from para.Tracking import filetime_ticks


def candidate_streams(archive, allocation, clock):
    partition = read_partition(archive.require(KPartitionStream))
    fields, _ = prism_edge_constructor_fields(archive, allocation, special_id_map_present=False)
    if clock <= allocation.updated:
        raise ValueError("cache construction event must follow the generated model allocation")
    faces = fresh_face_registration(partition, allocation, fields, clock)
    edges = fresh_edge_registration(partition, allocation, fields, clock)
    graph = collector_body(fields | {"f340": faces, "f380": edges})
    return store_part_caches(archive.streams, (ConfigurationCache(0, True, False, True, graph, False),))


def main():
    parser = ArgumentParser()
    parser.add_argument("--variant", type=int, choices=(1, 2), required=True)
    parser.add_argument("--part-path", type=PureWindowsPath, required=True)
    parser.add_argument("--model-second", type=int, required=True)
    parser.add_argument("--later-body-updates", type=int, choices=(0, 1), default=1)
    parser.add_argument("--record-saved-body-count", action="store_true")
    parser.add_argument("--record-rebuild-completion", action="store_true")
    parser.add_argument("--artifact", type=Path, required=True)
    projection = parser.add_mutually_exclusive_group()
    projection.add_argument("--include-cache", action="store_true")
    projection.add_argument("--omit-downstream-allocation", action="store_true")
    args = parser.parse_args()
    for codec in ("utf-8", "utf-16le", "utf-16be", "latin-1", "cp1252"):
        lookup(codec)
    classes = registry()
    blocked = []
    active = True

    def guard(event, arguments):
        if active and event in ("open", "subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect"):
            blocked.append(event)
            raise RuntimeError("native prism preparation attempted runtime operation: " + event)

    addaudithook(guard)
    try:
        owner, archive, allocation = authored_prism(args.variant, classes, model_path=args.part_path,
                                                   model_second=args.model_second,
                                                   allocate_downstream=not args.omit_downstream_allocation,
                                                   later_body_updates=args.later_body_updates,
                                                   record_saved_body_count=args.record_saved_body_count,
                                                   record_rebuild_completion=args.record_rebuild_completion)
        clock = filetime_ticks(args.model_second + 1, 0)
        streams = candidate_streams(archive, allocation, clock) if args.include_cache else archive.streams
        output = BuildSldprt(streams, FormatVersion=4)
        resolved = SldprtArchive.from_bytes(output)
        assert resolved.streams == streams
        assert all(resolved.require(key) == value for key, value in archive.streams.items())
        path = cache_path(0)
        if args.include_cache:
            payload = resolved.require(path)
            cache, _ = read_component_body(payload)
            assert write_component_body(cache)[0] == payload
            assert len(cache.FieldsValue["f40"]) == len(cache.FieldsValue["f48"]) == len(cache.FieldsValue["f340"]) == 6
            assert len(cache.FieldsValue["f60"]) == len(cache.FieldsValue["f380"]) == 12
            assert cache.FieldsValue["f78"] == cache.FieldsValue["f90"] == []
        else:
            assert path not in resolved.streams
    finally:
        active = False
    with args.artifact.open("xb") as stream:
        stream.write(output)
    print(dumps({
        "variant": args.variant, "generated_part_sha256": sha256(output).hexdigest(), "cache_included": args.include_cache,
        "cache_sha256": sha256(resolved.require(path)).hexdigest() if args.include_cache else None,
        "scope": "disclosed generated ordinary prism part for native cache consumption probe",
        "model_path": str(owner), "stream_count": len(resolved.streams), "runtime_io_attempts": len(blocked),
        "model_second": args.model_second, "kernel_filetime": allocation.updated if allocation is not None else None,
        "cache_filetime": clock if args.include_cache else None, "heldout_inputs_read": 0,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
