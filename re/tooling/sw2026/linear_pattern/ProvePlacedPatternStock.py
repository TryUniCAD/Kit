from argparse import ArgumentParser
from hashlib import sha256
from json import loads
from math import isclose
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(HERE.parent), str(ROOT / "src")]

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import ReadPrismFrame
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLinePoint import ReadLinePoint
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative

from CheckPatternAngleOwners import require
from MakePatternSeed import FrontBlindIntent, RaisedSeedIntent
from PatternAngleWire import read_resolved, write_resolved
from ProvePatternAngleOwners import exact_config
from ProvePatternPlaneDirectionRule import digest, encode
from ProvePatternSeed import MODEL_CASES, model


LOCK = "8239fc92779aadd6a0116ad2df9e7969568394a301e1ed11aa44fc3875ac0426"
PRIOR = "ca72e44d85d6f9284e18d45a4f9fea3301443b39af659ed01d5fffb8c793aa5f"
NATIVE = "LocalLinearPatternDatumPlacement01.json"
INVENTORY = ROOT / "re/solidworks/measurements/2026"


def pinned(path, expected):
    payload = path.read_bytes()
    require(sha256(payload).hexdigest() == expected, "bound input changed: " + path.name)
    return payload


def plan(case):
    name = case["name"]
    x0, y0 = case["plate_origin_m"]
    width, height = case["plate_size_m"]
    thickness = case["plate_depth_m"]
    x_offset, y_offset = case["seed_offset_m"]
    seed_width, seed_height = case["seed_size_m"]
    sx, sy = x0 + x_offset, y0 + y_offset
    upper = thickness + case["seed_extra_depth_m"]
    return RaisedSeedIntent(name, "Default", r"C:\KitPatternPlacedStock" + "\\" + name + ".SLDPRT",
                            1795259000,
                            FrontBlindIntent("PlateSketch", "PlateBoss",
                                             ((x0, y0, 0.0), (x0 + width, y0 + height, thickness))),
                            FrontBlindIntent("SeedSketch", "SeedBoss",
                                             ((sx, sy, 0.0), (sx + seed_width, sy + seed_height, upper))))


def compare_source(path, checksum, intent):
    archive, _, config, raw_config = exact_config(path, checksum)
    cmgr = ReadCmgrMut(archive.require("Contents/CMgr"), 19000)
    context = MakeLinkContext(config, cmgr)
    raw = archive.require("Contents/Config-0-ResolvedFeatures")
    roots, dormant, maps = read_resolved(raw, config.MapValue, context, source_replay=True)
    replay, replay_maps = write_resolved(roots, dormant, config.MapValue, context, source_replay=True)
    require(replay == raw and replay_maps == maps, "disclosed placed-stock archive has an unmodeled wire gap")
    link = NativeLink(config, ResolvedGraph(roots, dormant, maps, config.MapValue.CounterValue, 19000, context, {}),
                      "Config-0", "Config-0-ResolvedFeatures")
    indexed = {node.FieldsValue["f08"]: node for node in roots}
    operations = [node for node in roots if node.ClassValue.NameValue in ("moExtrusion_c", "moICE_c")]
    require(len(operations) == 2, "need the two actual joined stock operators")
    rows = []
    for index, (feature, expected) in enumerate(zip(operations, (intent.plate, intent.seed), strict=True)):
        typed = ReadExtrude(link, feature, indexed, NewSolid=index == 1)
        profile, = typed.ParentsValue
        frame = ReadPrismFrame(profile, config.RootValue, indexed)
        require((frame.origin.x, frame.origin.y, frame.origin.z) == (0.0, 0.0, 0.0)
                and (frame.z_axis.x, frame.z_axis.y, frame.z_axis.z) == (0.0, 0.0, 1.0),
                "disclosed profile lost its actual Front datum")
        sketch = RequireNative(profile.FieldsValue.get("pd_f80"), "sgSketch")
        point_rows = (ReadLinePoint(item, ordinal) for ordinal, item in enumerate(sketch.FieldsValue["points"]))
        points = {point.IndexValue: point for point in point_rows if point.CreationId > 0}
        require(len(points) == 4, "disclosed profile does not own four live corners")
        positions = {(item.PositionValue[0] * 0.001, item.PositionValue[1] * 0.001) for item in points.values()}
        x_values, y_values = {x for x, _ in positions}, {y for _, y in positions}
        require(len(x_values) == len(y_values) == 2 and positions == {(x, y) for x in x_values for y in y_values},
                "disclosed geometry does not own the four actual rectangular corners")
        live_depth = typed.RequireDepth().DepthValue
        measured = ((min(x_values), min(y_values), 0.0), (max(x_values), max(y_values), live_depth.native_value))
        require(live_depth.name == "D1" and typed.EndValue.FieldsValue["f128"] == 1
                and typed.EndValue.FieldsValue["f08"] == 1
                and all(isclose(value, target, abs_tol=1e-15, rel_tol=0.0)
                        for left, right in zip(measured, expected.bounds_m, strict=True)
                        for value, target in zip(left, right, strict=True)),
                "disclosed actual stock owners differ from the frozen authored model")
        rows.append({"feature_id": feature.FieldsValue["f08"], "profile_id": profile.FieldsValue["f08"],
                     "bounds_m": measured, "depth_owner": live_depth.TypedOwner})
    return {"source_sha256": checksum, "config_sha256": digest(raw_config),
            "resolved_sha256": digest(raw), "operations": rows}


def main():
    parser = ArgumentParser()
    parser.add_argument("--disclosed", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.disclosed
    lock = loads(pinned(source / "SourceLock.json", LOCK))
    require(lock["cohort"] == "disclosed" and lock["passed"] and lock["completed_native_phases"] == 14,
            "expected the original completed disclosed source controls")
    author_intents = loads(pinned(source / "FrozenInputs.json", lock["specs_sha256"]))
    require([case["name"] for case in author_intents["cases"]] == ["D01X", "D02Y"], "source plans changed")
    intended = {case["name"]: plan(case) for case in author_intents["cases"]}
    prior = loads(pinned(INVENTORY / "LocalLinearPatternRaisedSeedGraph01.json", PRIOR))
    unchanged = {}
    for control in MODEL_CASES:
        seen = model(control)
        require(seen["streams"] == prior["independent_model_cases"][control.name]["streams"],
                "origin-stock reference streams changed")
        unchanged[control.name] = seen["streams"]
    generated = {name: model(intent) for name, intent in intended.items()}
    rows = loads(pinned(INVENTORY / NATIVE, "827baa41493ed7fc459dcb5d7b4485a733494cf20fd4fb8d9ecb5aee4a70f566"))
    disclosed = {name: compare_source(source / name[:4] / name, row["sha256"], intended[name[:4]])
                 for name, row in rows["principal"].items()}
    require(len(disclosed) == 6 and len(generated) == 2, "incomplete placed stock audit")
    result = {"schema": "kit.sw2026.placed-pattern-stock.v1", "build": "34.5.2.0604",
              "disclosed_lock_sha256": LOCK, "frozen_author_intent_sha256": lock["specs_sha256"],
              "prior_origin_stock_sha256": PRIOR, "disclosed_archive_comparisons": disclosed,
              "independent_guarded_models": generated, "unchanged_origin_stock_streams": unchanged,
              "fresh_guarded_processes": 8, "native_processes": 0, "heldout_cases": 0, "corpus_credit": 0,
              "output_files_written": 0,
              "tool_sha256": digest(HERE.read_bytes())}
    with args.output.open("xb") as handle:
        handle.write(encode(result))
    print({"sources": len(disclosed), "generated": len(generated), "receipt": digest(args.output.read_bytes())})


if __name__ == "__main__":
    main()
