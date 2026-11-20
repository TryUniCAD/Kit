from argparse import ArgumentParser
import json
import os
from pathlib import Path
import re

from AuthorRevolveSources import run_phase
from AuthorCurves import digest, write_json
from InspectFresh import healthy, inspect


ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
CONTROL = "28e1f9cd045a7a264b2bdf8658ae593744d65ca708def4a48199ec357f063ab0"
CASE = {
    "name": "PrincipalRevolveRightReverse",
    "split": "discovery",
    "plane": "right",
    "radius_m": [0.0113, 0.0347],
    "axial_m": [-0.0169, 0.0122],
    "axis_x_m": 0.0093,
    "axis_axial_m": [-0.0219, 0.0202],
    "angle_deg": 87.5,
    "edit_angle_deg": 138.25,
    "reverse": True,
}


def control_phase(path, output):
    record = {}
    try:
        if digest(path) != CONTROL:
            raise ValueError("native control digest changed")
        inspect(path, result=record)
    except Exception as error:
        record["exception"] = repr(error)
    write_json(output, record)
    identity = record.get("oracle_identity", {})
    passed = (
        healthy(record) and record["sha256"] == CONTROL
        and identity.get("sha256") == ORACLE
        and identity.get("file_version") == "34.5.2.0604"
    )
    return {
        "passed": passed, "record_sha256": digest(output),
        "birth": identity.get("process_creation_filetime"),
    }


def capture(output, control, checkout, revision):
    if os.name != "nt" or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("run the independent source capture inside the native oracle")
    output = output.resolve()
    checkout = checkout.resolve(strict=True)
    control = control.resolve(strict=True)
    if (
        output.exists() or output.is_relative_to(checkout)
        or not output.parent.is_dir() or digest(control) != CONTROL
    ):
        raise ValueError("select an unused guest output directory and the pinned control")
    output.mkdir()
    source = output / (CASE["name"] + ".SLDPRT")
    before = control_phase(control, output / "ControlBefore.json")
    cases = []
    try:
        if before["passed"]:
            author, author_pin = run_phase(CASE, "author", source, ORACLE)
            cases.append((author, author_pin))
            if author["passed"]:
                reopened, reopen_pin = run_phase(
                    CASE, "reopen", source, ORACLE, author["native_sha256"],
                    inspect_profile=True,
                )
                cases.append((reopened, reopen_pin))
    finally:
        after = control_phase(control, output / "ControlAfter.json")
    phases = [
        {
            "phase": row["job"]["phase"],
            "passed": row["passed"],
            "record_sha256": pin,
            "birth": row.get("oracle_identity", {}).get("process_creation_filetime"),
        }
        for row, pin in cases
    ]
    births = {row["birth"] for row in (before, *phases, after)} - {None}
    native_source = cases[0][0] if cases else {}
    edited = len(cases) == 2 and cases[1][0].get("edit", {}).get("passed") is True
    passed = (
        before["passed"] and after["passed"] and edited
        and all(row["passed"] for row in phases) and len(births) == 4
    )
    source_tools = (
        "CapturePrincipalRevolveControl.py", "AuthorRevolveSources.py", "AuthorCurves.py",
        "InspectFresh.py", "OracleIdentity.py", "Swapp.py",
    )
    result = {
        "schema": "kit.sw2026.principal-revolve-disclosed-source.v1",
        "source_revision": revision, "oracle_sha256": ORACLE, "oracle_version": "34.5.2.0604",
        "case": CASE, "control_sha256": CONTROL, "control_before": before, "control_after": after,
        "native_sha256": native_source.get("native_sha256"),
        "native_bytes": native_source.get("native_bytes"), "source_phases": phases,
        "driving_angle_edit": edited, "distinct_processes": len(births),
        "writer_outputs": 0, "sealed_sources_read": 0, "passed": passed,
        "tool_sha256": {name: digest(Path(__file__).with_name(name)) for name in source_tools},
    }
    write_json(output / "Source.json", result)
    return result


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--control", required=True, type=Path)
    parser.add_argument("--checkout", required=True, type=Path)
    parser.add_argument("--source-revision", required=True)
    args = parser.parse_args()
    result = capture(args.output, args.control, args.checkout, args.source_revision)
    print(json.dumps({
        "passed": result["passed"], "distinct_processes": result["distinct_processes"],
        "native_sha256": result["native_sha256"], "receipt_sha256": digest(args.output / "Source.json"),
    }, sort_keys=True))
    raise SystemExit(0 if result["passed"] else 3)
