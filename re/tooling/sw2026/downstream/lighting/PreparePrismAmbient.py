from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from json import dumps, loads
from pathlib import Path, PureWindowsPath
from sys import addaudithook
import sys


ROOT = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(Path(__file__).resolve().parent)]
sys.path.extend((str(ROOT / "re/tooling/sw2026/serial"), str(ROOT / "re/tooling/sw2026")))

from Classes import registry
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from downstream.CheckPrismFaceConstructors import authored_prism
from downstream.Components import read_component_body, write_component_body
from downstream.PreparePrismCacheNative import candidate_streams
from downstream.Storage import cache_path
from para.Partition import read_partition
from para.Tracking import filetime_ticks
from para.concentric.CylinderFace import words
from downstream.lighting.PrismAmbientGraph import add_authored_ambient


def main():
    cli = ArgumentParser()
    cli.add_argument("root", type=Path)
    cli.add_argument("--variant", required=True, type=int, choices=(1, 2))
    cli.add_argument("--part-path", required=True, type=PureWindowsPath)
    cli.add_argument("--model-second", required=True, type=int)
    cli.add_argument("--later-body-updates", type=int, choices=(0, 1), default=0)
    cli.add_argument("--record-saved-body-count", action="store_true")
    cli.add_argument("--record-rebuild-completion", action="store_true")
    cli.add_argument("--include-cache", action="store_true")
    cli.add_argument("--with-authored-ambient", action="store_true")
    cli.add_argument("--specification", required=True, type=Path)
    cli.add_argument("--artifact", required=True, type=Path)
    args = cli.parse_args()
    specification_bytes = args.specification.read_bytes()
    specification = loads(specification_bytes)
    if args.artifact.exists():
        raise FileExistsError(args.artifact)
    for name in ("utf-8", "utf-16le", "utf-16be", "latin-1", "cp1252"):
        lookup(name)
    classes = registry()
    blocked = []
    active = True

    def guard(event, arguments):
        if active and event in ("open", "subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect"):
            blocked.append(event)
            raise RuntimeError("ambient prism construction attempted runtime operation: " + event)

    addaudithook(guard)
    try:
        owner, archive, allocation = authored_prism(
            args.variant, classes, model_path=args.part_path, model_second=args.model_second,
            allocate_downstream=True, later_body_updates=args.later_body_updates,
            record_saved_body_count=args.record_saved_body_count,
            record_rebuild_completion=args.record_rebuild_completion,
        )
        partition_bytes = archive.require(KPartitionStream)
        streams, evidence = add_authored_ambient(archive, specification, args.model_second, args.with_authored_ambient)
        modeled = SldprtArchive.from_bytes(BuildSldprt(streams, FormatVersion=4))
        clock = filetime_ticks(args.model_second + 1, 0)
        streams = candidate_streams(modeled, allocation, clock) if args.include_cache else modeled.streams
        output = BuildSldprt(streams, FormatVersion=4)
        restored = SldprtArchive.from_bytes(output)
        if restored.streams != streams or restored.require(KPartitionStream) != partition_bytes:
            raise ValueError("ambient graph composition changed generated partition bytes")
        linked = ReadNativeLink(restored, 0)
        members = linked.ConfigValue.RootValue.FieldsValue["f1e0"].FieldsValue["f60"]["list"]["items"]
        if len(members) != int(args.with_authored_ambient):
            raise ValueError("linked part lost the authored environment member")
        partition = read_partition(partition_bytes)
        body, = (value for value in partition.nodes if value.kind == 12)
        nodes = {value.index: value for value in partition.nodes}
        body_time, = words(nodes, body, "ENT_TIME_STAMP_2001", 1)
        header_time = linked.ConfigValue.HeaderValue.FieldsValue["f44"]
        if args.later_body_updates == 0 and body_time != header_time:
            raise ValueError("matching-clock variant did not retain body/header timestamp equality")
        cache_name = cache_path(0)
        cache_counts = None
        if args.include_cache:
            raw = restored.require(cache_name)
            cache, map_value = read_component_body(raw)
            if write_component_body(cache)[0] != raw:
                raise ValueError("complete downstream cache changed on typed replay")
            cache_counts = {key: len(cache.FieldsValue[key]) for key in ("f40", "f48", "f60", "f340", "f380", "f78", "f90")}
            if cache_counts != {"f40": 6, "f48": 6, "f60": 12, "f340": 6, "f380": 12, "f78": 0, "f90": 0}:
                raise ValueError("ordinary complete cache row ownership differs")
        elif cache_name in restored.streams:
            raise ValueError("cache-free lane acquired an unrequested downstream stream")
        evidence.update(variant=args.variant, model_path=str(owner), model_second=args.model_second,
                        body_stamp=body_time, header_body_stamp=header_time,
                        generated_part_sha256=sha256(output).hexdigest(), generated_bytes=len(output),
                        partition_sha256=sha256(partition_bytes).hexdigest(), cache_counts=cache_counts,
                        streams={name: {"bytes": len(value), "sha256": sha256(value).hexdigest()} for name, value in streams.items()},
                        source_specification_sha256=sha256(specification_bytes).hexdigest(),
                        runtime_io_attempts=len(blocked), heldout_inputs_read=0, native_acceptance=False,
                        native_execution=False, public_writer_qualified=False,
                        scope="generated matching-clock prism with independently authored optional ambient light")
    finally:
        active = False
    with args.artifact.open("xb") as destination:
        destination.write(output)
    print(dumps(evidence, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
