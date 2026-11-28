from __future__ import annotations

import argparse
import json
from pathlib import Path, PureWindowsPath

import AuthorCurves as curves
from BlindDrawingSemantics import compare_lanes, complete_observations
from InspectFrontDrawingMap import TOOL_NAMES as FRONT_TOOLS
from InspectScaledDrawing import ORACLE_SHA256, input_files, observe, relative_file


SCHEMA = "kit.sw2026.blind-standard-drawing-oracle-packet.v1"
RESULT_SCHEMA = "kit.sw2026.blind-standard-drawing-oracle-result.v1"
TOOL_NAMES = (*FRONT_TOOLS, "InspectScaledDrawing.py", "BlindDrawingSemantics.py", "InspectBlindDrawing.py")
ORIGINAL_LOCK = "60dc068659185e981419d7a09006dd8358fb46896150fad8dcc8cb8414d4f1a7"
ORIGINAL_SPECS = "2174e5c33aa724610eb90723125281953634bf0d9dd5cd7be65e18339e20c9f1"
HELDOUT_NAMES = ("H01SheetA", "H02SheetB")


def read_packet(packet, packet_sha, tools_sha, runner_sha):
    curves.require(curves.digest(packet) == packet_sha, "blind drawing packet changed")
    tool_file = Path(__file__).with_name("GuestTools.json")
    curves.require(curves.digest(tool_file) == tools_sha, "blind drawing tools manifest changed")
    tools = json.loads(tool_file.read_bytes())
    curves.require(set(tools) == set(TOOL_NAMES), "blind drawing observer dependency set differs")
    for name, expected in tools.items():
        curves.require(curves.digest(tool_file.with_name(name)) == expected, f"blind drawing observer changed: {name}")
    curves.require(curves.digest(Path(__file__)) == tools["InspectBlindDrawing.py"] == runner_sha, "blind drawing runner changed")
    job = json.loads(packet.read_bytes())
    curves.require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE_SHA256 and job["native_acceptance"] is False,
                   "blind drawing oracle identity differs")
    curves.require(job["mode"] in ("disclosed", "heldout") and job["comparison_exclusions"] == {
        "path_role_fields": ["reference_name", "resolved_reference_path"], "volatile_fields": ["child_update_stamp"]},
        "blind drawing comparison contract differs")
    if job["mode"] == "heldout":
        curves.require(job["source_lock_sha256"] == ORIGINAL_LOCK and job["source_specs_sha256"] == ORIGINAL_SPECS
                       and tuple(case["name"] for case in job["cases"]) == HELDOUT_NAMES
                       and job["writer_discovery_profile_qualified"], "blind drawing original registration/profile differs")
    for name, expected in job["source_artifacts"].items():
        curves.require(curves.digest(relative_file(packet.parent, name)) == expected,
                       f"blind drawing generation/comparison artifact changed: {name}")
    host = json.loads((packet.parent / "HostPreparation.json").read_bytes())
    lock = json.loads((packet.parent / "SourceLock.json").read_bytes())
    curves.require(host["source_lock_sha256"] == job["source_lock_sha256"]
                   and host["source_specs_sha256"] == job["source_specs_sha256"]
                   and not host["author_observations_read"] and not host["native_source_payloads_read"],
                   "blind generation and native comparison lost their separation")
    host_cases = {case["name"]: case for case in host["cases"]}
    registered = {case["name"]: case for case in lock["cases"]}
    admitted = []
    for case in job["cases"]:
        if case["state"] == "unsupported_before_oracle":
            curves.require(case["writer_output_count"] == 0 and case["reasons"], "unsupported blind drawing emitted output")
            continue
        curves.require(case["state"] == "admitted_host_generated" and case["writer_output_count"] == 2,
                       "blind drawing generation state differs")
        curves.require(case["generated"] == host_cases[case["name"]], "native comparison changed a frozen generated case")
        curves.require(case["source"]["drawing"]["sha256"] == registered[case["name"]]["native_sha256"]
                       and case["source"]["part"]["sha256"] == registered[case["name"]]["reference_part_sha256"],
                       "native comparison source differs from its original registered case")
        admitted.append(case)
    control = job["control"]
    curves.require(control["drawing"]["sha256"] == registered[control["source_case"]]["native_sha256"]
                   and control["part"]["sha256"] == registered[control["source_case"]]["reference_part_sha256"],
                   "blind native bracket differs from its registered pristine source")
    for row in [job["control"], *(row for case in admitted for row in (case["source"], case["generated"]))]:
        for kind, suffix in (("drawing", ".slddrw"), ("part", ".sldprt")):
            name = PureWindowsPath(row[kind]["filename"])
            curves.require(name.name == row[kind]["filename"] and name.suffix.casefold() == suffix,
                           "blind drawing input filename differs")
        for path, item in zip(input_files(packet.parent, row), (row["drawing"], row["part"]), strict=True):
            curves.require(path.stat().st_size == item["bytes"] and curves.digest(path) == item["sha256"],
                           "blind drawing native/generated input changed")
    return job


def run(packet, packet_sha, tools_sha, runner_sha):
    job = read_packet(packet, packet_sha, tools_sha, runner_sha)
    import Swapp
    from OracleIdentity import application_identity

    output = packet.parent / "BlindDrawingResults"
    output.mkdir(exist_ok=False)
    admitted = [case for case in job["cases"] if case["state"] == "admitted_host_generated"]
    result = {"schema": RESULT_SCHEMA, "mode": job["mode"], "packet_sha256": packet_sha,
              "tools_sha256": tools_sha, "runner_sha256": runner_sha, "source_lock_sha256": job["source_lock_sha256"],
              "source_specs_sha256": job["source_specs_sha256"], "lanes": {}, "cases": []}

    def measure(name, row, tree):
        lane = observe(Swapp, application_identity, root=packet.parent, row=row, name=name, output=output,
                       oracle=job["oracle_sha256"], tree=tree)
        result["lanes"][name] = lane
        curves.write_json(output / "Progress.json", result)
        return lane

    tree = None
    with complete_observations():
        try:
            before = measure("ControlBefore", job["control"], None)
            if before["passed"]:
                tree = before["open_edit_save"]["tree"]
                for case in admitted:
                    source = measure(case["name"] + "Source", case["source"], None)
                    generated = measure(case["name"] + "Generated", case["generated"], case["generated"]["tree"])
                    compared = compare_lanes(source, generated)
                    result["cases"].append({"name": case["name"], "state": "qualified_pass" if compared["passed"] else "native_mismatch",
                                            "passed": compared["passed"], "comparison": compared})
        except Exception as error:
            result["batch_error"] = str(error)
        finally:
            try:
                measure("ControlAfter", job["control"], tree)
            except Exception as error:
                result["final_control_error"] = str(error)
    try:
        read_packet(packet, packet_sha, tools_sha, runner_sha)
        immutable = True
    except Exception as error:
        immutable = False
        result["final_custody_error"] = str(error)
    lanes = result["lanes"]
    phases = [value for lane in lanes.values() for value in (lane["open_edit_save"], lane["fresh_reopen"]) if value is not None]
    identities = {(row["oracle_identity"]["process_id"], row["oracle_identity"]["process_creation_filetime"])
                  for row in phases if "oracle_identity" in row}
    controls = all(lanes.get(name, {}).get("passed") for name in ("ControlBefore", "ControlAfter"))
    expected_processes = 4 + 4 * len(admitted)
    result.update(input_files_immutable=immutable, controls_healthy=controls, distinct_processes=len(identities),
                  expected_processes=expected_processes, phase_count=len(phases),
                  interpretable=bool(controls and immutable and len(identities) == len(phases)))
    for case in job["cases"]:
        if case["state"] == "unsupported_before_oracle":
            result["cases"].append({**case, "passed": False})
    if not controls:
        for case in result["cases"]:
            case["state"], case["passed"] = "uninterpretable_controls", False
    result["paired_semantic_profile_passed"] = bool(
        result["interpretable"] and len(identities) == len(phases) == expected_processes
        and len(result["cases"]) == len(job["cases"]) and all(case["passed"] for case in result["cases"])
        and all(lane["passed"] for lane in lanes.values()) and not any(name in result for name in
            ("batch_error", "final_control_error", "final_custody_error"))
    )
    result["drawing_layout_heldout_profile_passed"] = bool(job["mode"] == "heldout" and result["paired_semantic_profile_passed"])
    result["complete_cad_acceptance"] = False
    curves.write_json(output / "BlindDrawingResults.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description="Compare frozen original drawing layouts and generated pairs through the owned oracle")
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--tools-sha256", required=True)
    parser.add_argument("--runner-sha256", required=True)
    parser.add_argument("--verify-only", action="store_true")
    arguments = parser.parse_args()
    packet = arguments.packet.resolve()
    if arguments.verify_only:
        read_packet(packet, arguments.packet_sha256, arguments.tools_sha256, arguments.runner_sha256)
        print(json.dumps({"custody_verified": True, "vendor_runtime_executed": False}))
        return 0
    result = run(packet, arguments.packet_sha256, arguments.tools_sha256, arguments.runner_sha256)
    print(json.dumps({key: result[key] for key in ("paired_semantic_profile_passed", "drawing_layout_heldout_profile_passed",
                                                  "controls_healthy", "distinct_processes", "input_files_immutable")}))
    return 0 if result["paired_semantic_profile_passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
