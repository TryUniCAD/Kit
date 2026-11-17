from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import json
import os
from pathlib import Path, PureWindowsPath
import re
import secrets

from AuthorCurves import digest, require, write_json
from AuthorRectangleAnchors import CONTROL, ORACLE, TOOLS, control, phase


SCHEMA = "kit.sw2026.sealed-rectangle-anchor-sources.v1"
DISCLOSED = "0f7836d44b0e0b32d470b28924306ba782bdedd9abbc092ae4cd8570844b25f0"
SEALED_TOOLS = TOOLS | {Path(__file__).name}


def verify(path, sha):
    require(digest(path) == sha, "rectangle source lock packet changed")
    plan = json.loads(path.read_bytes())
    require(plan["schema"] == SCHEMA and plan["control_sha256"] == CONTROL and plan["oracle_sha256"] == ORACLE
            and plan["disclosed_receipt_sha256"] == DISCLOSED and plan["writer_output_count"] == 0, "rectangle source lock scope differs")
    directory = PureWindowsPath(plan["guest_private_root"])
    require(directory.is_absolute() and directory.drive.casefold() == "c:" and len(directory.parts) == 2
            and re.fullmatch(r"KitRectangleAnchorSources[0-9]{2}", directory.name), "choose a new Windows-local anchor source directory")
    root = path.parent
    require(Path(__file__).resolve().parent == root / "Tools" and set(plan["tools_sha256"]) == SEALED_TOOLS,
            "use the complete frozen rectangle source tools")
    for name, expected in plan["tools_sha256"].items():
        require(digest(root / "Tools" / name) == expected, f"rectangle source lock tool changed: {name}")
    require(digest(root / "Control.SLDPRT") == CONTROL and digest(root / "DisclosedReceipt.json") == DISCLOSED,
            "disclosed rectangle evidence or pristine control changed")
    return plan


def private_cases():
    require(os.name == "nt", "held-out rectangle recipes stay in the Windows guest")

    def distance(low_micrometers, span_micrometers):
        return (low_micrometers + secrets.randbelow(span_micrometers)) / 1e6

    return {
        name: {"kind": kind, "width_m": distance(49000, 24001), "height_m": distance(12000, 14001),
               "depth_m": distance(2000, 9001), "edit_width_m": distance(25000, 16001), "edit_height_m": distance(29000, 14001)}
        for name, kind in (("H01", "corner"), ("H02", "center"))
    }


def identity(result):
    value = result["oracle_identity"]
    require(value["version_matches"] and value["sha256"] == ORACLE, "held-out source oracle build differs")
    return {"process_id": value["process_id"], "creation_filetime": value["process_creation_filetime"]}


def run(path, sha):
    plan = verify(path, sha)
    require(os.name == "nt", "sealed source authoring only runs through the Windows guest oracle")
    root = Path(plan["guest_private_root"])
    root.mkdir(exist_ok=False)
    output = path.parent / "RectangleAnchorLockResults"
    output.mkdir(exist_ok=False)
    public = output / "Record.json"
    cases = private_cases()
    recipes = root / "SourceRecipes.json"
    write_json(recipes, cases)
    result = {"schema": SCHEMA, "packet_sha256": sha, "oracle_sha256": ORACLE, "oracle_file_version": "34.5.2.0604",
              "specifications_sha256": digest(recipes), "phases": [], "cases": {}, "passed": False,
              "writer_output_count": 0, "heldout_payloads_shared": 0, "native_acceptance": False}

    def measure(label, function, *args):
        result["stage"] = label
        write_json(public, result)
        record = function(*args)
        result["phases"].append({"phase": label, "passed": record["passed"], "record_sha256": record["record_sha256"],
                                 "identity": identity(record)})
        write_json(public, result)
        require(record["passed"], "one sealed rectangle source phase failed")
        return record

    with (root / "NativeOracle.log").open("x", encoding="utf-8") as log, redirect_stdout(log), redirect_stderr(log):
        try:
            seed = path.parent / "Control.SLDPRT"
            measure("ControlBefore", control, root, "ControlBefore", seed)
            for name, case in cases.items():
                authored = measure(name + "Author", phase, root, case, "Author", None)
                reopened = measure(name + "Reopen", phase, root, case, "Reopen", authored)
                require(all(reopened["files"][role]["sha256"] == row["sha256"] for role, row in authored["files"].items()),
                        "held-out rectangle source hashes changed during fresh reopen")
                artifact_file = root / (name + "Artifacts.json")
                write_json(artifact_file, authored["files"])
                result["cases"][name] = {"family": case["kind"], "native_artifact_manifest_sha256": digest(artifact_file),
                                          "source_record_sha256": authored["record_sha256"],
                                          "reopen_record_sha256": reopened["record_sha256"]}
        except Exception as error:
            result["failure"] = {"stage": result["stage"], "class": type(error).__name__}
            print(repr(error))
        finally:
            try:
                measure("ControlAfter", control, root, "ControlAfter", seed)
            except Exception as error:
                result["final_control_failure"] = type(error).__name__
                print(repr(error))
    verify(path, sha)
    unique = {(row["identity"]["process_id"], row["identity"]["creation_filetime"]) for row in result["phases"]}
    result["distinct_processes"] = len(unique)
    result["controls_healthy"] = [row["passed"] for row in result["phases"] if row["phase"].startswith("Control")] == [True, True]
    result["passed"] = (len(unique) == len(result["phases"]) == 6 and result["controls_healthy"]
                        and tuple(result["cases"]) == ("H01", "H02") and "failure" not in result and "final_control_failure" not in result)
    result["stage"] = "complete" if result["passed"] else "failed"
    write_json(public, result)
    return result


def main():
    parser = argparse.ArgumentParser(description="Lock two independently authored native rectangle source families")
    parser.add_argument("plan", type=Path)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    path = args.plan.resolve()
    if args.verify_only:
        verify(path, args.plan_sha256)
        print(json.dumps({"verified": True, "native_processes": 0, "heldout_payloads_read": 0}))
        return 0
    result = run(path, args.plan_sha256)
    print(json.dumps({name: result[name] for name in ("passed", "controls_healthy", "distinct_processes", "specifications_sha256")}))
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
