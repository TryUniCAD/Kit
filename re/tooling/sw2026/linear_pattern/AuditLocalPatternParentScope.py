from argparse import ArgumentParser
from pathlib import Path
from struct import unpack
import json
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent), str(HERE.parents[1]), str(HERE.parents[1] / "serial")]

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KResolvedFeaturesStream
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import ReadSingleNode

from CheckPatternAngleOwners import node_fields, require
from PatternAngleWire import read_resolved
from ProvePatternAngleArc import span_report
from ProvePatternPlaneDirectionRule import Image, MODULES, checked, digest, encode, module


FIRST_FREEZE = "103912a8dd5d983866d5d66c848f08d954372d0ebef9d9c53a5781fa9fffc9c5"
SECOND_FREEZE = "b04e279af46524b69a3198c50e2ba06a89702327be1885eb5e2283d82f2d84a3"
NATIVE_RESULT = "b20cc4286fb26d034b17bf241ea4289e4327031dbadf7fc7cfc1a8c8a3010a41"
FIRST_PACKET = "2228f783fe1847fc390284b7fa72bb96968e948f7e5895e553242dff66b39bcb"
API_DLL = "97bc3d859637c8b420108a1a3ebd4262580fa45d05c761874df7658fad49b6c2"
CASES = ("ColdRaisedPatternA", "ColdRaisedPatternB")
SPANS = {
    "api_parent_dispatch": (0x4BB45E90, 0x4BB45EC9, "2bdde71c8c8873e4f169781e7ab5e3e90d7b4eba8312f32b728ec6d0044a855c"),
    "linear_parent_override": (0x4BFD42C0, 0x4BFD4413, "7e60b99998cf07ccec3a85c0f66b9e341829308eb50de944ef87bd68289ea0d4"),
    "inherited_parent_enumeration": (0x4C053080, 0x4C0534DD, "8867d675831d0359e78c17f24baf3f367e369481795c3259fa9ed56686234fb3"),
    "f9f0_parent_scope_gate": (0x4C05320C, 0x4C0532B5, "6488930d163676e4ef1555f4a862f6b57cdfd51c107fb345b0faa800a896c7c9"),
    "direct_seed_enumeration": (0x4C053355, 0x4C053415, "d4af04129e223ac9a739b6f466950942c44710f2240e9019dd8b9be7f2094dca"),
    "second_seed_enumeration": (0x4C0571A0, 0x4C0573DD, "ea9ed89ff34cce7b6bad80fe7d3be305b474f6ec4e3bceb8ffe09df45357a8f9"),
    "scope_wrapper_local_features": (0x4B7F9030, 0x4B7F928E, "8bdcf43531a7c0f29ee0801bbb7e44a96b1042b3cd2eb5fc2c2efbfb4729bdd3"),
    "direction_wrapper_local_features": (0x4C317C40, 0x4C317F46, "5a624dad79fb1f85bbe8d7755db04e25501d967c1b4513f9e2a8379109edb0ba"),
}
VIRTUALS = {
    "linear_parent_override": (0x4D0BC0A0, 0x13B0, 0x4BFD42C0),
    "second_seed_enumeration": (0x4D0BC0A0, 0x13B8, 0x4C0571A0),
    "inherited_parent_enumeration": (0x4D0CBAA0, 0x13B0, 0x4C053080),
    "scope_wrapper_local_features": (0x4CE93810, 0xA8, 0x4B7F9030),
    "direction_wrapper_local_features": (0x4CE5CD20, 0x250, 0x4C317C40),
}


def authority(binaries):
    api, model = (Image(binaries / name) for name in ("sldapiu.dll", "sldmodu.dll"))
    identities = [module(api, API_DLL), module(model, MODULES["sldmodu.dll"])]
    imported = api.imports[0x4302A3D8]
    require(imported["module"].lower() == "sldmodu.dll"
            and imported["symbol"] == "?getParents@moFeature_c@@QEBAXAEAVsuObList@@@Z",
            "native 2026 API imports changed the directly observed parent surface")
    slots = {}
    for name, (table, slot, target) in VIRTUALS.items():
        require(unpack("<Q", model.bytes(table + slot, table + slot + 8))[0] == target,
                "expected exact-build local parent enumeration dispatch")
        slots[name] = {"vtable": hex(table), "slot": hex(slot), "target": hex(target)}
    return {"modules": identities, "api_parent_import": {"slot": "0x4302a3d8", **imported},
            "routines": span_report(model, SPANS), "virtual_dispatch": slots}


def parse_pattern(archive):
    header = ReadHeaderGraph(archive.Require("Contents/Config-0-ModelHeader"), 19000)
    config = ReadConfigMut(archive.Require("Contents/Config-0"), 19000, header)
    context = MakeLinkContext(config, ReadCmgrMut(archive.Require("Contents/CMgr"), 19000))
    roots, tail, mapping = read_resolved(archive.Require(KResolvedFeaturesStream), config.MapValue, context)
    require(tail is None and len(roots) == 24, "unexpected generated layout or protected input")
    pattern = roots[-1]
    fields = node_fields(pattern, "moLPattern_c")
    selector = ReadSingleNode(fields["f548"], "moCompSolidBody_c").FieldsValue
    previous = ReadSingleNode(fields["f530"], "moAtom_c")
    require(fields["f948"] == 0 and fields["f544"] == 1 and fields["f1054"] == 0
            and fields["has_f548"] == 1 and fields["f988"].FieldsValue["items"][0]["o"] is roots[-4]
            and selector["f18"] == selector["f1c"] == previous.FieldsValue["f140"]
            and selector["ff0"] is None and selector["f108"] == roots[-6].FieldsValue["f08"],
            "cold selector variant changed the ordinary actual feature and body ownership")
    return {"f9f0": fields["f9f0"], "scope_f544": fields["f544"], "base_feature_f108": selector["f108"],
            "selected_atom_f18": selector["f18"], "body_lineage_f110": [row["v"] for row in selector["f110"]],
            "resolved_object_span": [pattern.StartOffset, pattern.EndOffset],
            "resolved_map_frontier": mapping.CounterValue}


def check_native(directory, baseline):
    report = json.loads(checked(directory / "Result.json", NATIVE_RESULT))
    require(report["build"] == "34.5.2.0604" and report["packet_sha256"] == FIRST_PACKET
            and report["build_sha256"] == FIRST_FREEZE and report["heldout_cases"] == 0
            and report["distinct_processes"] == 4 and report["passed"] is False
            and set(report["controls"]) == {"before", "after"}
            and all(row["passed"] for row in report["controls"].values()),
            "first two-parent refusal is bounded by the exact installed build and passing controls")
    rows = {}
    for name in CASES:
        job = f"{name}-edit"
        phase = report["phases"][job]
        observed = json.loads(checked(directory / f"{job}.json", phase["record_sha256"]))
        axis = baseline[name]["original"]["modeled_input"]
        wanted = [axis["seed"]["seed"]["feature"], axis["plane"]["name"]]
        actual = [axis["seed"]["plate"]["feature"], *wanted]
        calls = observed["api_calls"]
        parents = [row["result"] for row in calls[-3:]]
        require(phase["passed"] is False and phase["numeric_checks"] == 33
                and phase["open"] == {"opened": True, "error": 0, "warning": 0}
                and phase["first_failure"]["error"] == "EvidenceFailure('pattern dependency owners differ')"
                and calls[-4]["method"] == "GetParents" and len(calls[-4]["result"]) == 3
                and all(call["method"] == "Name" for call in calls[-3:]) and parents == actual,
                "initial refusal differs from the exact additional plate parent")
        rows[name] = {"record_sha256": phase["record_sha256"], "old_reported_parents": actual,
                      "expected_direct_parents": wanted, "native_open": phase["open"],
                      "cold_geometry": phase["cold_geometry"], "numeric_checks": phase["numeric_checks"]}
    return {"result_sha256": NATIVE_RESULT, "packet_sha256": FIRST_PACKET, "controls": report["controls"], "cases": rows}


def compare(name, old_directory, new_directory, old, new):
    for key in ("input_sha256", "modeled_input", "independent_cell_measure", "observed", "map_counters"):
        require(old[key] == new[key], "archive contrast changed modeled source semantics or selected physical owners")
    require(old["guarded_runtime_reads"] == new["guarded_runtime_reads"] == 0, "unexpected runtime source reads")
    archives = tuple(SldprtArchive.FromBytes(checked(directory / f"{name}.SLDPRT", case["native_container"]["sha256"]))
                     for directory, case in ((old_directory, old), (new_directory, new)))
    first, second = (archive.Streams for archive in archives)
    require(first.keys() == second.keys() and [key for key in first if first[key] != second[key]] == [KResolvedFeaturesStream],
            "startup parent contrast modified an unrelated stream")
    a, b = [data[KResolvedFeaturesStream] for data in (first, second)]
    changes = [index for index, (x, y) in enumerate(zip(a, b, strict=True)) if x != y]
    original, corrected = map(parse_pattern, archives)
    require(len(changes) == 1 and a[changes[0]] == 0 and b[changes[0]] == 1
            and original["f9f0"] == 0 and corrected["f9f0"] == 1
            and original == {**corrected, "f9f0": 0}
            and original["resolved_object_span"][0] <= changes[0] < original["resolved_object_span"][1],
            "startup parent contrast did not isolate the single typed pattern bit")
    return {"old_candidate": old["native_container"], "new_candidate": new["native_container"],
            "stream": KResolvedFeaturesStream, "derived_field": "moLPattern_c.f9f0", "stream_changed_bytes": len(changes),
            "stream_offset": changes[0], "old_value": 0, "corrected_value": 1, "preserved_owners": corrected}


def main():
    parser = ArgumentParser()
    parser.add_argument("--initial", type=Path, required=True)
    parser.add_argument("--corrected", type=Path, required=True)
    parser.add_argument("--native-result", type=Path, required=True)
    parser.add_argument("--binaries", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    old = json.loads(checked(args.initial / "LocalLinearPatternContainer01.json", FIRST_FREEZE))
    new = json.loads(checked(args.corrected / "LocalLinearPatternContainer02.json", SECOND_FREEZE))
    require(old["warm_replay"] == new["warm_replay"]
            and all(row["warm_scope_and_visual_application"] == [1, 1] for row in old["warm_replay"].values())
            and old["guarded_processes"] == new["guarded_processes"] == 10,
            "fixed probe requires the same disclosed cases, authority and guarded process coverage")
    old, new = old["model_cases"], new["model_cases"]
    result = {
        "schema": "kit.sw2026.local-linear-pattern-parent-scope.v1", "build": "34.5.2.0604", "heldout_cases": 0,
        "baseline_manifest_sha256": FIRST_FREEZE, "corrected_manifest_sha256": SECOND_FREEZE,
        "constructor_tool_sha256": digest((HERE.parent / "MakeLocalPattern.py").read_bytes()),
        "audit_tool_sha256": digest(HERE.read_bytes()), "first_native_failure": check_native(args.native_result, old),
        "static_authority": authority(args.binaries),
        "typed_contrasts": {name: compare(name, args.initial / "Candidates", args.corrected / "Candidates",
                                          old[name]["original"], new[name]["original"]) for name in CASES},
        "corrected_native_acceptance": None,
    }
    with args.output.open("xb") as target:
        target.write(encode(result))
    print(digest(args.output.read_bytes()))


if __name__ == "__main__":
    main()
