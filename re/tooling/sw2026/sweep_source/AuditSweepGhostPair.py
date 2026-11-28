from argparse import ArgumentParser
import json
from pathlib import Path
from struct import pack, unpack
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from AuditSweepArchive import SDK_TREE, check_sdk, checked, digest, guard_runtime
from AuditSweepConstructors import BRIDGE, MODULES, Image
from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.FieldScope import FieldScope
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ConfigLayouts import KConfigLayouts
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteFieldsMut import WriteFieldsMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteSchemaMut import WriteSchemaMut
from convert.adapters.solidworks.Archive.Construction.Model.MakeModelSeeds import MakeModelSeeds
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import FeatureTarget
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import InitFeatureMut
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from MakeSweepGhostPair import MODEL, SWEEP, make_sweep_ghost_pair
from SweepGhostGraph import BODY_KEY, EDGE_KEY, inspect_ghost
from SweepModel import dimensions, require, validate_spec


SPEC_DIGEST = "e62d1d09ac26cc0ae9538a846b0800023441403b5d04ac432a8f6b1da8e71023"
MANAGER_LAYOUT = "moGhostBodyIdManager_c.FUN_4bf050e0"
REGISTRATION = {
    BODY_KEY: (0x32f9ed9c, 0x32f9edc1, 0x330b81a0, 0x32f9edcf, 0x32f9eddb),
    EDGE_KEY: (0x32f9ef2e, 0x32f9ef5d, 0x330b8388, 0x32f9ef6b, 0x32f9ef77),
}


def registrations(directory):
    _, expected = MODULES[BRIDGE]
    image = Image(directory / BRIDGE, expected)
    results = {}
    for name, (start, literal, address, call, end) in REGISTRATION.items():
        raw = image.read(literal, literal + 7)
        branch = image.read(call, call + 5)
        spelling = (name + "\x00").encode("utf-16-le")
        require(raw[:3] == b"\x48\x8d\x15" and literal + 7 + unpack("<i", raw[3:])[0] == address
                and image.read(address, address + len(spelling)) == spelling
                and branch[0] == 0xe8 and call + 5 + unpack("<i", branch[1:])[0] == 0x32f9d010,
                "registered kernel attribute anchor differs")
        results[name] = {"first": hex(start), "end": hex(end), "sha256": digest(image.read(start, end)),
                         "definition_call": hex(call), "identifier_location": hex(address)}
    return {"module": BRIDGE, "sha256": expected, "registration": results, "native_execution": False}


def make_owner(next_id, name):
    root = ArchiveNode(MODEL, MakeModelSeeds())
    sweep = ArchiveNode(SWEEP, {})
    allocator = PersistentIds(next_id)
    InitFeatureMut(sweep, name, root, FeatureTarget(0, 3701250), allocator)
    require(sweep.FieldsValue["f08"] == next_id and allocator.NextValue == next_id + 1,
            "shared allocation did not deliver the actual sweep owner")
    return root, sweep


def manager_wire(pair, root, sweep):
    start_slot = 13
    writer = BodyWriter(ArchiveMaps(start_slot), BodyContext(19000, KConfigLayouts, {}, {}), WriteBodyMut)
    fields = dict(pair.manager)
    WriteSchemaMut(WriteFrame(writer, FieldScope(fields), root, WriteSchemaMut, WriteFieldsMut), MANAGER_LAYOUT)
    feature_id = sweep.FieldsValue["f08"]
    expected = pack("<iI", pair.path_id, (2 << 28) | 2)
    for owned_id in (pair.path_id, pair.section_id):
        expected += pack("<8i", owned_id, 8, 0, -1, 1, feature_id, 0, 0)
    require(writer.MapValue.CounterValue == start_slot and writer.OutputValue == expected and "n" not in pair.manager,
            "fresh typed ghost manager bytes, ownership or inherited map differ")
    return {"bytes": len(expected), "sha256": digest(expected), "unchanged_map_counter": start_slot}


def observe_pair(case, next_id):
    section, path = dimensions(case)
    root, sweep = make_owner(next_id, case["name"])
    pair = make_sweep_ghost_pair(root, sweep, section, path)
    require(pair == make_sweep_ghost_pair(root, sweep, section, path) and root.FieldsValue["fd90"] == MakeModelSeeds()["fd90"],
            "fresh ghost construction depends on a changed allocator or leaked mutable state")
    roles = {"section": {"ghost_id": pair.section_id}, "path": {"ghost_id": pair.path_id}}
    owners = {"section": {"driver": {"metres": 2 * section}}, "path": {"driver": {"metres": path},
              "arc": {"start_m": (0.0, 0.0, 0.0), "end_m": (path, path, 0.0), "center_m": (0.0, path, 0.0)}}}
    return {"input": case["name"], "sweep_id": sweep.FieldsValue["f08"], "section_ghost_id": pair.section_id,
            "path_ghost_id": pair.path_id, "ghost_stream_sha256": digest(pair.stream),
            "manager_wire": manager_wire(pair, root, sweep), "partition": inspect_ghost(pair.stream, roles, owners)}


def contrasts():
    root, sweep = make_owner(97, "ContrastingSweep")
    foreign, _ = make_owner(107, "ForeignSweep")
    invalid = ("split radii", "zero and Boolean", "alternate owner", "unallocated identity", "previous manager")
    cases = ((root, sweep, 0.024, 0.022), (root, sweep, True, 0.042), (foreign, sweep, 0.004, 0.033))
    _, incomplete = make_owner(43, "Unallocated")
    incomplete.FieldsValue.update(owner=root, f08=0)
    occupied, other = make_owner(61, "AlreadyAllocated")
    occupied.FieldsValue["fd90"]["n"] = 1
    cases += ((root, incomplete, 0.004, 0.033), (occupied, other, 0.004, 0.033))
    refused = {}
    for role, inputs in zip(invalid, cases, strict=True):
        try:
            make_sweep_ghost_pair(*inputs)
        except ValueError as error:
            refused[role] = str(error)
        else:
            raise ValueError("unsupported ghost input reached generated output")
    return refused


def main():
    parser = ArgumentParser(description="Measure the fresh two-ghost sweep partition or its exact registrations")
    options = parser.add_mutually_exclusive_group(required=True)
    options.add_argument("--model-only", action="store_true")
    options.add_argument("--emit", choices=("SweepArcNear", "SweepArcWide"))
    options.add_argument("--licensed-bin", type=Path)
    args = parser.parse_args()
    if args.licensed_bin:
        print(json.dumps(registrations(args.licensed_bin), sort_keys=True, indent=2))
        return
    check_sdk()
    _, cases = validate_spec(json.loads(checked(HERE / "DisclosedSweepInputs.json", SPEC_DIGEST)))
    tool_hashes = {name: digest((HERE / name).read_bytes()) for name in (
        "AuditSweepGhostPair.py", "MakeSweepGhostPair.py", "SweepGhostAttributes.py", "SweepGhostGraph.py",
        "SweepPathWire.py", "SweepSectionTransport.py", "SweepModel.py",
    )}
    blocked = guard_runtime()
    if args.emit:
        for index, case in enumerate(cases, 173):
            if case["name"] == args.emit:
                root, sweep = make_owner(index, case["name"])
                output = make_sweep_ghost_pair(root, sweep, *dimensions(case)).stream
                require(not blocked, "ghost input was read at runtime")
                sys.stdout.buffer.write(output)
                return
        raise ValueError("unavailable ghost candidate")
    result = [observe_pair(case, index) for index, case in enumerate(cases, 173)]
    require(len({row["ghost_stream_sha256"] for row in result}) == len(result), "neutral case did not affect ghost output")
    negatives = contrasts()
    require(not blocked, "ghost input was read at runtime")
    print(json.dumps({"schema": "kit.sw2026.fresh-sweep-ghost-pair.v1", "sdk_tree": SDK_TREE,
                      "disclosed_intent_sha256": SPEC_DIGEST, "tool_sha256": tool_hashes,
                      "cases": result, "input_refusals": negatives, "blocked_runtime_calls": len(blocked),
                      "full_native_part_outputs": 0, "heldout_cases": 0, "native_execution": False},
                     sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
