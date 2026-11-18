from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import sys


parser = ArgumentParser(description="Audit a controlled reverse or dual through-all native save")
parser.add_argument("--sdk-root", type=Path, required=True)
parser.add_argument("--native-root", type=Path, required=True)
parser.add_argument("--trial-sha256", required=True)
parser.add_argument("--result-sha256", required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
root = args.native_root.resolve(strict=True)


def read_bound(path, digest):
    data = path.read_bytes()
    if sha256(data).hexdigest() != digest:
        raise ValueError(f"immutable evidence changed: {path.name}")
    return data


task = json.loads(read_bound(root / "Trial.json", args.trial_sha256))
terminal = json.loads(read_bound(root / "Inspection/Result.json", args.result_sha256))
assert terminal["passed"] and terminal["controls_healthy"] and terminal["distinct_native_processes"] == 4
assert terminal["all_numeric_checks_passed"] and terminal["all_inputs_immutable"]
assert terminal["heldout_payloads_read"] == task["heldout_payloads_read"] == 0
assert task["oracle_sha256"] == "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
assert all(item["oracle_identity"]["sha256"] == task["oracle_sha256"] for item in terminal["phases"].values())

source_manifest_sha = task["writer_source_manifest_sha256"]
source_manifest = json.loads(read_bound(root / "WriterSourceManifest.json", source_manifest_sha))
for relative, fact in source_manifest["source_files"].items():
    if relative.startswith("src/"):
        read_bound(args.sdk_root / relative, fact["sha256"])
for name in ("NeutralRequest.json", "GeneratedCase.json", "DestinationProof.json"):
    read_bound(root / name, task["files_sha256"][name])

request = json.loads((root / "NeutralRequest.json").read_bytes())
mode = (request["direction"], request["axis"])
expected_ends = {("reverse", "y"): (1, 1, 0, 0, 0), ("both", "x"): (0, 1, 1, 0, 1)}[mode]
prediction = json.loads((root / "GeneratedCase.json").read_bytes())["prediction"]["edited"]
row = terminal["phases"]["Generated"]
record = json.loads(read_bound(root / "Inspection/Generated/Record.json", row["record_sha256"]))
assert record["passed"] and record["result"]["save"] == [True, 0, 0]
artifact_sha = record["result"]["saved_sha256"]
payload = read_bound(root / "Inspection/Generated/Saved.SLDPRT", artifact_sha)
helper = Path(__file__).with_name("AuditThroughAllDisclosed.py")
read_bound(helper, "3efab18180d8c849fc8eb8a809bfb2f9bff2726ca01b0faec5d8fbdf7ee9b9bb")

sys.path[:0] = [str(args.sdk_root / "src"), str(helper.parent)]
from AuditThroughAllDisclosed import graph, roundtrip
from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckSavedCutScope import CheckSavedCutScope
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadManagedCutAtoms import ReadManagedCutAtoms
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSavedCutBodies import ReadSavedCutBodies
from convert.adapters.solidworks.Core.TypedResolved.ReadDepthOwner import ReadDepthOwner

archive, links, _, named = graph(payload)
for usage in (links.ConfigValue.ReportValue, links.ResolvedValue.ReportValue):
    assert usage["completed"] and not usage["missing_schemas"] and not usage["provisional_schemas"]
stock, cut = named["StockBoss"], named["ThroughFeature"]
fields = cut.FieldsValue
end = fields["f818"].FieldsValue
assert tuple(end[name] for name in ("f08", "f0c", "f10", "f88", "f8c")) == expected_ends
assert all(end[name] is None for name in ("f18", "f20", "fc8", "fd0"))
depth = ReadDepthOwner(links, stock.FieldsValue["f818"].FieldsValue["f18"]).DepthValue.native_value
assert depth == prediction["stock_depth_m"]
atoms = ReadManagedCutAtoms(links)
consumed, produced = ReadSavedCutBodies(stock, cut, atoms)
scope = CheckSavedCutScope(links.ConfigValue.RootValue, stock, cut, consumed)

result = {
    "schema": "kit.sw2026.directional-through-all-saved-typed.v1",
    "passed": True,
    "trial_sha256": args.trial_sha256,
    "native_result_sha256": args.result_sha256,
    "sdk_source_manifest_sha256": source_manifest_sha,
    "tool_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
    "generated_save_sha256": artifact_sha,
    "generated_save_bytes": len(payload),
    "case": request["name"],
    "direction": mode[0],
    "axis": mode[1],
    "stream_roundtrips": roundtrip(archive, links),
    "cut_end": {name: end[name] for name in ("f08", "f0c", "f10", "f88", "f8c", "f148", "f14c", "f150", "f154", "f158")},
    "absent_distance_draft_owners": True,
    "stock_depth_m": depth,
    "stock_scope": stock.FieldsValue["f544"],
    "cut_scope": scope,
    "cut_wrapper_presence": fields["has_f548"],
    "chooser_links_actual_cut": fields["f4c0"]["f68"] is cut,
    "consumed_stock_atom_id": consumed,
    "produced_cut_atom_id": produced,
    "heldout_payloads_read": 0,
    "public_writer_qualified": False,
}
encoded = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
with args.output.open("xb") as stream:
    stream.write(encoded)
print(json.dumps({
    "passed": True,
    "result_sha256": sha256(encoded).hexdigest(),
    "stream_comparisons": len(result["stream_roundtrips"]),
    "stock_depth_m": depth,
    "cut_scope": scope,
}, sort_keys=True))
