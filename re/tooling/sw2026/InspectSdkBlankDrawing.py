from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import AuthorCurves as curves
from DrawingCacheCases import NATIVE_NAME, TOOL_NAMES as CACHE_TOOLS
from InspectDrawingCache import phase


SCHEMA = "kit.sw2026.sdk-blank-native-comparison.v1"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
CONTROL = "227f12b5834f73e31d1cb64db9e615418852bfba6c30d6c2700be6e26cc4932b"
TOOL_NAMES = (*CACHE_TOOLS, Path(__file__).name)


def checked(root, relative, expected):
    path = (root / relative).resolve(strict=True)
    curves.require(path.is_relative_to(root) and path.is_file() and curves.digest(path) == expected,
                   "blank drawing trial file does not match the frozen identity")
    return path


def verify(path, packet_sha):
    root = path.parent.resolve(strict=True)
    job = json.loads(checked(root, path.name, packet_sha).read_bytes())
    curves.require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE
                   and job["heldout_inputs_read"] == 0, "unexpected SDK blank discovery packet")
    tools = root / "Tools"
    curves.require(Path(__file__).resolve().parent == tools and set(job["tools_sha256"]) == set(TOOL_NAMES),
                   "SDK blank drawing tool custody differs")
    for name, value in job["tools_sha256"].items():
        checked(tools, name, value)
    rows = job["inputs"]
    curves.require(set(rows) == {"control", "generated"} and rows["control"]["sha256"] == CONTROL,
                   "blank drawing bracket is not the pinned D00 control")
    files = {name: checked(root, row["path"], row["sha256"]) for name, row in rows.items()}
    curves.require(files["control"].name == NATIVE_NAME and files["generated"].suffix.upper() == ".SLDDRW"
                   and files["generated"] != files["control"], "the trial must contain a distinct generated drawing")
    for row in rows.values():
        curves.require(row["expected"]["view"] is None and len(row["expected"]["sheet_properties"]) == 8,
                       "the SDK blank profile requires a single unlinked sheet")
    proof = json.loads(checked(root, "BuildProof.json", job["generation_proof_sha256"]).read_bytes())
    curves.require(proof["generated_sha256"] == rows["generated"]["sha256"]
                   and proof["runtime_file_reads"] == 0 and proof["identical_guarded_builds"] == 2
                   and proof["full_sdk_archive_construction"] is True,
                   "the SDK blank bytes must be linked to two guarded full builds")
    checked(root, "NeutralRequest.json", proof["request_sha256"])
    curves.require(len(rows["generated"]["expected_tree"]) == 10, "the generated blank tree prediction is incomplete")
    return job, files


def run(path, packet_sha):
    curves.require(os.name == "nt", "blank drawing measurement requires the Windows guest")
    request, files = verify(path, packet_sha)
    import Swapp
    from OracleIdentity import application_identity

    output = path.parent / "Inspection"
    output.mkdir()
    phases = []
    report = {"schema": SCHEMA, "packet_sha256": packet_sha, "phases": phases,
              "heldout_inputs_read": 0, "passed": False}

    def save():
        curves.write_json(output / "Result.json", report)

    def observe(role, name, tree):
        row = request["inputs"][name]
        work = output / role
        first = phase(Swapp, application_identity, directory=work / "OpenEditSave",
                      native=files[name], expected_hash=row["sha256"], expected=row["expected"],
                      tree=tree, oracle_sha=ORACLE, edit=True)
        first["role"] = role + "/OpenEditSave"
        phases.append(first)
        save()
        second = None
        if first["passed"]:
            second = phase(Swapp, application_identity, directory=work / "FreshReopen",
                           native=work / "OpenEditSave" / "EditedDrawing.SLDDRW",
                           expected_hash=first["derivative_sha256"], expected=first["edited"],
                           tree=first["tree"], oracle_sha=ORACLE, edit=False)
            second["role"] = role + "/FreshReopen"
            phases.append(second)
            save()
        return first, bool(first["passed"] and second and second["passed"])

    before = None
    before_pass = candidate_pass = after_pass = False
    try:
        before, before_pass = observe("ControlBefore", "control", None)
        if before_pass:
            _, candidate_pass = observe("Generated", "generated", request["inputs"]["generated"]["expected_tree"])
    finally:
        _, after_pass = observe("ControlAfter", "control", before["tree"] if before_pass else None)
        verified, _ = verify(path, packet_sha)
        stamps = {item.get("oracle_identity", {}).get("process_creation_filetime") for item in phases}
        report.update(controls_healthy=before_pass and after_pass, generated_passed=candidate_pass,
                      immutable_inputs_unchanged=verified == request, distinct_processes=len(stamps - {None}))
        report["passed"] = (report["controls_healthy"] and candidate_pass and report["immutable_inputs_unchanged"]
                            and len(phases) == report["distinct_processes"] == 6)
        save()
    return report


def main():
    parser = argparse.ArgumentParser(description="Verify a fresh SDK blank drawing through native scale edit and save")
    parser.add_argument("command", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    if args.command == "verify":
        verify(args.packet.resolve(strict=True), args.packet_sha256)
        result = {"passed": True, "processes_started": 0}
    else:
        report = run(args.packet.resolve(strict=True), args.packet_sha256)
        result = {name: report[name] for name in ("passed", "controls_healthy", "generated_passed", "distinct_processes")}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
