from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path, PureWindowsPath

from AuthorCurves import digest, require, write_json
from AuthorRectangleAnchors import CONTROL, ORACLE, control
import InspectSdkBlindPart as part_observer
from InspectSdkBlindPart import TOOLS as PART_TOOLS, phase, tree_prediction


SCHEMA = "kit.sw2026.sdk-default-part-native.v2"
TOOLS = (*PART_TOOLS, Path(__file__).name)
PART_SNAPSHOT = part_observer.snapshot


def checked(path, sha):
    require(path.is_file() and digest(path) == sha, f"frozen default-part evidence differs: {path.name}")
    return path


def verify(packet, expected):
    root = packet.parent
    job = json.loads(checked(packet, expected).read_bytes())
    require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE and job["heldout_inputs_read"] == 0,
            "expected the pinned disclosed default-part trial")
    tools = root / "Tools"
    require(Path(__file__).resolve().parent == tools and set(job["tools"]) == set(TOOLS),
            "the default-part observer closure differs")
    for name, sha in job["tools"].items():
        checked(tools / name, sha)
    seed = checked(root / "Control.SLDPRT", CONTROL)
    proof = json.loads(checked(root / "BuildProof.json", job["build_proof_sha256"]).read_bytes())
    require(proof["passed"] and proof["runtime_reads"] == 0 and len(proof["cases"]) == 2,
            "expected two independently guarded default part candidates")
    if "previous_result_sha256" in job:
        prior = json.loads(checked(root / "PreviousResult.json", job["previous_result_sha256"]).read_bytes())
        require(not prior["passed"] and prior["controls_healthy"] and len(prior["cases"]) == 2
                and all(value["passed"] for value in prior["phases"].values())
                and [value["generated_sha256"] for value in prior["cases"]] == [value["candidate_sha256"] for value in proof["cases"]],
                "density observer correction requires the failed exact candidate evidence")
    rows = []
    for value in proof["cases"]:
        home = root / value["role"]
        case = json.loads(checked(home / "Expected.json", value["expected_sha256"]).read_bytes())
        input_file = checked(home / "SdkRequest.json", value["request_sha256"])
        request = json.loads(input_file.read_bytes())
        name = PureWindowsPath(case["intent"]["self_path"]).name
        file = checked(home / name, value["candidate_sha256"])
        require(file.stat().st_size == value["bytes"] and request["expected_locator"] == case["intent"]["self_path"]
                and value["build_a_sha256"] == value["build_b_sha256"] and len(value["streams"]) == 10
                and all(stream["typed_roundtrip"] for stream in value["streams"].values()),
                "default-part evidence failed its guarded build or typed stream audit")
        require(request["written_at"] == proof["written_at"], "the frozen writer event changed")
        rows.append((value, case, file, tree_prediction(case["native_presentation"], case)))
    return job, seed, rows


def snapshot_density(author, case):
    snapshot = PART_SNAPSHOT(author, case)
    extension = author.get(author.model, "Extension")
    snapshot["document_density_kg_m3"] = float(author.get(extension, "GetUserPreferenceDouble", 7, 0))
    snapshot["effective_density_kg_m3"] = snapshot["mass"]["mass"] / snapshot["mass"]["volume"]
    return snapshot


def check_density(states):
    return bool(states) and all(
        math.isclose(state["document_density_kg_m3"], 1000.0, rel_tol=5e-7)
        and math.isclose(state["effective_density_kg_m3"], 1.0, rel_tol=5e-7)
        for state in states.values()
    )


def run(packet, expected):
    require(os.name == "nt", "native default-part verification requires the reserved Windows guest")
    job, seed, rows = verify(packet, expected)
    output = packet.parent / "Inspection"
    output.mkdir()
    stages = {}
    result = {"schema": SCHEMA, "packet_sha256": expected, "phases": stages, "cases": [],
              "heldout_inputs_read": 0, "passed": False}

    def record(role, observer, *arguments, **options):
        stages[role] = observer(output, role, *arguments, **options)
        write_json(output / "Result.json", result)
        return stages[role]

    part_observer.snapshot = snapshot_density
    try:
        before = record("ControlBefore", control, seed)
        if before["passed"]:
            for row, case, generated, tree in rows:
                role = row["role"]
                archive_path = Path(case["intent"]["self_path"])
                require(not archive_path.exists(), "standalone default-part archived location must be absent")
                built = record(role + "Generated", phase, generated, row["candidate_sha256"], case, tree)
                reopened = None
                if built["passed"]:
                    reopened = record(
                        role + "Reopen", phase, output / (role + "Generated") / "Edited.SLDPRT",
                        built["derivative_sha256"], case, tree, edited_tree=built["states"]["Edited"]["tree"],
                    )
                mass_states = (built, reopened) if reopened else ()
                mass_passed = bool(mass_states) and all(check_density(state["states"]) for state in mass_states)
                no_locator = not archive_path.exists()
                result["cases"].append({"role": role, "passed": bool(built["passed"] and reopened and reopened["passed"]
                                                                       and mass_passed and no_locator),
                                        "document_preference_and_unassigned_body_density_match": mass_passed,
                                        "archive_locator_absent": no_locator,
                                        "generated_sha256": row["candidate_sha256"]})
    except Exception as error:
        result["error"] = repr(error)
    finally:
        part_observer.snapshot = PART_SNAPSHOT
        after = record("ControlAfter", control, seed)
        again, _, _ = verify(packet, expected)
        births = {value["oracle_identity"]["process_creation_filetime"] for value in stages.values()
                  if value.get("oracle_identity")}
        result.update(controls_healthy=bool(stages.get("ControlBefore", {}).get("passed") and after["passed"]),
                      distinct_processes=len(births), inputs_unchanged=again == job)
        result["passed"] = (result["controls_healthy"] and result["inputs_unchanged"] and len(stages) == len(births) == 6
                            and all(value["passed"] for value in stages.values()) and len(result["cases"]) == 2
                            and all(value["passed"] for value in result["cases"]))
        write_json(output / "Result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description="Observe disclosed independently generated default-recipe parts")
    parser.add_argument("command", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    options = parser.parse_args()
    packet = options.packet.resolve(strict=True)
    if options.command == "verify":
        verify(packet, options.packet_sha256)
        result = {"passed": True, "processes_started": 0}
    else:
        trial = run(packet, options.packet_sha256)
        result = {key: trial[key] for key in ("passed", "controls_healthy", "distinct_processes")}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
