from argparse import ArgumentParser
from dataclasses import asdict
import json
from math import prod
from pathlib import Path
from subprocess import run
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent)]

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import ReadSingleNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Patterns.ReadPatChain import ReadPatChain
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude

from CheckPatternAngleOwners import require
from MakePatternSeed import FrontBlindIntent, RaisedSeedIntent
from PatternAngleWire import read_resolved, write_resolved
from ProvePatternAngleOwners import exact_config
from ProvePatternPlaneDirectionRule import digest, document_rows, encode


MODEL_CASES = (
    RaisedSeedIntent("RaisedNoteA", "Default", r"C:\KitRaisedPattern\RaisedNoteA.SLDPRT", 1795251123,
                     FrontBlindIntent("Model plate rectangle", "Model plate", ((0, 0, 0), (.147, .110, .0065))),
                     FrontBlindIntent("Model seed rectangle", "Model raised seed", ((.047, .025, 0), (.057, .037, .01375)))),
    RaisedSeedIntent("RaisedNoteB", "Modelled", r"C:\KitRaisedPattern\RaisedNoteB.SLDPRT", 1795262162,
                     FrontBlindIntent("Base plate footprint", "Base extrusion", ((0, 0, 0), (.128, .104, .00475))),
                     FrontBlindIntent("Raised island footprint", "Raised extrusion", ((.024, .071, 0), (.039, .085, .01625)))),
)


def model(intent):
    payload = encode(asdict(intent))
    command = (sys.executable, "-I", "-B", str(HERE.with_name("PatternSeedProcess.py")))
    first, second = (run(command, input=payload, capture_output=True, cwd=ROOT, timeout=30) for _ in range(2))
    require(first.returncode == second.returncode == 0, "guarded raised seed process refused\n" + first.stderr.decode())
    require(not first.stderr and not second.stderr and first.stdout == second.stdout,
            "generated raised seed streams or receipts are nondeterministic")
    report = json.loads(first.stdout)
    require(report["roots"] == 21 and report["actual_atoms"] == [101, 102] and report["consumed"] == [1, 0]
            and report["guarded_runtime_reads"] == report["native_files_written"] == 0
            and len(report["bad_input"]) == 4 and len(report["bad_readback"]) == 6,
            "fresh graph lost selected ownership or required boundaries")
    ((px0, py0, _), (px1, py1, base_depth)) = intent.plate.bounds_m
    ((x0, y0, _), (x1, y1, top)) = intent.seed.bounds_m
    length, width = px1 - px0, py1 - py0
    add_h = top - base_depth
    base = prod((length, width, base_depth))
    excess = prod((x1 - x0, y1 - y0, add_h))
    base_center, raised_center = ((px0 + px1) * .5, (py0 + py1) * .5, base_depth * .5), ((x0 + x1) * .5, (y0 + y1) * .5, (base_depth + top) * .5)
    area = 2 * (length * width + base_depth * (length + width) + add_h * (x1 - x0 + y1 - y0))
    centroid = tuple((p * base + q * excess) / (base + excess) for p, q in zip(base_center, raised_center, strict=True))
    return {"request_sha256": digest(payload), "authored_inputs": asdict(intent),
            "independent_joined_geometry": {"body_count": 1, "face_count": 11, "volume_m3": base + excess,
                                           "area_m2": area, "centroid_m": centroid}, **report}


def read_disclosures(share):
    measured = {}
    for path, pin, _ in document_rows(share):
        if not (path.name.startswith(("DirectionEnvelope", "DatumHeight")) or path.stem in ("D01X", "D02Y")):
            continue
        archive, _, config, raw_config = exact_config(path, pin)
        cmgr = ReadCmgrMut(archive.require("Contents/CMgr"), 19000)
        context = MakeLinkContext(config, cmgr)
        raw = archive.require("Contents/Config-0-ResolvedFeatures")
        roots, dormant, snapshot = read_resolved(raw, config.MapValue, context, source_replay=True)
        replay, replayed = write_resolved(roots, dormant, config.MapValue, context, source_replay=True)
        require(raw == replay and snapshot == replayed, "disclosed seed archive changed bytes or class maps")
        link = NativeLink(config, ResolvedGraph(roots, dormant, snapshot, config.MapValue.CounterValue, 19000, context, {}),
                          "Config-0", "Config-0-ResolvedFeatures")
        actual = tuple(node for node in roots if node.ClassValue.NameValue in ("moProfileFeature_c", "moExtrusion_c", "moICE_c", "moLPattern_c"))
        require(tuple(node.ClassValue.NameValue for node in actual) ==
                ("moProfileFeature_c", "moExtrusion_c", "moProfileFeature_c", "moICE_c", "moLPattern_c"),
                "alternate disclosed seed/root inventory")
        atom_ids, result = ReadPatChain(link, actual)
        names = {node.FieldsValue["f08"]: node for node in roots}
        end_states = []
        for index, node in enumerate((actual[1], actual[3])):
            typed = ReadExtrude(link, node, names, NewSolid=index == 1)
            driver = typed.RequireDepth()
            end = typed.EndValue.FieldsValue
            require(driver.DepthValue.name == "D1" and end["f128"] == 1 and end["f08"] == 1 and end["f8c"] == 0
                    and end["f0c"] == end["f10"] == 0 and all(end[field] is None for field in ("f20", "fc8", "fd0")),
                    "disclosed raised seed lost actual blind merged depth")
            end_states.append({"feature_id": node.FieldsValue["f08"], "depth_m": driver.DepthValue.native_value,
                               "depth_owner": driver.DepthValue.TypedOwner, "native_merge_tolerance_m": node.FieldsValue["f838"],
                               "solid_mode": node.FieldsValue["f810"], "merge": end["f128"]})
        manager = config.RootValue.FieldsValue["fd88"]
        wrapper = ReadSingleNode(actual[3].FieldsValue["f548"], "moCompSolidBody_c").FieldsValue
        face = wrapper["ff0"]
        managed = tuple(row["o"] for row in manager["atoms"])
        require(manager["f260"] == atom_ids[-1] and result in managed, "disclosed manager frontier lost actual final result")
        measured[path.name] = {"source_sha256": pin, "config_sha256": digest(raw_config), "resolved_sha256": digest(raw),
                               "map_counters": [config.MapValue.CounterValue, snapshot.CounterValue], "roots": len(roots),
                               "lineage": atom_ids, "manager_order": [node.FieldsValue["f140"] for node in managed],
                               "seed_wrapper_base": wrapper["f108"], "seed_wrapper_immediate": wrapper["f18"],
                               "seed_wrapper_saved_face_class": face.ClassValue.NameValue,
                               "seed_wrapper_saved_face_index": face.IndexValue, "live_output_kernel_tag": result.FieldsValue["f180"],
                               "ends": end_states}
    require(len(measured) == 6 and len({tuple(row["manager_order"]) for row in measured.values()}) == 2,
            "expected only six exact disclosures including opposite actual save orders")
    return measured


def main():
    parser = ArgumentParser()
    parser.add_argument("--share", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    cases = {intent.name: model(intent) for intent in MODEL_CASES}
    require(len({row["streams"]["Config-0-ResolvedFeatures"]["bytes"] for row in cases.values()}) == 2,
            "unrelated modeled sizes and names must vary actual linked length")
    sources = read_disclosures(args.share)
    files = tuple(HERE.with_name(name + ".py") for name in ("ProvePatternSeed", "PatternSeedProcess", "MakePatternSeed"))
    receipt = {"schema": "kit.sw2026.raised-seed-graph.v1", "build": "34.5.2.0604", "exact_native_runs": 0,
               "heldout_cases": 0, "cad_files_written": 0, "fresh_guarded_processes": 4,
               "tools": {str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in files},
               "disclosed_warm_owner_audit": sources, "independent_model_cases": cases}
    with args.output.open("xb") as target:
        target.write(encode(receipt))
    print(json.dumps({"model_cases": len(cases), "warm_cases": len(sources),
                      "receipt_sha256": digest(args.output.read_bytes())}, sort_keys=True))


if __name__ == "__main__":
    main()
