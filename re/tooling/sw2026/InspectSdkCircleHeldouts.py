from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import time

import AuthorCurves
import InspectCircleSketch as base
from InspectFresh import healthy, inspect
import Swapp

from CompareSdkCircleHeldouts import check_extra, compare_phases
from SdkCircleHeldoutRules import require


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def extreme_bounds(author, body):
    rows = []
    for axis in range(3):
        values = []
        for sign in (-1.0, 1.0):
            direction = [0.0, 0.0, 0.0]
            direction[axis] = sign
            outputs = [Swapp.VARIANT(Swapp.pythoncom.VT_BYREF | Swapp.pythoncom.VT_R8, 0.0) for _ in range(3)]
            answer = author.get(body, "GetExtremePoint", *direction, *outputs)
            if isinstance(answer, tuple):
                require(len(answer) == 4 and bool(answer[0]), "typed extreme point did not return its boolean and coordinates")
                coordinates = [float(value) for value in answer[1:]]
            else:
                require(bool(answer), "native body extreme point was not found")
                coordinates = [float(value.value) for value in outputs]
            values.append(coordinates[axis])
        rows.append(values)
    return rows


def extra(author, case, factors):
    bodies = author.get(author.model, "GetBodies2", 0, False) or ()
    require(len(bodies) == 1, "paired circle must expose one actual solid body")
    body = author.typed(bodies[0], "Body2")
    names = list(author.get(author.model, "GetConfigurationNames") or ())
    configuration = author.get(author.model, "GetActiveConfiguration")
    state = {"complete_tree": author.feature_tree(required_names=(case["spec"]["sketch_name"], case["spec"]["feature_name"])),
             "configuration_names": [str(value) for value in names], "active_configuration": str(author.get(configuration, "Name")),
             "solid_count": len(bodies), "visible_solid_count": len(author.get(author.model, "GetBodies2", 0, True) or ()),
             "body_is_solid": bool(author.get(body, "IsSolidBody")),
             "body_topology": {"faces": int(author.get(body, "GetFaceCount")), "edges": int(author.get(body, "GetEdgeCount")),
                               "vertices": len(author.get(body, "GetVertices") or ())},
             "mass_properties": author.rec.call("paired circle independent mass properties", Swapp.mass, author.model),
             "document_density_kg_m3": float(author.get(author.get(author.model, "Extension"), "GetUserPreferenceDouble", 7, 0)),
             "extreme_bounds_m": extreme_bounds(author, body)}
    check_extra(state, case["spec"], case["expected_tree"], factors)
    return state


def configure_observer():
    original_snapshot = base.snapshot
    original_initial = base.initial_state

    def snapshot(author, case, factor=1.0, depth_factor=1.0, reverse_depth_factor=1.0):
        result = original_snapshot(author, case, factor, depth_factor, reverse_depth_factor)
        result["extra"] = extra(author, case, (factor, depth_factor, reverse_depth_factor))
        return result

    def initial(author, case):
        result = original_initial(author, case)
        result["extra"] = extra(author, case, case.get("initial_factors", (1.0, 1.0, 1.0)))
        return result

    base.snapshot = snapshot
    base.initial_state = initial


def verify(packet, expected):
    root = packet.parent.resolve(strict=True)
    require(packet.is_file() and digest(packet) == expected, "native paired job identity differs")
    job = json.loads(packet.read_bytes())
    require(job["schema"] == "kit.sw2026.sdk-circle-original-heldouts-native.v1" and 1 <= len(job["cases"]) <= 2,
            "expected the exact first two original circle cases")
    tools = root / "Tools"
    require(Path(__file__).resolve().parent == tools, "use the frozen native tools beside the packet")
    for name, identity in job["tools_sha256"].items():
        require(digest(tools / name) == identity, "frozen native helper differs: " + name)
    for relative, identity in job["files_sha256"].items():
        path = (root / relative).resolve(strict=True)
        require(path.is_relative_to(root) and not path.is_symlink() and digest(path) == identity, "native input custody differs: " + relative)
    require(job["generator_frozen_before_original_attachment"] is True and
            job["oracle_sha256"] == "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe",
            "native job lost original input ordering or exact oracle identity")
    return job, root


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--verify-only", action="store_true")
    arguments = parser.parse_args()
    job, packet_root = verify(arguments.packet.resolve(), arguments.packet_sha256)
    if arguments.verify_only:
        print(json.dumps({"passed": True, "packet_sha256": arguments.packet_sha256}))
        return 0
    configure_observer()
    output = Path(job["output"])
    require(not output.exists() and not output.resolve().is_relative_to(Path(job["checkout_root"]).resolve()),
            "native result directory must be unused and outside checkout")
    output.mkdir(parents=True)
    result = {"schema": "kit.sw2026.sdk-circle-original-heldout-native-result.v1", "packet_sha256": arguments.packet_sha256,
              "started_at": time.time(), "cases": [], "controls": [], "passed": False, "native_acceptance": False}

    def checkpoint():
        (output / "Result.json").write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n")

    checkpoint()
    before = {"kind": "control_before"}
    result["controls"].append(before)
    control = Path(job["control"])
    inspect(control, result=before, checkpoint=checkpoint)
    before["healthy"] = healthy(before) and before["oracle_identity"]["sha256"] == job["oracle_sha256"]
    try:
        require(before["healthy"], "preflight native control failed")
        for case in job["cases"]:
            row = {"name": case["name"], "lanes": {}, "paired_comparisons": [], "passed": False}
            result["cases"].append(row)
            for lane in ("reference", "generated"):
                lane_case = {**case, "name": case["name"] + ("Reference" if lane == "reference" else "Generated")}
                source = Path(case[lane + "_path"])
                expected = case[lane + "_sha256"]
                require(digest(source) == expected, "paired original changed before measurement")
                phases = []
                row["lanes"][lane] = phases
                for phase in ("open-save", "fresh-reopen", "edited-fresh-reopen"):
                    factors = (1.0, 1.0, 1.0) if phase != "edited-fresh-reopen" else (
                        case["edit_factor"], case["depth_edit_factor"], case.get("reverse_depth_edit_factor", 1.0))
                    lane_case["initial_factors"] = factors
                    current = source if not phases else Path(phases[-1]["saved_path"])
                    observed = base.run_phase(lane_case, phase, current, output, job["oracle_sha256"], checkpoint, *factors)
                    phases.append(observed)
                    require(observed["passed"], "paired circle native lifecycle failed")
                    if lane == "generated":
                        row["paired_comparisons"].append(compare_phases(observed, row["lanes"]["reference"][len(phases) - 1]))
                    checkpoint()
                require(digest(source) == expected, "paired original was modified")
            row["passed"] = len(row["paired_comparisons"]) == 3 and all(value["passed"] for value in row["paired_comparisons"])
            checkpoint()
    except Exception as error:
        result["exception"] = repr(error)
    finally:
        after = {"kind": "control_after"}
        result["controls"].append(after)
        inspect(control, result=after, checkpoint=checkpoint)
        after["healthy"] = healthy(after) and after["oracle_identity"]["sha256"] == job["oracle_sha256"]
        result["controls_healthy"] = len(result["controls"]) == 2 and all(row.get("healthy") for row in result["controls"])
        result["inputs_immutable"] = all(digest(packet_root / relative) == identity for relative, identity in job["files_sha256"].items())
        identities = [row["oracle_identity"] for row in result["controls"] if row.get("oracle_identity")]
        identities += [phase["oracle_identity"] for case in result["cases"] for phases in case["lanes"].values() for phase in phases if phase.get("oracle_identity")]
        result["native_processes"] = len(identities)
        result["distinct_processes"] = len({(row["process_id"], row["process_creation_filetime"]) for row in identities})
        result["cohort_fully_admitted"] = job["cohort_fully_admitted"]
        result["unsupported_inputs_or_owners"] = job["unsupported_inputs_or_owners"]
        result["measurement_passed"] = (result["controls_healthy"] and result["inputs_immutable"] and
                            len(result["cases"]) == len(job["cases"]) and all(row["passed"] for row in result["cases"]) and
                            result["native_processes"] == result["distinct_processes"] == 2 + 6 * len(job["cases"]) and not result.get("exception"))
        result["passed"] = result["measurement_passed"] and result["cohort_fully_admitted"]
        result["native_acceptance"] = result["passed"]
        result["finished_at"] = time.time()
        checkpoint()
    print(json.dumps({"passed": result["passed"], "native_processes": result["native_processes"]}))
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
