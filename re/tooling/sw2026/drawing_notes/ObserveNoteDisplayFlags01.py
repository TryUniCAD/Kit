from argparse import ArgumentParser
from json import dumps, loads
import os
from pathlib import Path

from InspectNoteGrid01 import phase
from ObservePlainNotePresentation01 import CONTROL, ORACLE, digest, publish, require


SCHEMA = "kit.sw2026.disclosed-drawing-display-flags.v1"
COMBINATIONS = {
    "GridOffNeither": (False, False, False),
    "GridOffAnnotations": (False, True, False),
    "GridOffAll": (False, False, True),
    "GridOffBoth": (False, True, True),
    "GridOnBoth": (True, True, True),
}
FIELDS = ("swGridDisplay", "swDisplayAnnotations", "swDisplayAllAnnotations")
TOOLS = {
    "AuthorCurves.py", "AuthorDrawingSources.py", "AuthorPlainDrawingNotes.py",
    "DrawingCacheCases.py", "InspectDrawingCache.py", "InspectNoteGrid01.py",
    "ObserveNoteDisplayFlags01.py", "ObservePlainNotePresentation01.py", "OracleIdentity.py", "Swapp.py",
}


def verify(path, expected):
    root = path.resolve().parent
    require(digest(path) == expected, "display flag trial changed")
    job = loads(path.read_bytes())
    require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE
            and job["heldout_inputs_read"] == 0, "wrong display flag trial")
    require(Path(__file__).resolve().parent == root / "Tools" and job["tools"].keys() == TOOLS,
            "display flag helper closure differs")
    for name, proof in job["tools"].items():
        require(digest(root / "Tools" / name) == proof, "display flag helper identity changed")
    files = {"Control.SLDDRW", "GridApi01.json", "Source/Disclosed01.SLDDRW", "Source/Intent.json"}
    files.update(name + suffix for name in COMBINATIONS for suffix in ("/Disclosed01.SLDDRW", "/Proof.json", "/Intent.json"))
    require(job["files"].keys() == files and job["files"]["Control.SLDDRW"] == CONTROL,
            "display flag inputs differ")
    require(job["roles"] == ["ControlBefore", "Source", *COMBINATIONS, "ControlAfter"],
            "display flag role order changed")
    for relative, proof in job["files"].items():
        require(digest(root / relative) == proof, "display flag input identity changed")
    source = loads((root / "Source/Intent.json").read_bytes())
    for name, switches in COMBINATIONS.items():
        request = loads((root / name / "Intent.json").read_bytes())
        proof = loads((root / name / "Proof.json").read_bytes())
        require(
            tuple(request[key] for key in ("display_grid", "display_annotations", "display_all_annotations")) == switches
            and request["detailing_standard"] == 0
            and all(request[key] == source[key] for key in ("initial_text", "initial_position", "sheet", "scale"))
            and proof["runtime_input_reads"] == 0 and proof["definition_reemit_exact"]
            and proof["container_sha256"] == job["files"][name + "/Disclosed01.SLDDRW"],
            "display flag generation receipt differs",
        )
    return root, job


def run(path, expected):
    require(os.name == "nt", "display flag trial must use the reserved Windows guest")
    root, job = verify(path, expected)
    api = loads((root / "GridApi01.json").read_bytes())
    output = root / "Inspection"
    output.mkdir()
    before_names = ("ControlBefore", "Source")
    rows = {}
    for role in job["roles"]:
        control = role in ("ControlBefore", "ControlAfter")
        if role in COMBINATIONS and not all(rows[name]["passed"] for name in before_names):
            rows[role] = {"passed": False, "skipped": "independent controls failed"}
            continue
        if control:
            source_name, intent = "Control.SLDDRW", None
        else:
            source_name = role + "/Disclosed01.SLDDRW"
            intent = loads((root / role / "Intent.json").read_bytes())
            if role in COMBINATIONS:
                require((root / source_name).samefile(intent["locator"]), "candidate does not use its actual generated locator")
        rows[role] = phase(output / role, root / source_name, job["files"][source_name], intent, api)
    verify(path, expected)
    births = {row["identity"]["process_creation_filetime"] for row in rows.values() if "identity" in row}
    control_names = (*before_names, "ControlAfter")
    healthy = all(rows[name]["passed"] for name in control_names)
    matches = {
        name: tuple(row["preference_state"]["toggles"][key] for key in FIELDS) == COMBINATIONS[name]
        for name, row in rows.items() if name in COMBINATIONS and row["passed"]
    }
    complete = len(births) == len(job["roles"]) and all(row["passed"] for row in rows.values())
    if healthy:
        healthy = rows["ControlBefore"]["after_rebuild"] == rows["ControlAfter"]["after_rebuild"]
    result = output / "Result.json"
    publish(result, {
        "schema": SCHEMA, "job_sha256": expected, "complete": complete, "healthy_controls": healthy,
        "distinct_processes": len(births), "observed_expected_switches": matches,
        "settings_writes": 0, "heldout_source_reads": 0, "phases": rows,
    })
    print(dumps({
        "complete": complete, "healthy_controls": healthy, "expected_switches": matches,
        "distinct_processes": len(births), "result_sha256": digest(result),
    }))
    return 0 if complete and healthy and all(matches.values()) else 3


def main():
    parser = ArgumentParser()
    parser.add_argument("mode", choices=("verify", "run"))
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    if args.mode == "run":
        return run(args.job, args.sha256)
    verify(args.job, args.sha256)
    print(dumps({"verified": True, "native_processes": 0, "heldout_source_reads": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
