from __future__ import annotations

import sys
from pathlib import Path

sys.path[:] = [
    value
    for value in sys.path
    if Path(value or ".").resolve() != Path(__file__).resolve().parent
]
sys.path.append(str(Path(__file__).resolve().parent))

import argparse
from contextlib import redirect_stderr, redirect_stdout
import ctypes
import json
import os
import time

from AuthorCurves import Recorder, digest, require, write_json
from AuthorDrawingSources import (
    compare_states,
    make_drawing,
    set_view_position,
    snapshot as drawing_snapshot,
)
from AuthorRectangleAnchors import BOSS, SKETCH, RectangleAuthor
from OriginProfileSourcePlan import (
    DISCLOSED,
    HIDDEN,
    SCHEMA as SPEC_SCHEMA,
    disclosed_cases,
    hidden_cases,
    validate,
)

SCHEMA = "kit.sw2026.origin-profile-prewriter-source-packet.v1"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
CONTROL = "c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57"
TOOLS = {
    Path(__file__).name,
    "OriginProfileSourcePlan.py",
    "AuthorCurves.py",
    "AuthorDrawingSources.py",
    "AuthorRectangleAnchors.py",
    "InspectFresh.py",
    "OracleIdentity.py",
    "Swapp.py",
}
NATIVE_PHASES = ("author", "reopen-source", "move-save", "reopen-moved")
PHASES = ("seal", "before", *NATIVE_PHASES, "after", "lock", "export-disclosed")


def checked(path, expected, owner=None):
    require(
        path.is_file()
        and not path.is_symlink()
        and (owner is None or path.resolve().is_relative_to(owner.resolve()))
        and digest(path) == expected,
        "a frozen origin source input changed",
    )
    return path


def verify(path, expected):
    root = path.parent.resolve(strict=True)
    job = json.loads(checked(path, expected, root).read_bytes())
    require(
        job["schema"] == SCHEMA
        and job["oracle_sha256"] == ORACLE
        and job["control_sha256"] == CONTROL
        and job["writer_output_count"] == 0
        and job["heldout_designs_guest_private"] is True
        and job["native_acceptance"] is False,
        "use the exact source-only origin packet",
    )
    require(
        Path(__file__).resolve().parent == root / "Tools"
        and set(job["tools_sha256"]) == TOOLS,
        "the frozen origin author tools differ",
    )
    for name, sha in job["tools_sha256"].items():
        checked(root / "Tools" / name, sha, root / "Tools")
    checked(root / "RunPlan.json", job["run_plan_sha256"], root)
    checked(root / "README.md", job["readme_sha256"], root)
    checked(root / "Control.SLDPRT", CONTROL, root)
    checked(Path(job["drawing_template"]), job["drawing_template_sha256"])
    require(
        job["paper_size"] == 0
        and job["native_hooks"] == 0
        and job["source_saved_bytes_used_in_writer"] is False,
        "the source authoring scope differs",
    )
    require(
        job["case_ids"] == {"disclosed": list(DISCLOSED), "hidden": list(HIDDEN)},
        "the source cohort inventory differs",
    )
    data = json.loads(
        checked(root / "Disclosed.json", job["disclosed_sha256"], root).read_bytes()
    )
    require(
        data == {"schema": SPEC_SCHEMA, "cases": disclosed_cases()},
        "the disclosed origin request changed",
    )
    return job


def private_root(job, expected, cohort, identifier):
    require(os.name == "nt", "native authoring requires the reserved Windows oracle")
    root = Path(job["guest_private_base"])
    drive = ctypes.windll.kernel32.GetDriveTypeW
    drive.argtypes, drive.restype = (ctypes.c_wchar_p,), ctypes.c_uint
    require(
        root.is_absolute()
        and root.resolve() == root
        and drive(root.anchor) == 3
        and not root.is_symlink(),
        "sealed source custody requires a canonical fixed guest drive",
    )
    result = root / expected / cohort / identifier
    result.mkdir(parents=True, exist_ok=True)
    return result


def prior(root, cohort, identifier, phase, expected):
    row = json.loads(
        (root / "Progress" / cohort / identifier / phase / "Record.json").read_bytes()
    )
    require(
        row["packet_sha256"] == expected
        and row["cohort"] == cohort
        and row["case_id"] == identifier
        and row["phase"] == phase
        and row["stage"] == "passed"
        and row["passed"] is True,
        "an origin source phase prerequisite failed or is missing",
    )
    return row


def case_input(root, job, expected, cohort, identifier):
    sealed = prior(root, cohort, "C00", "seal", expected)
    directory = private_root(job, expected, cohort, "C00")
    data = json.loads(
        checked(
            directory / "SealedSpecs.json", sealed["sealed_spec_sha256"], directory
        ).read_bytes()
    )
    ids = DISCLOSED if cohort == "disclosed" else HIDDEN
    require(
        data["schema"] == SPEC_SCHEMA
        and tuple(row["id"] for row in data["cases"]) == ids,
        "the sealed source cohort changed",
    )
    return validate(next(row for row in data["cases"] if row["id"] == identifier))


class SourceRecorder(Recorder):
    def __init__(self, path, job, publish):
        self.publish, self.last_public = publish, float("-inf")
        super().__init__(path, job)

    def flush(self):
        super().flush()
        now = time.monotonic()
        if now - self.last_public >= 1:
            self.publish(progress_at=time.time())
            self.last_public = now


def feature_owners(author, child):
    rows, seen, steps = [], set(), 0

    def visit(feature, parent, depth):
        nonlocal steps
        require(depth <= 16, "native child feature depth exceeded its bound")
        while feature is not None:
            steps += 1
            require(steps <= 512, "native child feature scan exceeded its bound")
            concrete = author.typed(feature, "Feature")
            kind = str(author.get(concrete, "GetTypeName2"))
            name = str(author.get(concrete, "Name"))
            fid = None
            if kind in ("OriginProfileFeature", "ProfileFeature"):
                fid = author.get(concrete, "GetID")
                require(
                    type(fid) is int and fid >= 0,
                    "native profile IFeature.GetID did not return its document identity",
                )
            key = (name, kind, fid)
            if key not in seen:
                require(
                    len(rows) < 256, "native child feature count exceeded its bound"
                )
                seen.add(key)
                rows.append({"name": name, "type": kind, "feature_id": fid})
                visit(author.get(concrete, "GetFirstSubFeature"), name, depth + 1)
            feature = author.get(
                concrete, "GetNextFeature" if parent is None else "GetNextSubFeature"
            )

    visit(author.get(child, "FirstFeature"), None, 0)
    origins = [row for row in rows if row["type"] == "OriginProfileFeature"]
    require(len(origins) == 1, "native child must have one origin feature identity")
    origin = origins[0]
    profiles = [row for row in rows if row["type"] == "ProfileFeature"]
    require(
        len(profiles) == 1
        and profiles[0]["name"] == SKETCH
        and profiles[0]["feature_id"] != origin["feature_id"],
        "native origin and ordinary rectangle profile are not distinct",
    )
    return {
        "origin": origin,
        "ordinary_profile": profiles[0],
        "features": rows,
    }


def observe(author, drawing, case, child_path, paper, moved=False):
    request = dict(case["view"])
    if moved:
        request["position_m"] = [
            a + b
            for a, b in zip(request["position_m"], case["view_move_m"], strict=True)
        ]
    observed = drawing_snapshot(
        author, author.model, drawing, request, child_path, paper
    )
    view = author.typed(
        author.get(
            author.typed(author.get(drawing, "GetFirstView"), "View"), "GetNextView"
        ),
        "View",
    )
    child = author.get(view, "ReferencedDocument")
    require(
        child is not None
        and Path(author.get(child, "GetPathName")).samefile(child_path),
        "origin drawing resolved a different child",
    )
    saved_model, saved_sketch = author.model, author.sketch
    try:
        author.model = child
        geometry = author.snapshot(case["part"], "Original")
        owners = feature_owners(author, child)
        active = author.get(
            author.get(child, "ConfigurationManager"), "ActiveConfiguration"
        )
        require(
            str(author.get(active, "Name")) == observed["view"]["configuration"],
            "native child configuration differs from the view",
        )
    finally:
        author.model, author.sketch = saved_model, saved_sketch
    return {
        "drawing": observed,
        "child": geometry,
        "feature_owners": owners,
        "resolved_child_sha256": digest(child_path),
        "resolved_child_path": str(child_path),
        "drawing_tree": author.feature_tree(required_names=()),
        "display_profile_selection_requires_postsave_typed_join": True,
    }


def file_row(path):
    return {"path": str(path), "sha256": digest(path), "bytes": path.stat().st_size}


def save(author, controller, model, path):
    require(not path.exists(), "native source output must be unused")
    path.parent.mkdir(parents=True, exist_ok=True)
    status = author.rec.call(
        "save newly authored immutable source",
        controller.save_as,
        model,
        path,
        parameters={
            "path": str(path),
            "version": 0,
            "options": 1,
            "export_data": None,
            "advanced_options": None,
        },
    )
    require(
        tuple(status) == (True, 0, 0) and path.is_file(),
        "native source save failed or warned",
    )
    return {**file_row(path), "save_status": list(status)}


def source_author(author, controller, job, case, private):
    author.build(controller, case["part"])
    child = author.model
    child_geometry = author.snapshot(case["part"], "Original")
    child_owners = feature_owners(author, child)
    child_path = private / "Native" / (case["child_name"] + ".SLDPRT")
    saved_child = save(author, controller, child, child_path)
    author.rec.call(
        "close owned authored child before readonly drawing link",
        controller.close_doc,
        child,
    )
    author.model, author.sketch = None, None
    drawing = make_drawing(
        author,
        controller,
        Path(job["drawing_template"]),
        job["paper_size"],
        case["view"],
        child_path,
    )
    initial = observe(author, drawing, case, child_path, job["paper_size"])
    require(
        initial["feature_owners"] == child_owners,
        "creating a view changed child feature identity",
    )
    require(
        author.get(author.model, "ForceRebuild3", False),
        "new native origin drawing did not rebuild",
    )
    rebuilt = observe(author, drawing, case, child_path, job["paper_size"])
    drawing_path = private / "Native" / (case["name"] + ".SLDDRW")
    saved_drawing = save(author, controller, author.model, drawing_path)
    saved = observe(author, drawing, case, child_path, job["paper_size"])
    compare_states(author, saved["drawing"], rebuilt["drawing"])
    require(
        saved["feature_owners"] == child_owners,
        "the source save changed origin/profile ownership",
    )
    return {
        "initial": initial,
        "rebuilt": rebuilt,
        "saved": saved,
        "child_authored_geometry": child_geometry,
        "files": {"drawing": saved_drawing, "child": saved_child},
    }


def assert_files(private, data):
    for row in data["files"].values():
        require(
            checked(Path(row["path"]), row["sha256"], private).stat().st_size
            == row["bytes"],
            "a locked native source changed",
        )


def reopen(author, controller, job, case, private, phase, source, moved):
    assert_files(private, source)
    source_path = Path(source["files"]["drawing"]["path"])
    child_path = Path(source["files"]["child"]["path"])
    current = moved if phase == "reopen-moved" else source
    assert_files(private, current)
    path = Path(current["files"]["drawing"]["path"])
    author.model, errors, warnings = author.rec.call(
        "fresh readonly open exact origin drawing",
        controller.open,
        path,
        doctype=3,
        read_only=True,
    )
    require(
        author.model is not None
        and errors == warnings == 0
        and Path(author.get(author.model, "GetPathName")).samefile(path),
        "native origin source reopen failed or warned",
    )
    drawing = author.typed(author.model, "DrawingDoc")
    initial = observe(
        author, drawing, case, child_path, job["paper_size"], phase == "reopen-moved"
    )
    compare_states(author, initial["drawing"], current["saved"]["drawing"])
    require(
        initial["feature_owners"] == source["saved"]["feature_owners"],
        "fresh reopen changed native origin/profile identity",
    )
    require(
        author.get(author.model, "ForceRebuild3", False),
        "native origin source rebuild failed",
    )
    rebuilt = observe(
        author, drawing, case, child_path, job["paper_size"], phase == "reopen-moved"
    )
    compare_states(author, rebuilt["drawing"], initial["drawing"])
    files = {key: dict(row) for key, row in current["files"].items()}
    result = {
        "initial": initial,
        "rebuilt": rebuilt,
        "saved": rebuilt,
        "files": files,
        "open_errors": errors,
        "open_warnings": warnings,
    }
    if phase == "move-save":
        sentinel = author.typed(author.get(drawing, "GetFirstView"), "View")
        view = author.typed(author.get(sentinel, "GetNextView"), "View")
        target = [
            a + b
            for a, b in zip(
                case["view"]["position_m"], case["view_move_m"], strict=True
            )
        ]
        set_view_position(author, view, target)
        require(
            author.get(author.model, "ForceRebuild3", False),
            "moving the origin view did not rebuild",
        )
        edited = observe(author, drawing, case, child_path, job["paper_size"], True)
        require(
            edited["feature_owners"] == source["saved"]["feature_owners"]
            and edited["drawing_tree"] == source["saved"]["drawing_tree"],
            "view movement changed native feature identities or tree",
        )
        files["drawing"] = save(
            author,
            controller,
            author.model,
            private / "Native" / (case["name"] + "Moved.SLDDRW"),
        )
        result.update(edited=edited, saved=edited)
    return result


def native_phase(job, case, private, raw, phase, source, moved, publish):
    import Swapp
    from OracleIdentity import application_identity

    rec = SourceRecorder(raw, {"case": case, "phase": phase}, publish)
    controller, author, preference = None, None, None
    result = {"passed": False}
    with Swapp.Dismisser() as dialogs:
        try:
            rec.call("guard idle reserved oracle", Swapp.sweep)
            controller = rec.call("start owned native origin source oracle", Swapp.Sw)
            full_identity = rec.call(
                "verify exact origin source oracle",
                application_identity,
                controller.app,
            )
            require(
                full_identity["version_matches"]
                and full_identity["sha256"] == ORACLE
                and controller.revision == "34.5.2",
                "origin source oracle build differs",
            )
            result["identity"] = {
                key: full_identity[key]
                for key in (
                    "process_id",
                    "process_creation_filetime",
                    "file_version",
                    "sha256",
                )
            }
            author = RectangleAuthor(controller.app, rec, Swapp)
            if phase == "author":
                template = Path(
                    rec.call(
                        "resolve registered native part template",
                        controller.template,
                        "part",
                    )
                )
                require(
                    template.is_absolute() and template.is_file(),
                    "registered native part template is missing",
                )
                result["part_template_sha256"] = digest(template)
                preference = bool(author.get(author.app, "GetUserPreferenceToggle", 10))
                author.get(author.app, "SetUserPreferenceToggle", 10, False)
                require(
                    not author.get(author.app, "GetUserPreferenceToggle", 10),
                    "native dimension prompt remained enabled",
                )
                result.update(source_author(author, controller, job, case, private))
            else:
                result.update(
                    reopen(author, controller, job, case, private, phase, source, moved)
                )
            result["passed"] = True
        except Exception as error:
            rec.failure(error)
        finally:
            if author is not None and preference is not None:
                try:
                    author.get(author.app, "SetUserPreferenceToggle", 10, preference)
                    require(
                        bool(author.get(author.app, "GetUserPreferenceToggle", 10))
                        == preference,
                        "native dimension prompt restoration differed",
                    )
                except Exception as error:
                    rec.failure(error, cleanup=True)
            if controller is not None:
                controller.close()
                result["controller_diagnostics"] = controller.diagnostics
    result.update(dialogs=dialogs.log, progress_windows=dialogs.progress)
    if "files" in result:
        for row in result["files"].values():
            row["before_close_sha256"] = row["sha256"]
            row.update(file_row(Path(row["path"])))
        if source is not None:
            assert_files(private, source)
        if moved is not None:
            assert_files(private, moved)
    result["passed"] = bool(
        result["passed"]
        and rec.data["first_failure"] is None
        and not rec.data["cleanup_errors"]
        and not result.get("controller_diagnostics")
        and not dialogs.log
    )
    rec.data.update(
        source_result=result, passed=result["passed"], finished_at=time.time()
    )
    rec.flush()
    require(
        result["passed"], "native origin source phase failed; inspect private record"
    )
    write_json(raw.with_name("State.json"), result)
    return {
        "identity": result["identity"],
        "state_sha256": digest(raw.with_name("State.json")),
        "files": {
            key: {k: row[k] for k in ("sha256", "bytes")}
            for key, row in result["files"].items()
        },
        "numeric_checks": len(rec.data["checks"]),
    }


def read_state(root, job, expected, cohort, identifier, phase):
    record = prior(root, cohort, identifier, phase, expected)
    path = private_root(job, expected, cohort, identifier) / phase / "State.json"
    return json.loads(checked(path, record["state_sha256"], path.parent).read_bytes())


def execute(root, job, expected, cohort, identifier, phase, private, raw, publish):
    ids = DISCLOSED if cohort == "disclosed" else HIDDEN
    if phase == "seal":
        require(identifier == "C00", "seal uses cohort identity C00")
        values = disclosed_cases() if cohort == "disclosed" else hidden_cases()
        path = private / "SealedSpecs.json"
        require(
            not path.exists(), "origin specifications are immutable and must be new"
        )
        write_json(
            path, {"schema": SPEC_SCHEMA, "cases": [validate(row) for row in values]}
        )
        return {
            "sealed_spec_sha256": digest(path),
            "case_count": len(values),
            "writer_output_count": 0,
            "hidden_designs_disclosed": False,
        }
    if phase in ("before", "after"):
        require(identifier == "C00", "controls use cohort identity C00")
        from InspectFresh import inspect, healthy

        row = inspect(
            root / "Control.SLDPRT", checkpoint=lambda: publish(progress_at=time.time())
        )
        write_json(raw, row)
        require(
            healthy(row) and row["oracle_identity"]["sha256"] == ORACLE,
            "origin source control is unhealthy",
        )
        return {
            "healthy": True,
            "identity": {
                key: row["oracle_identity"][key]
                for key in (
                    "process_id",
                    "process_creation_filetime",
                    "file_version",
                    "sha256",
                )
            },
        }
    if phase == "export-disclosed":
        require(
            cohort == "disclosed" and identifier == "C00",
            "only locked disclosed source files can leave guest-private custody before the writer freeze",
        )
        prior(root, cohort, "C00", "lock", expected)
        from shutil import copyfile

        output = root / "DisclosedExports"
        output.mkdir(exist_ok=False)
        cases = []
        for name in DISCLOSED:
            folder = private_root(job, expected, cohort, name)
            original = read_state(root, job, expected, cohort, name, "author")
            moved_state = read_state(root, job, expected, cohort, name, "move-save")
            assert_files(folder, original)
            assert_files(folder, moved_state)
            case_dir = output / name
            case_dir.mkdir()
            child = Path(original["files"]["child"]["path"])
            copyfile(child, case_dir / child.name)
            item = {
                "case": name,
                "child": {
                    "path": name + "/" + child.name,
                    **{
                        key: original["files"]["child"][key]
                        for key in ("sha256", "bytes")
                    },
                },
                "drawings": {},
                "observations": {},
            }
            for state_name, source_state in (
                ("source", original),
                ("moved", moved_state),
            ):
                path = Path(source_state["files"]["drawing"]["path"])
                copyfile(path, case_dir / path.name)
                item["drawings"][state_name] = {
                    "path": name + "/" + path.name,
                    **{
                        key: source_state["files"]["drawing"][key]
                        for key in ("sha256", "bytes")
                    },
                }
                observed = source_state["saved"]
                item["observations"][state_name] = {
                    "feature_owners": observed["feature_owners"],
                    "orientation": observed["drawing"]["view"]["orientation"],
                    "configuration": observed["drawing"]["view"]["configuration"],
                    "resolved_child_path": observed["resolved_child_path"],
                    "resolved_child_sha256": observed["resolved_child_sha256"],
                    "position_m": observed["drawing"]["view"]["position_m"],
                }
            cases.append(item)
        index = output / "Index.json"
        write_json(
            index,
            {
                "schema": "kit.sw2026.disclosed-origin-profile-source-export.v1",
                "packet_sha256": expected,
                "cohort": cohort,
                "cases": cases,
                "heldout_details_exported": False,
            },
        )
        return {
            "disclosed_export_sha256": digest(index),
            "case_count": len(cases),
            "heldout_details_exported": False,
        }
    if phase == "lock":
        require(identifier == "C00", "cohort lock uses identity C00")
        before = prior(root, cohort, "C00", "before", expected)
        after = prior(root, cohort, "C00", "after", expected)
        rows = [before, after] + [
            prior(root, cohort, name, step, expected)
            for name in ids
            for step in NATIVE_PHASES
        ]
        births = [
            (
                row["identity"]["process_id"],
                row["identity"]["process_creation_filetime"],
            )
            for row in rows
        ]
        require(
            len(births) == len(set(births)) == 18
            and before["healthy"]
            and after["healthy"],
            "source lock needs eighteen distinct healthy native phases",
        )
        for name in ids:
            folder = private_root(job, expected, cohort, name)
            for step in ("author", "move-save"):
                state = read_state(root, job, expected, cohort, name, step)
                assert_files(folder, state)
        return {
            "source_locked": True,
            "controls_healthy": True,
            "distinct_native_phases": 18,
            "case_count": len(ids),
            "writer_output_count": 0,
            "native_acceptance": False,
            "heldout_acceptance": False,
            "profile_selection_typed_join_still_required": True,
        }
    require(identifier in ids, "case identity is outside its cohort")
    prior(root, cohort, "C00", "before", expected)
    case = case_input(root, job, expected, cohort, identifier)
    source = (
        None
        if phase == "author"
        else read_state(root, job, expected, cohort, identifier, "author")
    )
    moved = (
        read_state(root, job, expected, cohort, identifier, "move-save")
        if phase == "reopen-moved"
        else None
    )
    if phase == "move-save":
        prior(root, cohort, identifier, "reopen-source", expected)
    return native_phase(job, case, private, raw, phase, source, moved, publish)


def run(args, job):
    root, expected = args.packet.parent, args.packet_sha256
    output = root / "Progress" / args.cohort / args.case_id / args.phase
    output.mkdir(parents=True, exist_ok=False)
    state = {
        "schema": SCHEMA,
        "packet_sha256": expected,
        "cohort": args.cohort,
        "case_id": args.case_id,
        "phase": args.phase,
        "stage": "starting",
        "passed": False,
        "writer_output_count": 0,
        "native_acceptance": False,
        "heldout_acceptance": False,
    }

    allowed = {
        "stage",
        "passed",
        "progress_at",
        "finished_at",
        "private_record_sha256",
        "identity",
        "sealed_spec_sha256",
        "case_count",
        "writer_output_count",
        "hidden_designs_disclosed",
        "healthy",
        "state_sha256",
        "files",
        "numeric_checks",
        "source_locked",
        "controls_healthy",
        "distinct_native_phases",
        "native_acceptance",
        "heldout_acceptance",
        "profile_selection_typed_join_still_required",
        "disclosed_export_sha256",
        "heldout_details_exported",
    }

    def publish(**values):
        require(
            set(values) <= allowed,
            "public source status cannot disclose design observations",
        )
        state.update(values)
        write_json(output / "Record.json", state)

    publish()
    raw = None
    try:
        private = private_root(job, expected, args.cohort, args.case_id)
        detail = private / args.phase
        detail.mkdir(exist_ok=False)
        raw = detail / "Private.json"
        with (detail / "Console.log").open(
            "x", encoding="utf-8"
        ) as log, redirect_stdout(log), redirect_stderr(log):
            result = execute(
                root,
                job,
                expected,
                args.cohort,
                args.case_id,
                args.phase,
                private,
                raw,
                publish,
            )
            if not raw.exists():
                write_json(raw, result)
            verify(args.packet, expected)
        publish(
            **result,
            stage="passed",
            passed=True,
            finished_at=time.time(),
            private_record_sha256=digest(raw),
        )
    except Exception as error:
        if raw is not None:
            write_json(
                raw.with_name("Failure.json"),
                {"type": type(error).__name__, "message": str(error)},
            )
        publish(stage="failed", passed=False, finished_at=time.time())
    print(
        json.dumps(
            {
                key: state[key]
                for key in ("cohort", "case_id", "phase", "stage", "passed")
            }
        )
    )
    return 0 if state["passed"] else 3


def main():
    parser = argparse.ArgumentParser(
        description="Author independent native origin-display sources before writer construction"
    )
    parser.add_argument("command", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--cohort", choices=("disclosed", "hidden"))
    parser.add_argument("--case-id", choices=("C00", *DISCLOSED, *HIDDEN))
    parser.add_argument("--phase", choices=PHASES)
    args = parser.parse_args()
    args.packet = args.packet.resolve(strict=True)
    job = verify(args.packet, args.packet_sha256)
    if args.command == "verify":
        print(
            json.dumps(
                {"passed": True, "tools": len(TOOLS), "native_processes_started": 0}
            )
        )
        return 0
    require(
        args.cohort is not None and args.case_id is not None and args.phase is not None,
        "run one explicit source phase",
    )
    return run(args, job)


if __name__ == "__main__":
    raise SystemExit(main())
