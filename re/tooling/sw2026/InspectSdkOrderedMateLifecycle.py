from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from shutil import copyfile
import sys

from InspectSdkMateReferenceIdentity import base_values, digest, host_path, reference_options, windows_path, write


SCHEMA = "kit.sw2026.sdk-ordered-mate-lifecycle.v3"
TOOLS = ("InspectSdkMateReferenceIdentity.py", Path(__file__).name)


def prepare(args):
    original = args.probe_packet.resolve(strict=True)
    if digest(original) != args.probe_packet_sha256:
        raise ValueError("the qualified matched-reference packet differs")
    probe = json.loads(original.read_bytes())
    if probe["schema"] != "kit.sw2026.sdk-mate-specific-plane-diagnostic.v1":
        raise ValueError("expected the disclosed matched-reference diagnostic")
    result_path = original.parent / "Inspection/Result.json"
    result = json.loads(result_path.read_bytes())
    if not (result["passed"] and result["controls_healthy"] and result["control_identity_preserved"] and result["immutable_inputs_unchanged"]
            and result["distinct_processes"] == 3 and result["packet_sha256"] == args.probe_packet_sha256):
        raise ValueError("the matched native reference observation has not qualified")
    base = Path(probe["base_packet"]["host_path"])
    values = base_values(base, probe["base_packet"]["sha256"])
    for _, native, expected in values[2].values():
        if digest(host_path(native)) != expected:
            raise ValueError("the first lifecycle retry requires the exact unchanged generated working pair")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    tools = output / "Tools"
    tools.mkdir()
    hashes = {}
    for name in TOOLS:
        copyfile(Path(__file__).parent / name, tools / name)
        hashes[name] = digest(tools / name)
    if hashes["InspectSdkMateReferenceIdentity.py"] != probe["observer_sha256"]:
        raise ValueError("the matched reference observer implementation changed")
    copyfile(result_path, output / "ReferenceProbeResult.json")
    job = {"schema": SCHEMA, "base_packet": probe["base_packet"], "reference_probe_packet_sha256": args.probe_packet_sha256,
           "reference_probe_result_sha256": digest(result_path), "tools_sha256": hashes,
           "heldout_inputs_read": 0, "writer_source_changed": False,
           "method": {"repeated_reference_equality": 1,
                      "repeated_specific_plane_equality": 1, "specific_plane_codes_both_lanes": "retained diagnostic; exact semantic endpoint and live edit remain required",
                      "ordered_trees_configurations_geometry_and_all_constraints": "strict", "save_order": ["child", "parent"]}}
    sha = write(output / "Packet.json", job)
    recipe = {"verify": ["py", "-3.11", "-B", windows_path(tools / Path(__file__).name), "verify", windows_path(output / "Packet.json"), "--packet-sha256", sha],
              "run": ["py", "-3.11", "-B", windows_path(tools / Path(__file__).name), "run", windows_path(output / "Packet.json"), "--packet-sha256", sha],
              "result_windows_path": windows_path(output) + r"\Inspection\Result.json"}
    recipe_sha = write(output / "Recipe.json", recipe)
    return {"packet": str(output / "Packet.json"), "packet_sha256": sha, "observer_sha256": hashes[Path(__file__).name],
            "recipe_sha256": recipe_sha, "reference_probe_result_sha256": job["reference_probe_result_sha256"], "native_processes_started": 0}


def verify(packet, expected, *, working=True):
    if digest(packet) != expected:
        raise ValueError("the frozen lifecycle method differs")
    job = json.loads(packet.read_bytes())
    if job["schema"] != SCHEMA or job["heldout_inputs_read"] != 0 or job["writer_source_changed"] is not False:
        raise ValueError("expected the disclosed no-writer-change lifecycle retry")
    tools = (packet.parent / "Tools").resolve(strict=True)
    if Path(__file__).resolve().parent != tools or set(job["tools_sha256"]) != set(TOOLS):
        raise ValueError("the lifecycle source closure differs")
    for name, sha in job["tools_sha256"].items():
        if digest(tools / name) != sha:
            raise ValueError("a lifecycle source changed")
    result_path = packet.parent / "ReferenceProbeResult.json"
    if digest(result_path) != job["reference_probe_result_sha256"]:
        raise ValueError("the independent matched native reference evidence differs")
    result = json.loads(result_path.read_bytes())
    if not result["passed"] or not result["controls_healthy"] or result["distinct_processes"] != 3 or result["packet_sha256"] != job["reference_probe_packet_sha256"]:
        raise ValueError("the matched reference precondition is incomplete")
    key = "windows_path" if os.name == "nt" else "host_path"
    values = base_values(Path(job["base_packet"][key]), job["base_packet"]["sha256"])
    if working:
        for _, native, sha in values[2].values():
            actual = Path(native) if os.name == "nt" else host_path(native)
            if digest(actual) != sha:
                raise ValueError("the owned generated working pair changed before the lifecycle retry")
    return job, values


def checked_references(author, model, child, prediction, case):
    result = reference_options(author, model, child, prediction, case)
    for mate in result["ordered_reference_diagnostics"]:
        for entity in mate["entities"]:
            if entity["reference_type"] != 4 or entity["repeated_reference_equality"] != 1:
                raise ValueError("the native endpoint lost its datum type or repeated-reference positive control")
            for candidate in entity["comparisons"]:
                if candidate["repeated_specific_plane_equality"] != 1 or candidate["specific_plane_equality"] not in (0, 1) or candidate["feature_equality"] not in (0, 1):
                    raise ValueError("the native reference equality probe is invalid")
    return result


def run(packet, expected):
    if os.name != "nt":
        raise ValueError("only the pinned serial Windows oracle can execute this lifecycle")
    job, values = verify(packet, expected)
    fixture, prediction, paths, control, source, case, edit = values
    from AuthorCurves import write_json
    from InspectCombinedPlanarMates import phase, signature
    from SdkOrderedMateExpectations import state_matches

    output = packet.parent / "Inspection"
    output.mkdir()
    phases = {}
    report = {"schema": SCHEMA, "packet_sha256": expected, "base_packet_sha256": job["base_packet"]["sha256"],
              "reference_probe_result_sha256": job["reference_probe_result_sha256"], "phases": phases,
              "heldout_inputs_read": 0, "writer_source_changed": False, "passed": False}
    generated = {"case": case, "child_size_m": [prediction["child_dimensions_m"][key] for key in ("width", "height", "depth")],
                 "edit_distance_m": prediction["edit"]["new_value_m"]}
    targets = tuple(Path(paths[key][1]) for key in ("assembly", "child"))

    def record(role, selected, selected_edit, chosen_paths, wanted, **options):
        def observe(author, model, child):
            return checked_references(author, model, child, wanted, selected["case"])

        row = phase(selected, selected_edit, role, *chosen_paths, output / role, observe=observe, **options)
        phases[role] = row
        write_json(output / "Result.json", report)
        return row

    try:
        before = record("ControlBefore", control, control["case"], source, None)
        if before["passed"]:
            first = record("Generated", generated, edit, targets, prediction, editing=True)
            if first["passed"]:
                final = record("FreshReopen", generated, edit, targets, prediction, reopened=first["saved"])
                report["exact_prediction"] = bool(
                    all(state_matches(first[key], prediction["initial"], prediction) for key in ("initial", "rebuilt"))
                    and state_matches(first["edited"], prediction["edited"], prediction) and final["passed"]
                    and all(state_matches(final[key], prediction["edited"], prediction) for key in ("initial", "rebuilt")))
                report["edit_identity_preserved"] = signature(first["rebuilt"]) == signature(first["edited"])
                report["reopen_identity_preserved"] = bool(final["passed"] and signature(first["edited"]) == signature(final["rebuilt"]))
    except Exception as error:
        report["error"] = repr(error)
    finally:
        after = record("ControlAfter", control, control["case"], source, None)
        checked_fixture = verify(packet, expected, working=False)[1][0]
        healthy = bool(phases.get("ControlBefore", {}).get("passed") and after["passed"])
        report["controls_healthy"] = healthy
        report["source_bracket_identity"] = bool(healthy and signature(phases["ControlBefore"]["rebuilt"]) == signature(after["rebuilt"]))
        births = {row["oracle_identity"]["process_creation_filetime"] for row in phases.values() if row.get("oracle_identity")}
        report.update(distinct_processes=len(births), frozen_inputs_unchanged=checked_fixture == fixture)
        report["passed"] = bool(report["source_bracket_identity"] and report["frozen_inputs_unchanged"] and report.get("exact_prediction")
                                and report.get("edit_identity_preserved") and report.get("reopen_identity_preserved")
                                and len(phases) == len(births) == 4 and all(row["passed"] for row in phases.values()))
        write_json(output / "Result.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description="Measure the ordered SDK lifecycle with matched COM identity evidence")
    commands = parser.add_subparsers(dest="command", required=True)
    make = commands.add_parser("prepare")
    make.add_argument("--probe-packet", type=Path, required=True)
    make.add_argument("--probe-packet-sha256", required=True)
    make.add_argument("--output", type=Path, required=True)
    for name in ("verify", "run"):
        child = commands.add_parser(name)
        child.add_argument("packet", type=Path)
        child.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        report = prepare(args)
    elif args.command == "verify":
        verify(args.packet.resolve(strict=True), args.packet_sha256)
        forbidden = [name for name in sys.modules if name == "Swapp" or name == "pythoncom" or name.startswith("win32com")]
        if forbidden:
            raise ValueError("the lifecycle host preflight imported COM")
        report = {"passed": True, "com_imports": forbidden, "native_processes_started": 0}
    else:
        report = run(args.packet.resolve(strict=True), args.packet_sha256)
    print(json.dumps(report if args.command != "run" else {key: report[key] for key in ("passed", "controls_healthy", "distinct_processes")}, sort_keys=True))
    return 0 if report.get("passed", True) else 3


if __name__ == "__main__":
    raise SystemExit(main())
