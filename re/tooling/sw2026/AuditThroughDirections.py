from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import sys

LOCK_PIN = "3efe141cd31cc06e8b7545db590548dd1ba511960261e8b78cf72523d5d5ba79"
HELPER_PIN = "3efab18180d8c849fc8eb8a809bfb2f9bff2726ca01b0faec5d8fbdf7ee9b9bb"


def collect(args):
    assert sha256(args.lock.read_bytes()).hexdigest() == LOCK_PIN
    assert sha256((args.helpers_root / "AuditThroughAllDisclosed.py").read_bytes()).hexdigest() == HELPER_PIN
    assert args.source_root.name == "Disclosed" and args.source_root.parent.name == "ThroughAllSourcePacket03"
    sys.path[:0] = [str(args.sdk_root / "src"), str(args.helpers_root)]
    from AuditThroughAllDisclosed import graph, node_ref, roundtrip
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadManagedCutAtoms import ReadManagedCutAtoms
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSavedCutBodies import ReadSavedCutBodies
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckSavedCutScope import CheckSavedCutScope
    from convert.adapters.solidworks.Core.TypedResolved.ReadDepthOwner import ReadDepthOwner
    from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents

    lock = json.loads(args.lock.read_bytes())
    results = []
    for identifier in ("D01", "D02", "D03"):
        source = args.source_root / identifier
        expected = next(row for row in lock["slots"] if row["slot"] == identifier)
        manifest_path = source / "SavedAuthor.json"
        assert sha256(manifest_path.read_bytes()).hexdigest() == expected["source_manifest_sha256"]
        manifest = json.loads(manifest_path.read_bytes())
        for state in ("source", "edited"):
            files = list((source / "Native" / state.title()).glob("*.SLDPRT"))
            assert len(files) == 1
            payload = files[0].read_bytes()
            assert len(payload) == expected["native_artifacts"][state]["bytes"]
            assert sha256(payload).hexdigest() == expected["native_artifacts"][state]["sha256"]
            archive, link, _, named = graph(payload)
            for report in (link.ConfigValue.ReportValue, link.ResolvedValue.ReportValue):
                assert report["completed"] and not report["missing_schemas"] and not report["provisional_schemas"]
            boss, cut = named["StockBoss"], named["ThroughFeature"]
            native = manifest[state]["operation"]
            end = cut.FieldsValue["f818"].FieldsValue
            wanted = (int(not native["both_directions"]), native["end_forward"], native["end_reverse"], 0, int(native["reverse_direction"]))
            actual = tuple(end[key] for key in ("f08", "f0c", "f10", "f88", "f8c"))
            assert actual == wanted and actual[1] == 1
            assert all(end[key] is None for key in ("f18", "f20", "fc8", "fd0", "f138", "f90"))
            assert not native["dimensions"] and native["depth_forward_m"] == native["depth_reverse_m"] == 0
            assert ReadParents(boss) == (named["StockProfile"],) and ReadParents(cut) == (named["ThroughProfile"],)
            depth = ReadDepthOwner(link, boss.FieldsValue["f818"].FieldsValue["f18"])
            assert depth.DepthValue.native_value == manifest[state]["stock"]["depth_forward_m"]
            managed = ReadManagedCutAtoms(link)
            consumed, produced = ReadSavedCutBodies(boss, cut, managed)
            scope = CheckSavedCutScope(link.ConfigValue.RootValue, boss, cut, consumed)
            repeated = roundtrip(archive, link)
            results.append({"case": identifier, "state": state, "input_sha256": sha256(payload).hexdigest(), "bytes": len(payload), "source_manifest_sha256": expected["source_manifest_sha256"], "public_lock_record_sha256": expected["case_lock_sha256"], "end_tuple": list(actual), "stock_depth_m": depth.DepthValue.native_value, "absent_cut_distance_and_draft_owners": True, "saved_end_tail_words": {key: end[key] for key in ("f148", "f14c", "f150", "f154", "f158")}, "body_ownership": {"consumed_atom_id": consumed, "produced_atom_id": produced, "scope": scope, "chooser_owns_actual_cut": cut.FieldsValue["f4c0"]["f68"] is cut}, "typed_stream_roundtrips": repeated, "archive_retention_only": True})
    return {"schema": "kit.sw2026.through-all-disclosed-directions.v1", "source_lock_sha256": LOCK_PIN, "helper_sha256": HELPER_PIN, "tool_sha256": sha256(Path(__file__).read_bytes()).hexdigest(), "disclosed_cases": 3, "native_saves": 6, "exact_stream_comparisons": sum(len(row["typed_stream_roundtrips"]) for row in results), "passed": True, "heldout_payloads_read": 0, "writer_output_count": 0, "native_writer_acceptance": False, "inputs": results}


parser = ArgumentParser()
parser.add_argument("--sdk-root", type=Path, required=True)
parser.add_argument("--helpers-root", type=Path, required=True)
parser.add_argument("--source-root", type=Path, required=True)
parser.add_argument("--lock", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
result = collect(args)
encoded = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
if args.check:
    assert args.output.read_bytes() == encoded
else:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encoded)
print(json.dumps({"passed": True, "native_saves": result["native_saves"], "stream_comparisons": result["exact_stream_comparisons"], "sha256": sha256(encoded).hexdigest()}))
