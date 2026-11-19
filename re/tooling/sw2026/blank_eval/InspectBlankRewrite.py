from argparse import ArgumentParser
from hashlib import sha256
from json import dumps, loads
from pathlib import Path, PureWindowsPath
from shutil import copyfileobj
import os

from InspectDrawingCache import phase


SCHEMA = "kit.sw2026.preserved-blank-drawing-native.v1"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
CONTROL = "227f12b5834f73e31d1cb64db9e615418852bfba6c30d6c2700be6e26cc4932b"
TOOLS = {
    "InspectBlankRewrite.py", "InspectDrawingCache.py", "DrawingCacheCases.py",
    "AuthorCurves.py", "AuthorDrawingSources.py", "OracleIdentity.py", "Swapp.py",
}
CONTROL_STATE = {
    "sheet": "Sheet1", "sheet_properties": [0, 13, 1.0, 1.0, 0, 11 * 0.0254, 8.5 * 0.0254, 1],
    "view": None, "whats_wrong": 0,
}


def require(value, reason):
    if not value:
        raise ValueError(reason)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def read_job(path, expected):
    root = path.resolve().parent
    require(digest(path) == expected, "rewrite observation recipe changed")
    job = loads(path.read_bytes())
    require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE
            and job["control_sha256"] == CONTROL, "rewrite observation build or control differs")
    require(Path(__file__).resolve().parent == root / "OracleTools"
            and job["tools_sha256"].keys() == TOOLS, "rewrite observation tool closure differs")
    for name, proof in job["tools_sha256"].items():
        require(digest(root / "OracleTools" / name) == proof, "native observation tool changed")
    require(digest(root / "Control.SLDDRW") == CONTROL, "pristine blank control changed")
    require(tuple(job["cases"]) == ("PublicAlpha", "SdkAlpha"), "rewrite lanes differ")
    for case, row in job["cases"].items():
        source = (root / row["source"]).resolve(strict=True)
        target = PureWindowsPath(row["native_path"])
        info = root / (case + ".json")
        require(source.is_relative_to(root) and source.name == target.name
                and target.is_absolute() and target.drive.upper() == "C:"
                and target.suffix.upper() == ".SLDDRW", "rewrite self-file locator differs")
        require(digest(info) == row["proof_sha256"] and digest(source) == row["sha256"],
                "rewrite proof or candidate differs")
        proof = loads(info.read_bytes())
        require(proof["passed"] and proof["native_flags"] == [False, False]
                and proof["runtime_input_reads"] == proof["private_slot_reads"] == 0
                and proof["target"]["sha256"] == row["sha256"]
                and proof["actual_self_path"] == row["native_path"]
                and proof["expected_initial"] == row["initial"]
                and proof["expected_tree"] == row["tree"]
                and proof["edit_scale_ratio"] == row["edit_ratio"],
                "rewrite intent or previous host attestation differs")
    return root, job


def run(root, job, job_digest):
    require(os.name == "nt", "native rewrite verification requires the reserved Windows guest")
    import Swapp
    from OracleIdentity import application_identity

    output = root / "Inspection"
    output.mkdir()
    phases = {}
    report = {"schema": SCHEMA, "job_sha256": job_digest, "phases": phases, "passed": False,
              "heldout_inputs_read": 0, "finished": False}

    def save_progress():
        temporary = output / "Progress.tmp"
        temporary.write_text(dumps(report, indent=2, sort_keys=True) + "\n",encoding="utf-8")
        temporary.replace(output / "Result.json")

    def lifecycle(label, source, source_sha, expected, tree, ratio):
        directory = output / label
        directory.mkdir()
        first = phase(
            Swapp, application_identity, directory=directory / "OpenRebuildEditSave",
            native=source, expected_hash=source_sha, expected=expected,
            tree=tree, oracle_sha=ORACLE, edit=True, edited_ratio=ratio,
        )
        phases[label] = {"first": first}
        save_progress()
        if not first["passed"]:
            return False
        phases[label]["reopen"] = phase(
            Swapp, application_identity, directory=directory / "FreshReopen", edit=False,
            native=directory / "OpenRebuildEditSave/EditedDrawing.SLDDRW",
            expected_hash=first["derivative_sha256"], expected=first["edited"],
            tree=first["tree"], oracle_sha=ORACLE,
        )
        save_progress()
        return phases[label]["reopen"]["passed"]

    control = root / "Control.SLDDRW"
    before = lifecycle("ControlBefore", control, CONTROL, CONTROL_STATE, None, (3.0, 2.0))
    measured = []
    if before:
        for label in ("SdkAlpha", "PublicAlpha"):
            row = job["cases"][label]
            try:
                target = Path(row["native_path"])
                target.parent.mkdir(parents=True, exist_ok=True)
                with (root / row["source"]).open("rb") as input_stream, target.open("xb") as output_stream:
                    copyfileobj(input_stream, output_stream)
                require(digest(target) == row["sha256"], "staged generated drawing bytes differ")
                measured.append(lifecycle(label, target, row["sha256"], row["initial"],
                                          row["tree"], tuple(row["edit_ratio"])))
            except Exception as error:
                phases[label] = {"error": str(error)}
                measured.append(False)
                save_progress()
    baseline_tree = phases["ControlBefore"]["first"].get("tree") if before else None
    after = lifecycle("ControlAfter", control, CONTROL, CONTROL_STATE, baseline_tree, (3.0, 2.0))
    births = {
        state["oracle_identity"]["process_creation_filetime"]
        for states in phases.values() for state in states.values()
        if isinstance(state, dict) and "oracle_identity" in state
    }
    report.update(passed=before and after and measured == [True, True] and len(births) == 8,
                  distinct_processes=len(births), controls_healthy=bool(before and after), finished=True)
    save_progress()
    return report


def main():
    parser = ArgumentParser()
    parser.add_argument("mode", choices=("verify", "run"))
    parser.add_argument("job", type=Path)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    location, job = read_job(args.job, args.sha256)
    if args.mode == "verify":
        print(dumps({"passed": True, "cad_processes_started": 0}))
        return 0
    result = run(location, job, args.sha256)
    print(dumps({key: result[key] for key in ("passed", "distinct_processes", "controls_healthy")}))
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
