from hashlib import sha256
import json
from pathlib import Path

root = Path(r"C:\KitGeneratedChamfer01")
out = root / "Run01"
target = Path(r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover\GeneratedChamferCold01\DisclosedReceipt01.json")
digest = lambda path: sha256(path.read_bytes()).hexdigest()
raw_result = out / "Result.json"
result_pin = "454f8687d8ae35134a7c374855e105181c21d40365a614ae76f443fff6b831ea"
assert digest(raw_result) == result_pin
result = json.loads(raw_result.read_bytes())
trial = json.loads((root / "Packet" / "Trial.json").read_bytes())
assert result["passed"] and result["healthy_controls"] and result["proper_distinct_lifetimes"]
assert result["lifecycle_slots"] == [0, 1] and len(result["phases"]) == 6
assert result["heldout_credit"] == 0
rows, numeric = [], 0
for phase in result["phases"]:
    name = phase["role"] if phase["slot"] is None else f"Slot{phase['slot'] + 1:02d}-{phase['role']}"
    record = out / name / "Record.json"
    assert digest(record) == phase["receipt_sha256"] and phase["phase_passed"]
    native = json.loads(record.read_bytes())
    identity = native["oracle_identity"]
    assert identity["file_version"] == "34.5.2.0604" and identity["sha256"] == trial["oracle_sha256"]
    row = {"role": phase["role"], "slot": phase["slot"], "record_sha256": digest(record)}
    if phase["slot"] is not None:
        assert native["open_status"] == {"opened":True,"errors":0,"warnings":0}
        assert native["cold"]["body_count"] == 1 and native["cold"]["diagnostics"] == 0
        assert all(check["passed"] for check in native["checks"])
        row.update(numeric_checks=len(native["checks"]), saved_sha256=native["artifact_sha256"],
                   driver_edited=(phase["role"] == "edit"), body_count=1)
        if phase["role"] == "edit":
            assert native["native_save_status"] == [True,0,0]
        numeric += len(native["checks"])
    rows.append(row)
report = {"schema": "kit.sw2026.generated-cold-chamfer-disclosed.v1", "passed": True,
          "native_result_sha256": result_pin, "native_build": trial["oracle_build"],
          "oracle_sha256": trial["oracle_sha256"], "trial_sha256": result["manifest_sha256"],
          "construction_revision": trial["construction_revision"], "distinct_processes": 6,
          "healthy_controls": True, "numeric_checks": numeric, "lifecycle_slots": 2,
          "heldout_credit": 0, "generated_inputs": [row["archive_sha256"] for row in trial["cases"]],
          "observable_phases": rows}
with target.open("x", encoding="utf-8", newline="\n") as file:
    json.dump(report, file, indent=2, sort_keys=True, allow_nan=False)
    file.write("\n")
print(json.dumps({"receipt_sha256": digest(target), "native_phases": 6, "numeric_checks": numeric}))
