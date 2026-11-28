from argparse import ArgumentParser
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from AuditColdSweep import generate
from AuditSweepArchive import BUILD, ORACLE, SDK_TREE, SOURCE_LOCK, check_sdk, checked, digest, guard_runtime, load_disclosed
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Construction.Part.Materials.MakePartDensity import MakePartDensity
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from SweepArchiveLayout import observe
from SweepColdPacket import CONTROL, verify
from SweepModel import require


JOB = "0b731785080b3c530d579cee233619f19bf9bbd72e955eca0880c30ae2268a29"
TERMINAL = "011dc9148d07bd6a8acaccd58bea7a2cec32209f1fcd07d5b487c6304408ea0e"


def auth_attempt(packet, records):
    job, spec, _ = verify(packet / "SweepJob.json", JOB)
    terminal = json.loads(checked(records / "Result.json", TERMINAL))
    require(terminal["job_sha256"] == JOB and terminal["writer_revision"] == job["writer_revision"]
            and terminal["oracle_build"] == BUILD and terminal["oracle_sha256"] == ORACLE
            and terminal["started_processes"] == terminal["distinct_processes"] == 4
            and terminal["idle_after"] and terminal["inputs_unchanged"] and not terminal["passed"]
            and terminal["heldout_credit"] == 0, "wrong first disclosed sweep result")
    comparison = json.loads((packet / "DisclosedComparison.json").read_bytes())
    processes, controls, loaded = set(), {}, []

    def phase(relative, entry):
        pin = entry["receipt_sha256"]
        row = json.loads(checked(records / relative / "Record.json", pin))
        identity = row["oracle_identity"]
        require(identity["file_version"] == BUILD and identity["sha256"] == ORACLE
                and identity["version_matches"] and identity["pe_machine"] == "0x8664"
                and entry["job_sha256"] == JOB and not entry["timed_out"], "wrong native process or working packet")
        processes.add((identity["process_id"], identity["process_creation_filetime"]))
        return row, pin

    for bracket, entry in terminal["controls"].items():
        row, pin = phase(entry["phase"], entry)
        require(bracket in ("before", "after") and row["passed"] and row["sha256"] == CONTROL
                and entry["passed"] and entry["worker_exit_code"] == 0, "root sweep brace control failed")
        controls[bracket] = pin
    for slot, (entry, source) in enumerate(zip(terminal["cases"], comparison["cases"], strict=True)):
        name = spec["cases"][slot]["name"]
        relative = f"Candidates/{name}.SLDPRT"
        artifact_pin = job["files"][relative]["sha256"]
        original = checked(packet / relative, artifact_pin)
        part, = entry["phases"]
        row, pin = phase(Path(f"Slot{slot + 1:02d}") / "candidate-open", part)
        require(entry["slot"] == part["slot"] == source["slot"] == slot and part["phase"] == "candidate-open"
                and not (entry["passed"] or part["passed"] or row["passed"])
                and row["source_immutable"] and row["native_sha256"] == row["original_sha256"]
                == part["source_sha256"] == artifact_pin and not row["dialogs"]
                and not row["cleanup_errors"] and not row["controller_diagnostics"] and part["worker_exit_code"] == 1,
                "disclosed candidate open failure or custody differs")
        ordered = source["states"]["original"]["tree"]
        require(row["open_status"] == {"opened": True, "errors": 0, "warnings": 0}
                and row["cold_solid_count"] == 1 and row["cold_diagnostics"] == 0
                and row["cold_ordered_tree"] == row["reopened"]["tree"] == ordered
                and sorted((face["type"], face["torus"], face["producer"], face["producer_type"])
                           for face in row["last_body_faces"])
                == [("curved", True, "OrdinarySweptBoss", "Sweep"), ("plane", False, "OrdinarySweptBoss", "Sweep"),
                    ("plane", False, "OrdinarySweptBoss", "Sweep")]
                and row["first_failure"]["error"] == "ValueError('cold open mass differs from the independent analytic prediction')",
                "first result has additional geometry, tree or open failure")
        physical = row["checks"]
        require(len(physical) == part["checks"] == 7 and all(check["passed"] for check in physical[:5])
                and physical[-2]["name"] == "cold open mass" and physical[-1]["name"] == "actual document density in kg/m³"
                and all(not check["passed"] for check in physical[-2:])
                and physical[-1]["actual"] == 1000.0 and physical[-1]["expected"] == spec["density_kg_m3"],
                "first cold failure does not isolate the missing physical density")
        loaded.append((original, job["candidates"][relative], {"name": name, "native_receipt_sha256": pin,
                       "candidate_sha256": artifact_pin, "open": row["open_status"], "no_diagnostics": True,
                       "cold_solids": 1, "exact_source_tree_rows": len(ordered), "geometry_checks": physical[:5],
                       "mismatched_mass_and_density": physical[-2:]}))
    require(len(loaded) == len(controls) == 2 and len(processes) == 4, "cold sweep receipts do not match the complete attempt")
    return spec, loaded, controls


def read_density(archive, mode):
    with observe(mode):
        link = ReadNativeLink(archive, 0)
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000).RootValue.FieldsValue
    active = manager["f360"]
    instance, = manager["f370"]["items"]
    require(instance["o"] is active is manager["f368"] and active.FieldsValue["fc50"] == -1
            and manager["n600"] == 0, "unexpected assigned material or per-configuration density")
    return link, link.ConfigValue.RootValue.FieldsValue["f1420"]


def observed_density(material, density):
    expected = MakePartDensity(density)
    param = material.FieldsValue["f08"]
    value = expected.FieldsValue["f08"]
    require(material.ClassValue == expected.ClassValue and param.ClassValue == value.ClassValue
            and param.FieldsValue == value.FieldsValue, "unmodeled native density parameter state")
    return {"material_slot": material.IndexValue, "parameter_slot": param.IndexValue,
            "physical_span": [material.StartOffset, material.EndOffset], "density_kg_m3": param.FieldsValue["f58"]}


def recompose(case, density, old_bytes, locator):
    old = SldprtArchive.from_bytes(old_bytes)
    original, no_material = read_density(old, "cold")
    require(no_material is None, "old attempt already had the physical density owner")
    raw, new = generate(case, density, locator=locator)
    current = SldprtArchive.from_bytes(raw)
    link, material = read_density(current, "cold")
    changes = {name for name in old.streams if old.streams[name] != current.streams[name]}
    require(old.streams.keys() == current.streams.keys() and changes == {link.ConfigName, link.StreamName}
            and new["map_counts"] == [original.ConfigValue.MapValue.CounterValue + 4,
                                     original.ResolvedValue.MapValue.CounterValue + 4],
            "adding generated density changed unrelated stream or map ownership")
    return {"same_locator_sha256": new["candidate_sha256"], "same_locator_bytes": len(raw),
            "physical_owner": observed_density(material, density), "affected_streams": {
                name: {"before_sha256": digest(old.streams[name]), "after_sha256": digest(current.streams[name])}
                for name in sorted(changes)}, "other_streams_exact": len(old.streams) - len(changes)}


def main():
    parser = ArgumentParser(description="Verify the prior cold sweep diagnostic and density-only regeneration")
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--prior-result", type=Path, required=True)
    parser.add_argument("--disclosed", type=Path, required=True)
    args = parser.parse_args()
    check_sdk()
    spec, loaded, controls = auth_attempt(args.packet, args.prior_result)
    native_sources, _, _ = load_disclosed(args.disclosed)
    blocked = guard_runtime()
    density = spec["density_kg_m3"]
    source_owners = []
    for slot, state, raw, _ in native_sources:
        _, material = read_density(SldprtArchive.from_bytes(raw), "linked")
        source_owners.append({"slot": slot + 1, "state": state, "source_sha256": digest(raw),
                              **observed_density(material, density)})
    candidates = []
    for case, (original, locator, receipt) in zip(spec["cases"], loaded, strict=True):
        candidates.append(receipt | recompose(case, density, original, locator))
    require(not blocked, "sweep density generation attempted external access")
    print(json.dumps({"schema": "kit.sw2026.sweep-density-diagnostic.v1", "oracle_build": BUILD, "oracle_sha256": ORACLE,
                      "first_attempt_result_sha256": TERMINAL, "first_attempt_job_sha256": JOB, "sdk_tree": SDK_TREE,
                      "disclosed_source_lock_sha256": SOURCE_LOCK, "control_receipt_sha256": controls,
                      "prior_passed": False, "native_distinct_processes": 4, "native_source_owners": source_owners,
                      "cases": candidates, "blocked_runtime_calls": len(blocked), "new_native_processes_started": 0,
                      "heldout_inputs_read": 0}, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
