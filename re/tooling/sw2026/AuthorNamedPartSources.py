from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import json
import math
import os
from pathlib import Path
import re
import secrets
import string
import time

from AuthorCurves import digest, require, write_json
from AuthorPartDriverNames import TOOLS as DISCOVERY_TOOLS, driver, find_body, measure, save
from AuthorPerpendicularMateSources import TOOLS as PHASE_TOOLS
from AuthorPerpendicularMateSources import SourceRecorder, checked, control, identity, previous, private_root
from AuthorRectangleAnchors import BOSS, CONTROL, ORACLE, SKETCH, RectangleAuthor, rectangle_points


SCHEMA = "kit.sw2026.named-part-prewriter-sources.v1"
TOOLS = DISCOVERY_TOOLS | set(PHASE_TOOLS) | {Path(__file__).name}
IDS = ("H01", "H02")
ROLES = ("width", "height", "depth")
STATES = ("source", *ROLES)
NATIVE_PHASES = ("before", "author", *("reopen-" + state for state in STATES), "after")
PHASES = ("seal", *NATIVE_PHASES, "lock")


def verify(path, expected):
    root = path.parent.resolve(strict=True)
    job = json.loads(checked(path, expected, root).read_bytes())
    require(job["schema"] == SCHEMA and job["oracle_sha256"] == ORACLE and job["control_sha256"] == CONTROL
            and job["writer_output_count"] == 0 and job["heldout_designs_guest_private"] is True,
            "named source packet identity differs")
    require(Path(__file__).resolve().parent == root / "Tools" and set(job["tools_sha256"]) == TOOLS,
            "the named source tooling closure differs")
    require(re.fullmatch(r"C:\\KitNamedPartSources[0-9]{2}", job["guest_private_base"], re.IGNORECASE),
            "choose an unused fixed-drive named source directory")
    for name, wanted in job["tools_sha256"].items():
        checked(root / "Tools" / name, wanted, root / "Tools")
    checked(root / "Control.SLDPRT", CONTROL, root)
    return job


def private_cases():
    def length(first, width):
        return (first + secrets.randbelow(width)) / 1e6

    def word(length):
        return "".join(secrets.choice(string.ascii_lowercase) for unused in range(length)).capitalize()

    return {
        name: {
            "kind": kind,
            "width_m": length(31000, 17000),
            "height_m": length(14000, 13000),
            "depth_m": length(3200, 5900),
            "edit_width_m": length(49000, 16000),
            "edit_height_m": length(28000, 10000),
            "edit_depth_m": length(10200, 4900),
            "drivers": [
                {"role": role, "original_name": original, "feature": feature, "new_name": role.capitalize() + word(7)}
                for role, original, feature in zip(ROLES, ("D1", "D2", "D1"), (SKETCH, SKETCH, BOSS), strict=True)
            ],
            "body_name": ("Solid " if kind == "corner" else "Corps Étage β ") + word(9),
        }
        for name, kind in zip(IDS, ("corner", "center"), strict=True)
    }


def validate(case):
    require(case["kind"] in ("corner", "center") and tuple(row["role"] for row in case["drivers"]) == ROLES,
            "a sealed named source has invalid feature intent")
    require(len({row["new_name"] for row in case["drivers"]}) == len(ROLES), "the three drivers must have distinct names")
    require(all(type(case[role + "_m"]) is float and 0.001 < case[role + "_m"] < 0.2
                and type(case["edit_" + role + "_m"]) is float and case[role + "_m"] != case["edit_" + role + "_m"]
                and 0.001 < case["edit_" + role + "_m"] < 0.2 for role in ROLES),
            "the sealed named part lengths differ from the bounded profile")
    return case


def read_cases(root, job, expected):
    seal = previous(root, "R00", "seal", expected)
    folder = private_root(job, expected, "R00")
    cases = json.loads(checked(folder / "SealedSpecs.json", seal["sealed_spec_sha256"], folder).read_bytes())
    require(tuple(cases) == IDS, "the sealed named source cohort changed")
    return cases


def expected_lengths(case, state):
    return tuple(case[("edit_" if role == state else "") + role + "_m"] for role in ROLES)


def matches_points(actual, expected):
    return all(math.isclose(value, target, abs_tol=1e-10, rel_tol=2e-7)
               for left, right in zip(actual, expected, strict=True)
               for value, target in zip(left, right, strict=True))


def geometry(author, case, width, height):
    part = author.typed(author.model, "PartDoc")
    feature = author.typed(author.get(part, "FeatureByName", SKETCH), "Feature")
    author.sketch = author.typed(author.get(feature, "GetSpecificFeature2"), "Sketch")
    require(author.get(author.sketch, "GetConstrainedStatus") == 3, "the named source sketch lost full constraint")
    rows = author.geometry()
    regular = [row for row in rows if not row["construction"]]
    require(len(regular) == 4 and all(row["kind"] == "line" for row in regular), "the source does not have one four-line contour")
    points = rectangle_points(case["kind"], width, height)
    edges = list(zip(points, points[1:] + points[:1], strict=True))
    for row in regular:
        actual = row["start"], row["end"]
        matches = [edge for edge in edges if matches_points(actual, edge) or matches_points(actual, edge[::-1])]
        require(len(matches) == 1, "a native contour line differs from its independently authored coordinates")
        edges.remove(matches[0])
    return {"sketch_entities": rows, "sketch_relations": author.relation_graph(), "constraint_status": 3}


def snapshot(author, case, state):
    require(author.get(author.model, "ForceRebuild3", False), "the named source did not rebuild")
    actual = measure(author, case, True)
    require(actual["body_name"] == case["body_name"], "the native body label was lost")
    width, height, depth = expected_lengths(case, state)
    for row, expected in zip(case["drivers"], (width, height, depth), strict=True):
        identifier = row["new_name"] + "@" + row["feature"]
        author.rec.close_number("named driving length", actual["drivers_m"][identifier], expected)
    mass = actual["mass"]
    author.rec.close_number("named source solid volume", mass["volume"], width * height * depth, absolute=1e-16)
    author.rec.close_number("named source solid surface", mass["area"], 2 * (width * height + width * depth + height * depth))
    x, y = (width / 2, height / 2) if case["kind"] == "corner" else (0.0, 0.0)
    for observed, expected in zip(mass["com"], (x, y, depth / 2), strict=True):
        author.rec.close_number("named source solid centroid", observed, expected)
    return actual | geometry(author, case, width, height) | {"body_count": 1}


def export_sources(author, controller, case, folder):
    author.build(controller, case)
    for row in case["drivers"]:
        dimension, prior = driver(author, row, False)
        author.rec.close_number("unrenamed owner length", prior, case[row["role"] + "_m"])
        author.set(dimension, "Name", row["new_name"])
    author.set(find_body(author), "Name", case["body_name"])
    author.get(author.get(author.model, "FeatureManager"), "UpdateFeatureTree")
    states = {"source": snapshot(author, case, "source")}
    files = {"source": save_state(author, controller, folder, "source")}
    for row in case["drivers"]:
        role = row["role"]
        key = row["new_name"] + "@" + row["feature"]
        author.edit(key, case["edit_" + role + "_m"])
        states[role] = snapshot(author, case, role)
        require(states[role]["tree"] == states["source"]["tree"], "the native tree changed across an independent named edit")
        files[role] = save_state(author, controller, folder, role)
        author.edit(key, case[role + "_m"])
        restored = snapshot(author, case, "source")
        require(restored["tree"] == states["source"]["tree"], "the restored source tree changed")
    return {"observations": states, "files": files}


def native_path(folder, state):
    return folder / (state.title() + ".SLDPRT")


def save_state(author, controller, folder, state):
    path = native_path(folder, state)
    sha = save(author, controller, path)
    return {"sha256": sha, "bytes": path.stat().st_size}


def assert_files(folder, authored):
    for state in STATES:
        expected = authored["files"][state]
        path = checked(native_path(folder, state), expected["sha256"], folder)
        require(path.stat().st_size == expected["bytes"], "a sealed native source size changed")


def reopen_state(author, controller, case, folder, state, authored):
    assert_files(folder, authored)
    source = native_path(folder, state)
    author.model, error, warning = author.rec.call("open sealed named native source", controller.open, source, read_only=True)
    require(author.model is not None and error == warning == 0
            and Path(author.get(author.model, "GetPathName")).samefile(source), "the sealed native source did not open cleanly")
    actual = snapshot(author, case, state)
    stored = authored["observations"][state]
    require(actual["tree"] == stored["tree"] and actual["body_name"] == stored["body_name"],
            "the named source lost its actual tree or body label after reopening")
    return {"reopened": actual, "open_errors": error, "open_warnings": warning}


def measure_phase(case, phase, private, raw, prior, publish):
    import Swapp
    from OracleIdentity import application_identity

    recorder = SourceRecorder(raw, {"phase": phase, "source": case}, publish)
    controller = author = None
    result = {"passed": False}
    folder = private / "Native"
    with Swapp.Dismisser() as dialogs:
        try:
            recorder.call("confirm idle named source oracle", Swapp.sweep)
            controller = recorder.call("launch fresh named source oracle", Swapp.Sw)
            measured = recorder.call("bind exact named source oracle", application_identity, controller.app)
            result["oracle_identity"] = identity(measured)
            publish(stage="native_source", identity=result["oracle_identity"])
            author = RectangleAuthor(controller.app, recorder, Swapp)
            if phase == "author":
                folder.mkdir(exist_ok=False)
                result.update(export_sources(author, controller, case, folder))
            else:
                result.update(reopen_state(author, controller, case, folder, phase.removeprefix("reopen-"), prior))
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
        finally:
            if controller is not None:
                try:
                    controller.close()
                    result["controller_diagnostics"] = controller.diagnostics
                except Exception as error:
                    recorder.failure(error, cleanup=True)
    result["passed"] = bool(result["passed"] and not dialogs.log and not result.get("controller_diagnostics")
                            and recorder.data["first_failure"] is None and not recorder.data["cleanup_errors"])
    recorder.data.update(result=result, passed=result["passed"])
    recorder.flush()
    require(result["passed"], "the private named source native phase failed")
    assert_files(folder, result if phase == "author" else prior)
    public = {"identity": result["oracle_identity"]}
    if phase == "author":
        record = private / "SavedAuthor.json"
        write_json(record, result)
        public.update(saved_author_sha256=digest(record), native_artifacts=result["files"])
    return public


def execute(root, job, expected, case_id, phase, private, raw, publish):
    if phase == "seal":
        file = private / "SealedSpecs.json"
        require(not file.exists(), "sealed name intent already exists")
        write_json(file, private_cases())
        return {"sealed_spec_sha256": digest(file)}

    cases = read_cases(root, job, expected)
    if phase == "before" and case_id == IDS[1]:
        previous(root, IDS[0], "lock", expected)
    if phase != "before":
        previous(root, case_id, "before", expected)
    if phase in ("before", "after"):
        return control(root / "Control.SLDPRT", raw, publish)
    case = validate(cases[case_id])
    prior = None
    if phase != "author":
        earlier = previous(root, case_id, "author", expected)
        prior = json.loads(checked(private / "SavedAuthor.json", earlier["saved_author_sha256"], private).read_bytes())
        require(prior["passed"], "the sealed native author comparison failed")
    if phase == "lock":
        rows = [previous(root, case_id, step, expected) for step in NATIVE_PHASES]
        identities = {(row["identity"]["process_id"], row["identity"]["process_creation_filetime"]) for row in rows}
        require(len(identities) == len(NATIVE_PHASES), "the source phases did not use fresh native processes")
        assert_files(private / "Native", prior)
        return {"heldout_source_locked": True, "source_manifest_sha256": earlier["saved_author_sha256"],
                "native_artifacts": prior["files"], "fresh_native_processes": len(identities)}
    return measure_phase(case, phase, private, raw, prior, publish)


def run(args, job):
    require(os.name == "nt", "author sealed source cases only inside the Windows guest")
    case_id, phase = args.case_id, args.phase
    expected = args.packet_sha256
    require((case_id == "R00" and phase == "seal") or (case_id in IDS and phase != "seal"), "the named source phase is outside its declared slot")
    root = args.packet.parent
    output = root / "Progress" / case_id / phase
    output.mkdir(parents=True, exist_ok=False)
    state = {"schema": SCHEMA, "packet_sha256": expected, "case_id": case_id, "phase": phase, "stage": "verifying",
             "passed": False, "writer_output_count": 0, "started_at": time.time()}
    allowed = {"identity", "stage", "progress_at", "passed", "finished_at", "private_record_sha256", "sealed_spec_sha256",
               "native_artifacts", "saved_author_sha256", "heldout_source_locked", "source_manifest_sha256", "fresh_native_processes"}

    def publish(**changes):
        require(set(changes) <= allowed, "the named source status cannot expose private observations")
        state.update(changes)
        write_json(output / "Record.json", state)

    publish()
    raw = None
    try:
        private = private_root(job, expected, case_id)
        detail = private / phase
        detail.mkdir(exist_ok=False)
        raw = detail / "Private.json"
        with (detail / "Console.log").open("x", encoding="utf-8") as log, redirect_stdout(log), redirect_stderr(log):
            result = execute(root, job, expected, case_id, phase, private, raw, publish)
            if not raw.exists():
                write_json(raw, result)
            verify(args.packet, expected)
        publish(**result, stage="passed", passed=True, finished_at=time.time(), private_record_sha256=digest(raw))
    except Exception as error:
        if raw is not None:
            write_json(raw.with_name("Failure.json"), {"error": repr(error)})
        publish(stage="failed", passed=False, finished_at=time.time())
    print(json.dumps({key: state[key] for key in ("case_id", "phase", "stage", "passed")}))
    return 0 if state["passed"] else 3


def main():
    parser = argparse.ArgumentParser(description="Author and lock two independently named native rectangles before writer implementation")
    parser.add_argument("command", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--case-id", choices=("R00", *IDS))
    parser.add_argument("--phase", choices=PHASES)
    args = parser.parse_args()
    args.packet = args.packet.resolve(strict=True)
    job = verify(args.packet, args.packet_sha256)
    if args.command == "verify":
        print(json.dumps({"passed": True, "tool_count": len(TOOLS), "native_processes_started": 0}))
        return 0
    require(args.case_id is not None and args.phase is not None, "one actual native phase is required")
    return run(args, job)


if __name__ == "__main__":
    raise SystemExit(main())
