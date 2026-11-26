from argparse import ArgumentParser
from importlib import import_module
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
sys.path[:0] = [str(HERE.parents[3] / "src"), str(HERE.parent)]

from CfgFinishTags import birth_offsets, map_checkpoint
from CheckCfgFinish import exact_role, native_archive, native_inputs
from FinishSdkPin import pinned_config
from TraceCfgFinish import REVISION, ROLES, capture, guard_runtime, source
from convert.adapters.solidworks.Archive.Config.Link.ReadPartStart import ReadPartStart
from convert.adapters.solidworks.Archive.Header.HeaderRefNodes import HeaderRefNodes

require = source.require


def trace_live_case(case, data):
    with pinned_config():
        reader = import_module(source.ARCHIVE + "Config.ReadConfigMut").ReadConfigMut
        header_reader = import_module(source.ARCHIVE + "Header.ReadNativeHeader").ReadHeaderGraph
        body = import_module(source.ARCHIVE + "Bodies.ReadBodyMut")
        external = guard_runtime()
        archive, config, header_bytes = native_archive(case, data)
        seed = ReadPartStart(archive)
        (seed_alias,) = HeaderRefNodes(seed.HeaderValue, 19000)
        header = header_reader(header_bytes, 19000)
        (linked_header,) = HeaderRefNodes(header, 19000)
        prefix = [entry.IndexValue for entry in seed.MapValue.EntriesValue]
        require(prefix == [1, 2, 3] and seed.BaseValue == 4 and seed_alias.ClassValue == linked_header.ClassValue,
                "current SDK did not recover the native part and header prefix")

        checkpoints, checks, offsets = [], [], []

        def replay(role, rows, part, maps):
            require(part.ClassValue == seed.RootValue.ClassValue and part.IndexValue == seed.RootValue.IndexValue
                    and maps.EntryMap[3].EntryValue is linked_header, "finish helper received a foreign native prefix")
            checkpoints.append(map_checkpoint(role, maps))
            checks.extend(exact_role(role, rows, config, part, maps))
            offsets.append(birth_offsets(maps))

        native_rows, terminal = capture(reader, body, config, 19000, header, linked_header, replay)
        require(native_rows == case["rows"] and terminal == case["config_next_slot"],
                "live physical boundaries differ from the pinned receipt")
        require([row["role"] for row in checkpoints] == list(ROLES) and not external,
                "bounded native verification missed a checkpoint or used external data")
        require(offsets[0] == offsets[1] == offsets[2], "object-birth tags differ among live checkpoints")
        return {"runtime_external_accesses": len(external), "prefix_anchors": prefix,
                "native_checkpoints": checkpoints, "exact_intervals": checks}, offsets[0]


if __name__ == "__main__":
    parser = ArgumentParser(description="Trace live Config-0 finish maps from the pinned aggregate SDK")
    parser.add_argument("case", choices=("ladder", "concave"))
    parser.add_argument("--tag-offsets", action="store_true")
    args = parser.parse_args()
    case, data = native_inputs(args.case)
    native, offsets = trace_live_case(case, data)
    report = {"case": args.case, "native_source": case["file_sha256"], "trace_revision": REVISION} | native
    print(json.dumps(offsets if args.tag_offsets else report, sort_keys=True, allow_nan=False))
