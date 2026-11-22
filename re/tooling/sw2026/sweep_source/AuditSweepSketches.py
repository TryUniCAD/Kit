from argparse import ArgumentParser
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from AuditSweepArchive import SDK_TREE, SOURCE_LOCK, check_sdk, checked, digest, guard_runtime, load_disclosed
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import ReadPrismFrame
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimHandle import ReadDimHandle
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from MakeSweepSketchPart import make_sketch_part
from MakeSweepSketches import need_radii
from SweepArchiveLayout import observe
from SweepArchiveOwners import arc_positions, driver, sketch_relations
from SweepModel import PATH, SECTION, dimensions, require, validate_spec


SPEC = "e62d1d09ac26cc0ae9538a846b0800023441403b5d04ac432a8f6b1da8e71023"
EPOCH = 1794000000


def inspect_sketches(link, section_radius, path_radius):
    by_id = {NativeNodeId(node): node for node in link.ResolvedValue.RootsValue}
    profiles = [node for node in by_id.values() if ReadNativeName(node) in (SECTION, PATH)]
    section, path = profiles
    require(ReadNativeName(section) == SECTION and ReadNativeName(path) == PATH
            and section.EndOffset <= path.StartOffset, "sweep sketch history order differs")
    rows = []
    for node, radius, is_section in ((section, section_radius, True), (path, path_radius, False)):
        name = ReadNativeName(node)
        sketch = node.FieldsValue["pd_f80"]
        frame = ReadPrismFrame(node, link.ConfigValue.RootValue, by_id, FrontOnly=False)
        support = by_id[node.FieldsValue["pd_f78"].FieldsValue["ff0"]["f00"]]
        support_name = "Right Plane" if is_section else "Front Plane"
        require(sketch.FieldsValue.get("f138", node) is node and ReadNativeName(support) == support_name
                and (frame.origin.x, frame.origin.y, frame.origin.z) == (0, 0, 0)
                and (frame.z_axis.x, frame.z_axis.y, frame.z_axis.z) == ((1, 0, 0) if is_section else (0, 0, 1)),
                "sketch lost its actual profile backlink or canonical support")
        value, dim, param, view, handle = driver(
            sketch, {"value_m": 2 * radius if is_section else radius, "name": f"D1@{name}",
                     "display_kind": 6 if is_section else 5, "driven": 2, "read_only": False}, is_section,
        )
        geometry = arc_positions(sketch.FieldsValue, radius, is_section)
        geometry.pop("section_seam_angle_rad")
        if is_section:
            geometry.pop("start_m")
            geometry.pop("end_m")
        row = {"name": name, "id": NativeNodeId(node), "support": support_name, "value_metres": value,
               "dimension_id": dim.FieldsValue["f50"], "driver_slots": [part.IndexValue for part in (dim, param, view, handle)],
               "geometry": geometry, "logical_relations": sketch_relations(sketch.FieldsValue, is_section)}
        if not is_section:
            p = [value["point"] for value in sketch.FieldsValue["points"]]
            arc = sketch.FieldsValue["arcs"][0]["arc"]
            require([item["f0c"] for item in p] == [3, 1, 2] and [item["f20"] for item in p] == [2, 2, 1]
                    and [item["fe8"] for item in p] == [1, 1, 1] and [item["fec"] for item in p] == [1, 0, 0]
                    and all(item["h2"] is None for item in p) and p[0]["h1"] is None
                    and all(ReadDimHandle(item["h1"], "sgArcHandle") == 0 for item in p[1:])
                    and arc["fd0"] == 1 and arc["f20"] == 1 and p[1]["h1"] is not p[2]["h1"],
                    "actual Front point permanence, adjacency or participation differs")
            row.update(points=[{"permanence": item["f0c"], "relations": item["f20"],
                                "uses": item["fe8"], "centres": item["fec"]} for item in p],
                       ordinary_arc_state={key: arc[key] for key in ("f30", "f34", "f54")},
                       sketch_state={key: sketch.FieldsValue[key] for key in ("f12c", "f578")})
        rows.append(row)
    require(len({row["dimension_id"] for row in rows}) == 2, "sweep drivers reused an identifier")
    return rows


def map_shape(snapshot):
    return snapshot.CounterValue, tuple(
        (entry.IndexValue, type(entry.EntryValue),
         entry.EntryValue.ClassValue if isinstance(entry.EntryValue, ArchiveNode) else entry.EntryValue)
        for entry in snapshot.EntriesValue
    )


def generated(case, density, edit):
    radii = dimensions(case, edit)
    name = case["name"] + "Sketches"
    raw, streams, cfg, resolved = make_sketch_part(name, *radii, density, EPOCH)
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    actual = inspect_sketches(link, *radii)
    require(len(link.ResolvedValue.RootsValue) == 19 and map_shape(link.ConfigValue.MapValue) == map_shape(cfg.MapValue)
            and map_shape(link.ResolvedValue.MapValue) == map_shape(resolved.MapValue) and archive.streams == streams,
            "fresh model has unexpected roots, maps or streams")
    again, replay_map = WriteConfigMut(link.ConfigValue.RootValue, 19000, link.ConfigValue.HeaderValue)
    replay, finished = WriteResolMut(link.ResolvedValue.RootsValue, link.ResolvedValue.ExtraFields, 19000,
                                     replay_map.MapValue, link.ResolvedValue.ContextValue)
    require(again == streams[link.ConfigName] and replay == streams[link.StreamName]
            and replay_map.MapValue == link.ConfigValue.MapValue and finished.MapValue == link.ResolvedValue.MapValue
            and make_sketch_part(name, *radii, density, EPOCH)[0] == raw, "fresh sketch graph changed on re-emission")
    return {"name": name, "state": edit or "original", "bytes": len(raw), "sha256": digest(raw),
            "stream_sha256": {key: digest(value) for key, value in streams.items()},
            "exact_map_counts": [cfg.MapValue.CounterValue, resolved.MapValue.CounterValue], "profiles": actual}


def inspect_disclosed(sources, intent):
    rows = []
    for slot, role, raw, phases in sources:
        radii = dimensions(intent[slot], role if role != "original" else None)
        require((phases["section"]["value_m"], phases["path"]["value_m"]) == (2 * radii[0], radii[1]),
                "independent exact author values differ")
        with observe("linked"):
            link = ReadNativeLink(SldprtArchive.from_bytes(raw), 0)
        rows.append({"slot": slot + 1, "state": role, "sha256": digest(raw), "profiles": inspect_sketches(link, *radii)})
    return rows


def contrasts():
    cases = {"unchanged or reversed clearance": (0.04, 0.04), "negative": (-0.003, 0.01),
             "nonfinite": (0.004, float("inf")), "outside archive profile": (0.004, 0.16),
             "Boolean radius": (True, 0.04)}
    refused = {}
    for label, values in cases.items():
        try:
            need_radii(*values)
        except ValueError as error:
            refused[label] = str(error)
        else:
            raise ValueError("outside profile reached sketch construction")
    return refused


def main():
    parser = ArgumentParser(description="Measure fresh typed sweep profiles or generate an isolated sketch-only candidate")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--model-only", action="store_true")
    modes.add_argument("--disclosed", type=Path)
    modes.add_argument("--emit", choices=("SweepArcNear", "SweepArcWide"))
    parser.add_argument("--locator")
    args = parser.parse_args()
    require(args.locator is None or args.emit is not None, "a logical path belongs to a single output")
    check_sdk()
    density, intent = validate_spec(json.loads(checked(HERE / "DisclosedSweepInputs.json", SPEC)))
    if args.disclosed:
        sources, _, _ = load_disclosed(args.disclosed)
    tools = {name: digest((HERE / name).read_bytes()) for name in (
        "AuditSweepSketches.py", "MakeSweepSketchPart.py", "MakeSweepSketches.py", "MakeSweepPathDim.py",
        "AuditSweepArchive.py", "SweepArchiveLayout.py", "SweepArchiveOwners.py", "SweepModel.py",
    )}
    blocked = guard_runtime()
    if args.emit:
        case, = (row for row in intent if row["name"] == args.emit)
        raw = make_sketch_part(case["name"] + "Sketches", *dimensions(case), density, EPOCH, args.locator)[0]
        require(not blocked, "fresh sketch output attempted external access")
        sys.stdout.buffer.write(raw)
        return
    rows = [generated(case, density, edit) for case in intent for edit in (None, "section", "path")]
    for original, section, path in (rows[:3], rows[3:]):
        require(original["profiles"][0] == path["profiles"][0] and original["profiles"][1] == section["profiles"][1]
                and original["profiles"][0]["value_metres"] != section["profiles"][0]["value_metres"]
                and original["profiles"][1]["value_metres"] != path["profiles"][1]["value_metres"],
                "independent modeled edit changed the other owner's readback")
    witness = inspect_disclosed(sources, intent) if args.disclosed else []
    require(not blocked, "sweep sketch proof attempted external access after custody")
    result = {"schema": "kit.sw2026.ordinary-sweep-sketches.v1", "sdk_tree": SDK_TREE, "epoch": EPOCH,
              "intent_sha256": SPEC, "tool_sha256": tools, "blocked_runtime_calls": len(blocked),
              "native_source_lock_sha256": SOURCE_LOCK if witness else None, "source_witness_sketches": witness,
              "fresh_sketch_only_parts": rows, "input_refusals": contrasts(), "native_processes_started": 0,
              "heldout_inputs_read": 0, "whole_sweep_candidates": 0}
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
