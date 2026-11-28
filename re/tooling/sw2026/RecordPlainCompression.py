from argparse import ArgumentParser
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from StagePlainCompression import PRIOR_RECEIPT, checked, digest, require, write_json


def state_row(role, state, prior):
    mass = state["mass"]
    require(
        state["dimension_driving"]
        and state["whats_wrong"] == 0
        and state["body_count"] == 1
        and prior["dimension_driving"]
        and state["tree"] == prior["tree"]
        and state["sketch_parents"] == prior["sketch_parents"]
        and state["boss_parents"] == prior["boss_parents"],
        "tree, ownership or driving state differs: " + role,
    )
    current_values = (
        state["dimension_m"],
        mass["volume"],
        mass["area"],
        *mass["com"],
        mass["mass"],
        state["document_density_kg_m3"],
        state["effective_density_kg_m3"],
    )
    old_mass = prior["mass"]
    old_values = (
        prior["dimension_m"],
        old_mass["volume"],
        old_mass["area"],
        *old_mass["com"],
        old_mass["mass"],
        prior["document_density_kg_m3"],
        prior["effective_density_kg_m3"],
    )
    require(
        all(
            format(left, ".6g") == format(right, ".6g")
            for left, right in zip(current_values, old_values, strict=True)
        ),
        "same model produced different native measurements: " + role,
    )
    return {
        "role": role,
        "rows": len(state["tree"]),
        "depth_m": state["dimension_m"],
        "bodies": state["body_count"],
        "warnings": state["whats_wrong"],
        "volume_m3": mass["volume"],
        "area_m2": mass["area"],
        "centre_of_mass_m": mass["com"],
        "mass_kg": mass["mass"],
        "document_density_kg_m3": state["document_density_kg_m3"],
        "effective_body_density_kg_m3": state["effective_density_kg_m3"],
    }


def record(prior, batch, output):
    old = json.loads(PRIOR_RECEIPT.read_bytes())
    previous = json.loads(
        checked(prior / "Inspection/Result.json", old["native_result_sha256"])
    )
    comparison_raw = (batch / "Compression.json").read_bytes()
    comparison = json.loads(comparison_raw)
    packet_sha = comparison["packet_sha256"]
    packet = json.loads(checked(batch / "Packet.json", packet_sha))
    build_sha = packet["build_proof_sha256"]
    build = json.loads(checked(batch / "BuildProof.json", build_sha))
    terminal_raw = (batch / "Inspection/Result.json").read_bytes()
    terminal = json.loads(terminal_raw)
    host = json.loads((batch / "Host.json").read_bytes())
    require(
        host["transport_exit_confirmed"]
        and host["transport_returncode"] == 0
        and terminal["passed"]
        and terminal["controls_healthy"]
        and terminal["inputs_unchanged"]
        and terminal["packet_sha256"] == packet_sha
        and terminal["heldout_inputs_read"] == 0
        and terminal["distinct_processes"] == len(terminal["phases"]) == 6,
        "the exact native batch did not finish with six healthy processes",
    )
    labels = tuple(row["role"] for row in old["phases"])
    require(
        tuple(terminal["phases"]) == labels == tuple(previous["phases"]),
        "the exact native phase order changed",
    )
    require(
        [row["candidate_sha256"] for row in build["cases"]]
        == [row["generated_sha256"] for row in terminal["cases"]]
        == [row["zlib_ng_sha256"] for row in comparison["cases"]],
        "native outcomes do not own the compared compressed bytes",
    )
    phases = []
    births = set()
    for role in labels:
        phase = terminal["phases"][role]
        identity = phase["oracle_identity"]
        require(
            phase["passed"]
            and identity["version_matches"]
            and identity["sha256"] == old["oracle"]["sha256"]
            and identity["file_version"] == old["oracle"]["build"],
            "unexpected native build or phase",
        )
        births.add(identity["process_creation_filetime"])
        _ = checked(batch / "Inspection" / role / "Record.json", phase["record_sha256"])
        states = phase.get("states", {})
        old_states = previous["phases"][role].get("states", {})
        require(tuple(states) == tuple(old_states), "native states differ: " + role)
        if states:
            require(
                phase["open_errors"] == phase["open_warnings"] == 0
                and phase["immutable_bytes"],
                "native open failed or changed the input: " + role,
            )
        if role.endswith("Generated"):
            _ = checked(
                batch / "Inspection" / role / "Edited.SLDPRT",
                phase["derivative_sha256"],
            )
        phases.append(
            {
                "role": role,
                "passed": True,
                "record_sha256": phase["record_sha256"],
                "numeric_checks": phase.get("numeric_check_count", 0),
                "save_status": phase.get("save_status"),
                "derivative_sha256": phase.get("derivative_sha256"),
                "states": [
                    state_row(name, state, old_states[name])
                    for name, state in states.items()
                ],
            }
        )
    require(
        len(births) == 6 and build["runtime_reads"] == 0 and build["passed"],
        "native lifetimes or guarded build differ",
    )
    receipt = {
        "schema": old["schema"],
        "oracle": old["oracle"],
        "observer_sha256": packet["tools"],
        "packet_sha256": packet_sha,
        "native_result_sha256": digest(terminal_raw),
        "generation_report_sha256": build_sha,
        "frozen_writer_source_sha256": build["frozen_source_sha256"],
        "passed": True,
        "controls_healthy": True,
        "distinct_native_processes": len(births),
        "runtime_input_file_reads": build["runtime_reads"],
        "guarded_processes": 4,
        "fcstd_conversions": 0,
        "heldout_inputs_read": 0,
        "public_registry_in_candidate_trial": False,
        "numeric_checks": sum(phase["numeric_checks"] for phase in phases),
        "builds": build["cases"],
        "cases": terminal["cases"],
        "phases": phases,
        "compression_comparison_sha256": digest(comparison_raw),
    }
    print(
        json.dumps(
            {
                "receipt_sha256": write_json(output, receipt),
                "numeric_checks": receipt["numeric_checks"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("prior", type=Path)
    parser.add_argument("batch", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    record(args.prior, args.batch, args.output)
