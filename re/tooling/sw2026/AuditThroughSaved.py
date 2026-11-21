from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import sys


parser = ArgumentParser(description="Audit the exact disclosed generated G01 native-saved through-all derivative")
parser.add_argument("--sdk-root", type=Path, required=True)
parser.add_argument("--helpers-root", type=Path, required=True)
parser.add_argument("--native-root", type=Path, required=True)
parser.add_argument("--source-manifest", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
root = args.native_root.resolve(strict=True)
assert root.name == "GeneratedThroughAll02"
terminal = root / "Inspection/Result.json"
assert sha256(terminal.read_bytes()).hexdigest() == "a7a14451eb72a459aa70ff9937c996880cc3a8427ac90dcd6d49245187215dff"
assert json.loads(terminal.read_bytes())["passed"]
assert sha256((args.helpers_root / "AuditThroughAllDisclosed.py").read_bytes()).hexdigest() == "3efab18180d8c849fc8eb8a809bfb2f9bff2726ca01b0faec5d8fbdf7ee9b9bb"
assert sha256(args.source_manifest.read_bytes()).hexdigest() == "7ff3eacf713c39e109c09bb786f521c9f97df3413c1224a5e7278438d4a4639e"
for relative, expected_file in json.loads(args.source_manifest.read_bytes())["source_files"].items():
    if relative.startswith("src/"):
        assert sha256((args.sdk_root / relative).read_bytes()).hexdigest() == expected_file["sha256"]
sys.path[:0] = [str(args.sdk_root / "src"), str(args.helpers_root)]
from AuditThroughAllDisclosed import graph, roundtrip
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadManagedCutAtoms import ReadManagedCutAtoms
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSavedCutBodies import ReadSavedCutBodies
from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckSavedCutScope import CheckSavedCutScope
from convert.adapters.solidworks.Core.TypedResolved.ReadDepthOwner import ReadDepthOwner

generated = json.loads((root / "Inspection/Generated/Record.json").read_bytes())
assert generated["passed"] and generated["result"]["save"] == [True, 0, 0]
expected = json.loads((root / "GeneratedCase.json").read_bytes())["prediction"]["edited"]
file = root / "Inspection/Generated/Saved.SLDPRT"
payload = file.read_bytes()
assert sha256(payload).hexdigest() == generated["result"]["saved_sha256"] == "f1ac3d1b8657352c1a9c031b878b3fa336782746529ff66523f4e41a48df3ce7"
archive, link, _, named = graph(payload)
for report in (link.ConfigValue.ReportValue, link.ResolvedValue.ReportValue):
    assert report["completed"] and not report["missing_schemas"] and not report["provisional_schemas"]
boss, cut = named["StockBoss"], named["ThroughFeature"]
fields = cut.FieldsValue
end = fields["f818"].FieldsValue
atoms = ReadManagedCutAtoms(link)
consumed, produced = ReadSavedCutBodies(boss, cut, atoms)
scope = CheckSavedCutScope(link.ConfigValue.RootValue, boss, cut, consumed)
depth = ReadDepthOwner(link, boss.FieldsValue["f818"].FieldsValue["f18"])
assert depth.DepthValue.native_value == expected["stock_depth_m"]
assert tuple(end[key] for key in ("f08", "f0c", "f10", "f88", "f8c")) == (1, 1, 0, 0, 1)
assert all(end[key] is None for key in ("f18", "f20", "fc8", "fd0"))
result = {"schema": "kit.sw2026.generated-through-all-saved-typed.v1", "passed": True, "tool_sha256": sha256(Path(__file__).read_bytes()).hexdigest(), "native_result_sha256": sha256(terminal.read_bytes()).hexdigest(), "input_sha256": sha256(payload).hexdigest(), "bytes": len(payload), "sdk_source_manifest_sha256": sha256(args.source_manifest.read_bytes()).hexdigest(), "stream_roundtrips": roundtrip(archive, link), "cut_end": {key: end[key] for key in ("f08", "f0c", "f10", "f88", "f8c", "f148", "f14c", "f150", "f154", "f158")}, "absent_distance_draft_owners": True, "stock_depth_m": depth.DepthValue.native_value, "stock_scope": boss.FieldsValue["f544"], "cut_scope": scope, "cut_has_saved_wrapper": fields["has_f548"], "cut_has_saved_chooser": fields["has_f4c0"], "actual_chooser_owner_alias": fields["f4c0"]["f68"] is cut, "consumed_boss_atom_id": consumed, "produced_cut_atom_id": produced, "heldout_payloads_read": 0, "public_read_qualified": False}
encoded = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
if args.check:
    assert args.output.read_bytes() == encoded
else:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encoded)
print(json.dumps({"passed": True, "sha256": sha256(encoded).hexdigest(), "stream_roundtrips": len(result["stream_roundtrips"]), "edited_depth_m": result["stock_depth_m"], "cut_scope": scope}))
