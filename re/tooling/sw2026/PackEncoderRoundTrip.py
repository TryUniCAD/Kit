from argparse import ArgumentParser
import json
import math
from pathlib import Path, PureWindowsPath
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ObserveEncoderRoundTrip import digest, record, require


ORACLES = {
    ("34.4.1.1011", "200ac2597814daaead89c1de698a45341850fa2fe0d8c094debb316009e7ea7f"):
        "SOLIDWORKS 2026 SP04.1",
    ("34.5.2.0604", "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"):
        "SOLIDWORKS 2026 SP05.2",
}
PHASES = ("ControlBefore", "EditControl", "CandidateGenerated", "CandidateReopen", "ControlAfter")


def read(path):
    return json.loads(path.read_bytes())


def positive_density(state, reference):
    return (
        all(math.isclose(state[key], reference[key], rel_tol=1e-8, abs_tol=1e-12)
            for key in ("document_density_kg_m3", "effective_density_kg_m3"))
        and math.isclose(state["mass_kg"], state["volume_m3"], rel_tol=1e-8, abs_tol=1e-12)
        and math.isclose(reference["mass_kg"], reference["volume_m3"], rel_tol=1e-8, abs_tol=1e-12)
        and any(row["name"] == "Material <not specified>" for row in state["tree"])
        and any(row["name"] == "Material <not specified>" for row in reference["tree"])
    )


def state_row(label, state, reference):
    require(
        state["dimension_driving"] and state["bodies"] == 1
        and all(row["status"] == 0 and not row["warning"] for row in state["tree"])
        and positive_density(state, reference),
        "native solid isn't clean or its density differs from the independent control",
    )
    return {
        "role": label, "rows": len(state["tree"]), "warnings": 0,
        "bodies": state["bodies"], "depth_m": state["depth_m"],
        "volume_m3": state["volume_m3"], "area_m2": state["area_m2"],
        "centre_of_mass_m": state["centre_of_mass_m"],
        "document_density_kg_m3": state["document_density_kg_m3"],
        "effective_model_density_kg_m3": state["effective_density_kg_m3"],
        "mass_at_unit_density_kg": state["mass_kg"],
    }


def measured_phase(observation_dir, label, expected):
    base = observation_dir / label
    observation_path = base / "Record.json"
    row = read(observation_path)
    require(
        digest(observation_path) == expected["record_sha256"]
        and row == {key: value for key, value in expected.items() if key not in ("record_sha256", "worker_exit_code")}
        and row["passed"] and expected["worker_exit_code"] == 0
        and row["open_errors"] == row["open_warnings"] == 0
        and row["exit"]["exit_code"] == 0
        and row["exit"]["pid"] == row["oracle_identity"]["pid"]
        and row["exit"]["started"] == row["oracle_identity"]["started"],
        "native record or process lifecycle differs: " + label,
    )
    return row, {
        "native_record_sha256": digest(observation_path),
        "native_request_sha256": digest(base / "Request.json"),
        "worker_log_sha256": digest(base / "Worker.log"),
    }


def build_custody(args, observation):
    source_manifest = args.preparation / "Candidate.json"
    repeat_manifest = args.repeat / "Candidate.json"
    manifest_sha = digest(source_manifest)
    require(
        digest(repeat_manifest) == manifest_sha == observation["candidate_manifest_sha256"],
        "independent guarded preparation manifests differ",
    )
    build = read(source_manifest)
    require(
        build["stage"] == "awaiting_native_measurement" and build["runtime_input_reads"] == 0
        and build["neutral_sha256"] == digest(args.neutral)
        and build["archive_sha256"] == observation["candidate_sha256"],
        "guarded build did not own the measured candidate",
    )
    name = PureWindowsPath(build["native_locator"]).name
    for folder in (args.preparation, args.repeat):
        candidate = folder / name
        require(
            candidate.stat().st_size == build["archive_bytes"]
            and digest(candidate) == build["archive_sha256"],
            "independently generated candidate bytes or extent differ",
        )
    return build, manifest_sha


def pack(args):
    native_path = args.observation / "Result.json"
    observation = read(native_path)
    method = Path(__file__).with_name("ObserveEncoderRoundTrip.py")
    require(
        observation["schema"] == "kit.sw2026.encoder-round-trip-native-observation.v1"
        and observation["passed"] and observation["controls_healthy"]
        and not observation["faults"] and observation["archive_locator_absent"]
        and observation["method_sha256"] == digest(method)
        and tuple(observation["phases"]) == PHASES
        and observation["distinct_native_processes"] == len(PHASES),
        "expected the exact passing controlled native observation",
    )
    build, manifest_sha = build_custody(args, observation)
    role = observation["case"] + ("Edited" if observation["edited_input"] else "Reconstruction")
    native = {}
    packet_phases = {}
    for label in PHASES:
        native[label], packet_phases[label] = measured_phase(args.observation, label, observation["phases"][label])
    identities = [row["oracle_identity"] for row in native.values()]
    lifetimes = {(identity["pid"], identity["started"]) for identity in identities}
    oracle_identities = {(identity["build"], identity["sha256"]) for identity in identities}
    require(len(lifetimes) == len(PHASES) and len(oracle_identities) == 1, "oracle identity differs between fresh phases")
    (build_version, oracle_sha), = oracle_identities
    require((build_version, oracle_sha) in ORACLES, "native observation used an unqualified oracle identity")
    oracle = {"build": build_version, "product": ORACLES[build_version, oracle_sha], "sha256": oracle_sha}
    initial = native["ControlBefore"]
    opposite = native["EditControl"]
    generated = native["CandidateGenerated"]
    reopened = native["CandidateReopen"]
    trailing = native["ControlAfter"]
    derivative = args.observation / "CandidateGenerated/Edited.SLDPRT"
    require(
        initial["source_sha256"] == trailing["source_sha256"] != opposite["source_sha256"]
        and generated["source_sha256"] == observation["candidate_sha256"]
        and digest(derivative) == generated["derivative_sha256"] == reopened["source_sha256"],
        "the controlled candidate or saved derivative digest differs",
    )
    require(
        tuple(generated["states"]) == ("Initial", "Rebuilt", "Edited")
        and tuple(reopened["states"]) == ("Initial", "Rebuilt")
        and generated["save_status"] == {"saved": True, "errors": 0, "warnings": 0},
        "native clean edit, save and independent reopen are required",
    )
    phases = []
    for label, item in native.items():
        candidate_phase = label in ("CandidateGenerated", "CandidateReopen")
        states = []
        if candidate_phase:
            for name, state in item["states"].items():
                reference = opposite if label == "CandidateReopen" or name == "Edited" else initial
                states.append(state_row(name, state, reference["states"]["Rebuilt"]))
        phases.append({
            "role": label.replace("Candidate", role, 1) if candidate_phase else label,
            "passed": True, "record_sha256": packet_phases[label]["native_record_sha256"],
            "states": states, "numeric_checks": observation["numeric_checks"][label],
            "save_status": [True, 0, 0] if label == "CandidateGenerated" else None,
            "derivative_sha256": item.get("derivative_sha256"),
        })
    args.output.mkdir()
    packet_path = args.output / "Packet.json"
    record(packet_path, {
        "schema": "kit.sw2026.encoder-round-trip-custody.v1",
        "oracle": oracle, "native_result_sha256": digest(native_path),
        "guarded_manifest_sha256": manifest_sha, "repeat_guarded_manifest_sha256": manifest_sha,
        "native_observer_sha256": digest(method), "packaging_method_sha256": digest(Path(__file__)),
        "neutral_sha256": build["neutral_sha256"], "prepared_sha256": build["archive_sha256"],
        "archive_locator_absent": True, "native_locator": build["native_locator"],
        "derivative_sha256": digest(derivative), "phases": packet_phases,
    })
    receipt = {
        "schema": "kit.sw2026.sdk-standalone-default-part-evidence.v1",
        "oracle": oracle, "passed": True, "controls_healthy": True,
        "runtime_input_file_reads": build["runtime_input_reads"],
        "native_result_sha256": digest(native_path), "packet_sha256": digest(packet_path),
        "generation_report_sha256": manifest_sha,
        "distinct_native_processes": len(phases), "numeric_checks": sum(row["numeric_checks"] for row in phases),
        "builds": [{
            "role": role, "candidate_sha256": build["archive_sha256"], "bytes": build["archive_bytes"],
            "build_a_sha256": manifest_sha, "build_b_sha256": manifest_sha,
        }],
        "cases": [{
            "role": role, "generated_sha256": build["archive_sha256"], "passed": True,
            "archive_locator_absent": True, "document_preference_and_unassigned_body_density_match": True,
        }],
        "phases": phases,
    }
    target = args.output / "Measurement.json"
    record(target, {"written_at": build["written_at"], "receipt": receipt})
    print(json.dumps({"role": role, "native_result_sha256": receipt["native_result_sha256"],
                      "packet_sha256": receipt["packet_sha256"], "measurement_sha256": digest(target)}))


if __name__ == "__main__":
    parser = ArgumentParser(description="Bind measured native phases to an exact offline SDK receipt")
    for item in ("observation", "preparation", "repeat", "neutral", "output"):
        parser.add_argument("--" + item, type=Path, required=True)
    pack(parser.parse_args())
