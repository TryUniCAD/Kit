from argparse import ArgumentParser
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from AuditSweepArchive import SDK_TREE, check_sdk, checked, digest, guard_runtime, refusal
from AuditSweepSketches import EPOCH, SPEC, inspect_sketches, map_shape
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
from MakeColdSweepPart import make_cold_sweep_part
from SweepArchiveLayout import SIDE, SWEEP, observe
from SweepArchiveOwners import checked_profiles, one
from SweepGhostGraph import GHOST_STREAM, component_roles, manager_rows, read_ghost
from SweepModel import PATH, SECTION, dimensions, require, validate_spec
from SweepReplay import sweep_replay


def inspect_curve_owners(link, sweep, radii):
    section, path = ReadParents(sweep)
    require([ReadNativeName(node) for node in (section, path)] == [SECTION, PATH],
            "sweep inputs are not its actual ordered profiles")
    nodes = {NativeNodeId(node): node for node in link.ResolvedValue.RootsValue}
    header = link.ConfigValue.HeaderValue.FieldsValue
    data = sweep.FieldsValue["f820"]
    section_curve, path_curve = one(data["f2c0"]), one(data["f2e0"]).FieldsValue["fe8"]
    require(section_curve.FieldsValue["f08"] == header["f40"] and section_curve.FieldsValue["f68"] == 1
            and path_curve.FieldsValue["f68"] == 0 and path_curve.FieldsValue["f0c"] == -1
            and path_curve.FieldsValue["f08"] == 101, "fresh section cache or unresolved path last-access state differs")
    profiles = {}
    for role, node, curve, radius, mode, is_section in (
        ("section", section, section_curve, radii[0], 6, True),
        ("path", path, path_curve, radii[1], 5, False),
    ):
        observation = {"name": f"D1@{ReadNativeName(node)}", "value_m": 2 * radius if is_section else radius,
                       "display_kind": mode, "driven": 2, "read_only": False}
        profiles[role] = checked_profiles(link, nodes, curve, node, observation, is_section)
    return profiles, component_roles(link, sweep, section, path)


def inspect_output(raw, streams, config, resolved, radii):
    archive = SldprtArchive.from_bytes(raw)
    baseline = refusal(archive, "baseline", SWEEP)
    with observe("cold"):
        link = ReadNativeLink(archive, 0)
    cfg, history = link.ConfigValue, link.ResolvedValue
    sweep = history.RootsValue[-1]
    require(sweep.ClassValue.NameValue == SWEEP and len(history.RootsValue) == 20
            and archive.streams == streams and len(streams) == 11
            and map_shape(cfg.MapValue) == map_shape(config.MapValue)
            and map_shape(history.MapValue) == map_shape(resolved.MapValue),
            "cold part did not preserve actual stream or map ownership")
    require(history.ExtraFields is None and "Contents/Config-0-Partition" not in streams
            and not any(sweep.FieldsValue[name] for name in ("n494", "has_f528", "has_f548", "has_f4a8", "has_f4c0", "has_f3d0"))
            and cfg.RootValue.FieldsValue["fd88"]["n6c"] == 0
            and all(getattr(getattr(entry.EntryValue, "ClassValue", None), "NameValue", None) != SIDE
                    for entry in history.MapValue.EntriesValue), "cold experiment includes a stored result")
    profiles, refs = inspect_curve_owners(link, sweep, radii)
    sketch_observation = inspect_sketches(link, *radii)
    require(refs["section"]["general_secondary"] == 0, "sole active configuration has an alternate index")
    manager = manager_rows(cfg.RootValue, sweep, refs)
    ghost = read_ghost(archive, refs, profiles)
    config_bytes, config_replay = WriteConfigMut(cfg.RootValue, 19000, cfg.HeaderValue)
    with sweep_replay(cold=True):
        resolved_bytes, replay = WriteResolMut(history.RootsValue, history.ExtraFields, 19000, config_replay.MapValue,
                                               history.ContextValue)
    require(config_bytes == streams[link.ConfigName] and resolved_bytes == streams[link.StreamName]
            and config_replay.MapValue == cfg.MapValue and replay.MapValue == history.MapValue,
            "complete cold configuration or resolved bytes differ on typed re-emission")
    return {"candidate_bytes": len(raw), "candidate_sha256": digest(raw), "stream_sha256": {
        name: digest(data) for name, data in streams.items()
    }, "exact_stream_replays": [link.ConfigName, link.StreamName, GHOST_STREAM], "standard_reader_refusal": baseline,
        "map_counts": [cfg.MapValue.CounterValue, history.MapValue.CounterValue],
        "section_transport": profiles["section"]["embedded_body"], "ghost_partition": ghost, "references": refs,
        "ghost_manager": manager, "sketches": sketch_observation,
        "fresh_scope": {"f28": sweep.FieldsValue["f28"], "f544": sweep.FieldsValue["f544"],
                        "f2b4": sweep.FieldsValue["f820"]["f2b4"], "f2b8": sweep.FieldsValue["f820"]["f2b8"]},
    }


def generate(case, density, edit=None, locator=None):
    radii = dimensions(case, edit)
    inputs = (case["name"], *radii, density, EPOCH, locator)
    part = make_cold_sweep_part(*inputs)
    require(part[0] == make_cold_sweep_part(*inputs)[0], "model-only cold part construction is not deterministic")
    return part[0], inspect_output(*part, radii)


def main():
    parser = ArgumentParser(description="Measure or emit the unqualified cold Standard-sweep candidate")
    parser.add_argument("--emit", choices=("SweepArcNear", "SweepArcWide"))
    parser.add_argument("--locator")
    args = parser.parse_args()
    require((args.emit is not None) == (args.locator is not None), "single emission requires an explicit guest self locator")
    check_sdk()
    density, cases = validate_spec(json.loads(checked(HERE / "DisclosedSweepInputs.json", SPEC)))
    tools = {name: digest((HERE / name).read_bytes()) for name in (
        "AuditColdSweep.py", "SweepArchiveLayout.py", "SweepReplay.py", "MakeColdSweepPart.py",
        "MakeSweepCurveRefs.py", "SweepColdMembers.py", "MakeSweepSketchPart.py", "MakeSweepSketches.py",
        "MakeSweepPathDim.py", "MakeSweepGhostPair.py", "SweepSectionTransport.py", "SweepGhostGraph.py",
    )}
    blocked = guard_runtime()
    if args.emit:
        case, = (value for value in cases if value["name"] == args.emit)
        raw, _ = generate(case, density, locator=args.locator)
        require(not blocked, "model-only sweep accessed a runtime asset")
        sys.stdout.buffer.write(raw)
        return
    results = [{"name": case["name"], "state": edit or "original", **generate(case, density, edit)[1]}
               for case in cases for edit in (None, "section", "path")]
    for original, section, path in (results[:3], results[3:]):
        require(original["sketches"][0] == path["sketches"][0] and original["sketches"][1] == section["sketches"][1]
                and original["section_transport"]["transmit_sha256"] == path["section_transport"]["transmit_sha256"]
                != section["section_transport"]["transmit_sha256"]
                and len({case["candidate_sha256"] for case in (original, section, path)}) == 3,
                "cold shapes did not respond independently to each declared driver")
    require(not blocked, "model-only sweep accessed a runtime asset")
    print(json.dumps({"schema": "kit.sw2026.fresh-cold-sweep.v1", "sdk_tree": SDK_TREE, "epoch": EPOCH,
                      "intent_sha256": SPEC, "tool_sha256": tools, "cases": results, "blocked_runtime_calls": len(blocked),
                      "native_processes_started": 0, "native_qualified": False, "heldout_inputs_read": 0,
                      "production_registration": False}, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
