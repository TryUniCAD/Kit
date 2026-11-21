from argparse import ArgumentParser
from importlib import import_module
from io import BytesIO
import json
from pathlib import Path
from struct import unpack_from
from subprocess import check_output
import sys
from tarfile import open as tar_open
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent))

from CfgMasterInputs import ROOT, SCAN, digest, disclosed, fingerprint, guard_runtime, require


def map_state(frame):
    maps = frame.ReaderValue.MapValue
    return maps.BaseValue, maps.Snapshot()


def state_record(base, snapshot):
    slots = []
    for entry in snapshot.EntriesValue:
        stored = entry.EntryValue
        descriptor = getattr(stored, "ClassValue", stored)
        kind = "node" if descriptor is not stored else "class"
        slots.append([entry.IndexValue, kind, descriptor.NameValue, descriptor.SchemaValue])
    return {
        "base": base,
        "counter": snapshot.CounterValue,
        "entries": len(slots),
        "slot_shapes_sha256": fingerprint(slots),
        "first_entries": slots[:3],
    }


def trace(sdk, name):
    sys.path.insert(0, str(sdk))
    from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Container.Archive import ContainerMo
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    row, _, header, config = disclosed(name, SldprtArchive, ContainerMo)
    module = import_module("convert.adapters.solidworks.Archive.Bodies.Reading.ReadFieldsMut")
    execute = module.KReadActions["DirectNode"]
    observations = []

    def observe(frame, rule):
        if rule.NameValue != "f1018":
            return execute(frame, rule)
        start = frame.ReaderValue.Cursor.GetOffset()
        flags = dict(frame.ContextValue.FlagsValue)
        before = map_state(frame)
        execute(frame, rule)
        end = frame.ReaderValue.Cursor.GetOffset()
        base, after = map_state(frame)
        same = base == before[0] and all(
            original is written for original, written in
            zip(before[1].EntriesValue, after.EntriesValue, strict=True)
        )
        require(same and before[1] == after, "master changed physical archive ownership")
        node = frame.ScopeValue.FieldsValue["f1018"]
        require(node.IndexValue is None and id(node) not in frame.ReaderValue.MapValue.ObjectLookup,
                "direct master acquired a map slot")
        require(frame.ReaderValue.MapValue.EntryMap[2].EntryValue is frame.NodeValue,
                "f1018 did not belong to the physical part at slot 2")
        observations.append({
            "interval": [start, end],
            "map": state_record(base, after),
            "map_entry_identities_unchanged": same,
            "class": [node.ClassValue.NameValue, node.ClassValue.SchemaValue],
            "part_slot": frame.NodeValue.IndexValue,
            "object_slot": node.IndexValue,
            "flags": flags,
            "schema_path": list(frame.ContextValue.UsageValue.SchemaPath),
            "wire_sha256": digest(config[start:end]),
            "fields_sha256": fingerprint(node.FieldsValue),
            "f1014": unpack_from("<i", config, start - 4)[0],
            "n370": unpack_from("<i", config, end - 4)[0],
        })

    module.KReadActions = {**module.KReadActions, "DirectNode": observe}
    external = guard_runtime()
    graph = ReadConfigMut(config, 19000, ReadHeaderGraph(header, 19000))
    require(not external, "pinned typed traversal attempted runtime external access")
    require(graph.RootValue.FieldsValue["f1014"] == (1 if name == "circle" else 0),
            "physical direct owner flag changed")
    if name == "circle":
        prior = row["separate_direct_owner"]
        start, base, counter = prior["start"]
        end, _, _ = prior["end"]
        (actual,) = observations
        require(
            actual["interval"] == [start, end]
            and (actual["map"]["base"], actual["map"]["counter"]) == (base, counter)
            and actual["wire_sha256"] == prior["wire_sha256"]
            and actual["flags"] == {"ctx87c": 0} and actual["n370"] == 0,
            "physical master no longer matches the disclosed ordinary mode",
        )
    else:
        require(not observations and "f1018" not in graph.RootValue.FieldsValue,
                "an absent owner consumed a direct body")
    return {
        "config_bytes": len(config),
        "final_counter": graph.MapValue.CounterValue,
        "runtime_external_accesses": len(external),
        "f1014": graph.RootValue.FieldsValue["f1014"],
        "direct_owner": observations[0] if observations else None,
    }


def scratch_trace():
    with TemporaryDirectory(prefix="KitCfgMaster") as temp:
        source = check_output(("git", "archive", SCAN, "src"), cwd=ROOT)
        with tar_open(fileobj=BytesIO(source)) as archive:
            archive.extractall(temp, filter="data")
        sdk = Path(temp) / "src"
        return {
            "reader_revision": SCAN,
            "controls": {
                name: json.loads(check_output(
                    (sys.executable, "-I", "-B", str(Path(__file__).resolve()),
                     "--worker-sdk", str(sdk), "--case", name)
                ))
                for name in ("circle", "ladder", "concave")
            },
        }


if __name__ == "__main__":
    parser = ArgumentParser(description="Trace the disclosed part at the exact aggregate reader pin")
    parser.add_argument("--worker-sdk", type=Path)
    parser.add_argument("--case", choices=("circle", "ladder", "concave"))
    args = parser.parse_args()
    result = trace(args.worker_sdk, args.case) if args.worker_sdk else scratch_trace()
    print(json.dumps(result, sort_keys=True))
