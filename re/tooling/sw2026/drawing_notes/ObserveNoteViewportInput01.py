from argparse import ArgumentParser
from json import dumps, loads
from math import isclose
import os
from pathlib import Path

from InspectNoteViewport02 import pose
from ObservePlainNotePresentation01 import CONTROL, ORACLE, digest, phase, publish, require


ROLES = ("ControlBefore", "NativeSource", "Default", "PanA", "PanB", "ControlAfter")
CASES = ("Default", "PanA", "PanB")
SCHEMA = "kit.sw2026.disclosed-drawing-viewport-input.v1"


def verify(path, expected):
    root = path.resolve().parent
    require(digest(path) == expected and Path(__file__).resolve().parent == root / "Tools",
            "unexpected drawing viewport trial identity")
    job = loads(path.read_bytes())
    require(job["schema"] == SCHEMA and job["roles"] == list(ROLES) and job["oracle_sha256"] == ORACLE
            and job["heldout_inputs_read"] == 0 and job["files"]["Control.SLDDRW"] == CONTROL,
            "unexpected drawing viewport trial closure")
    for name, known in (job["files"] | job["tools"]).items():
        require(digest(root / name) == known, "an exact disclosed viewport trial input changed")
    for name in CASES:
        receipt = loads((root / name / "Proof.json").read_bytes())
        require(receipt["runtime_input_reads"] == 0 and receipt["definition_reemit_exact"]
                and receipt["container_sha256"] == job["files"][name + "/Disclosed01.SLDDRW"],
                "the generated drawing viewport candidate is unbound")
    return root, job


def camera_matches(camera, requested):
    return all(isclose(actual, target, rel_tol=1e-12, abs_tol=1e-12) for actual, target in zip(
        (*camera["translation"], camera["zoom"]), (*requested["pan"], requested["zoom"]), strict=True,
    ))


def observe_role(root, job, output, role):
    control = role.startswith("Control")
    name = "Control.SLDDRW" if control else role + "/Disclosed01.SLDDRW"
    intent = None if control else loads((root / role / "Intent.json").read_bytes())
    return phase(output / role, root / name, job["files"][name], intent, observe=pose)


def main():
    parser = ArgumentParser()
    parser.add_argument("mode", choices=("verify", "run", "phase"))
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--role", choices=ROLES)
    args = parser.parse_args()
    root, job = verify(args.job, args.sha256)
    if args.mode == "verify":
        print(dumps({"verified": True, "native_processes": 0}))
        return 0
    require(os.name == "nt", "reserved Windows guest is required")
    output = root / "Inspection01"
    if args.mode == "phase":
        require(args.role is not None, "one exact viewport phase is required")
        output.mkdir(exist_ok=True)
        row = observe_role(root, job, output, args.role)
        verify(args.job, args.sha256)
        result = output / args.role / "Result.json"
        print(dumps({"role": args.role, "passed": row["passed"], "result_sha256": digest(result)}))
        return 0 if row["passed"] else 3
    output.mkdir()
    rows = {}
    placement = {}
    for role in ROLES:
        if role in CASES and not all(rows[name]["passed"] for name in ("ControlBefore", "NativeSource")):
            rows[role] = {"passed": False, "skipped": "leading native controls failed"}
            continue
        rows[role] = observe_role(root, job, output, role)
        if role in ("PanA", "PanB") and rows[role]["passed"]:
            intent = loads((root / role / "Intent.json").read_bytes())
            placement[role] = {
                label: camera_matches(rows[role][label], intent["viewport"])
                for label in ("initial_observation", "rebuilt_observation")
            }
    verify(args.job, args.sha256)
    identities = {row["identity"]["process_creation_filetime"] for row in rows.values() if "identity" in row}
    complete = len(identities) == len(ROLES) and all(row["passed"] for row in rows.values())
    before, after = rows["ControlBefore"], rows["ControlAfter"]
    controls = before["passed"] and after["passed"] and rows["NativeSource"]["passed"] and all(
        before[item] == after[item] for item in ("initial", "bitmap", "initial_observation", "rebuilt_observation")
    )
    differences = {
        role: rows[role]["bitmap"]["sha256"] != before["bitmap"]["sha256"] for role in CASES
        if before["passed"] and rows[role]["passed"]
    }
    result = output / "Result.json"
    summary = {
        "complete": complete, "healthy_controls": controls, "distinct_processes": len(identities),
        "authored_camera_readbacks": placement, "generated_frames_differ_from_pristine": differences,
    }
    publish(result, {
        "schema": SCHEMA, "trial_sha256": args.sha256, **summary, "phases": rows,
        "document_saves": 0, "settings_writes": 0, "heldout_source_reads": 0,
    })
    print(dumps(summary | {"result_sha256": digest(result)}))
    return 0 if complete and controls else 3


if __name__ == "__main__":
    raise SystemExit(main())
