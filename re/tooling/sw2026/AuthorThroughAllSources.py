from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import argparse
import ast
import json
from math import isclose
import os
from pathlib import Path, PureWindowsPath
from shutil import copyfile
import time

from AuthorCurves import Recorder, digest, require, write_json
from ThroughAllApiMetadata import metadata
from ThroughAllSourcePlan import (
    SCHEMA as CASE_SCHEMA,
    SLOTS,
    disclosed_cases,
    heldout_cases,
    validate,
)

SCHEMA = "kit.sw2026.through-all-source-phases.v1"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
CONTROL = "c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57"
SCRIPT = Path(__file__).resolve()
TOOLS = (
    "AuthorThroughAllSources.py",
    "ThroughAllSourcePlan.py",
    "ThroughAllAuthor.py",
    "ThroughAllApiMetadata.py",
    "PrepareThroughAllSources.py",
    "AuthorCurves.py",
    "InspectFresh.py",
    "ObserveAssemblyLoad.py",
    "OracleIdentity.py",
    "Swapp.py",
)
PHASES = (
    "metadata",
    "seal",
    "before",
    "author",
    "reopen-source",
    "reopen-edited",
    "after",
    "lock",
)


def checked(path, expected, owner=None):
    require(
        path.is_file()
        and not path.is_symlink()
        and (owner is None or path.resolve().is_relative_to(owner.resolve()))
        and digest(path) == expected,
        "a pinned through-all source input changed",
    )
    return path


def check_namespace(tools):
    source = ast.parse((tools / "AuthorCurves.py").read_bytes())
    (base,) = [
        node
        for node in source.body
        if isinstance(node, ast.ClassDef) and node.name == "CurveAuthor"
    ]
    (constructor,) = [
        node
        for node in base.body
        if isinstance(node, ast.FunctionDef) and node.name == "__init__"
    ]
    attributes = {
        node.attr
        for node in ast.walk(constructor)
        if isinstance(node, ast.Attribute)
        and isinstance(node.ctx, ast.Store)
        and isinstance(node.value, ast.Name)
        and node.value.id == "self"
    }
    source = ast.parse((tools / "ThroughAllAuthor.py").read_bytes())
    (child,) = [
        node
        for node in source.body
        if isinstance(node, ast.ClassDef) and node.name == "ThroughAllAuthor"
    ]
    methods = {node.name for node in child.body if isinstance(node, ast.FunctionDef)}
    require(
        not attributes.intersection(methods),
        "the source author has a method shadowed by inherited instance state",
    )


def verify(path, expected):
    root = path.parent.resolve(strict=True)
    job = json.loads(checked(path, expected, root).read_bytes())
    require(
        job["schema"] == SCHEMA
        and job["oracle_sha256"] == ORACLE
        and job["control_sha256"] == CONTROL
        and job["writer_output_count"] == 0
        and job["native_acceptance"] is False
        and job["heldout_designs_guest_private"] is True,
        "use the source-only through-all packet",
    )
    require(
        SCRIPT.parent == root / "Tools" and set(job["tools_sha256"]) == set(TOOLS),
        "use the exact frozen through-all tools",
    )
    for name, wanted in job["tools_sha256"].items():
        checked(root / "Tools" / name, wanted, root / "Tools")
    check_namespace(root / "Tools")
    checked(root / "Control.SLDPRT", CONTROL, root)
    binding = json.loads(
        checked(
            root / "NativeBinding.json", job["native_binding_sha256"], root
        ).read_bytes()
    )
    require(
        binding["schema"] == "kit.sw2026.through-all-construction-evidence.v1"
        and binding["native_build"] == "34.5.2.0604"
        and binding["writer_output_count"] == binding["native_processes_started"] == 0,
        "the native through-all binding differs",
    )
    custody = json.loads(
        checked(root / "Custody.json", job["custody_sha256"], root).read_bytes()
    )
    require(
        custody["older_neutral_cases_exposed"]
        == ["H01Forward", "H02Reverse", "H03MidPlane", "H04TwoDirections"]
        and custody["older_numeric_design_values_reused"] is False
        and custody["new_through_all_hidden_payloads_read"] == 0
        and custody["writer_changed"] is False,
        "source custody is not frozen",
    )
    cases = json.loads(
        checked(root / "Disclosed.json", job["disclosed_sha256"], root).read_bytes()
    )
    require(
        cases == {"schema": CASE_SCHEMA, "cases": disclosed_cases()},
        "the disclosed through-all source intent differs",
    )
    source = job.get("sealed_source")
    if source is not None:
        require(
            set(source)
            == {"windows_path", "sha256", "packet_sha256", "seal_progress_sha256"}
            and all(
                len(source[key]) == 64
                and all(char in "0123456789abcdef" for char in source[key])
                for key in ("sha256", "packet_sha256", "seal_progress_sha256")
            )
            and PureWindowsPath(source["windows_path"])
            == PureWindowsPath(job["guest_private_base"])
            / source["packet_sha256"]
            / "D00"
            / "SealedSpecs.json",
            "the opaque prior sealed-source identity is not canonical",
        )
    return job


def private_root(job, expected, identifier):
    import ctypes

    root = Path(job["guest_private_base"])
    drive = ctypes.windll.kernel32.GetDriveTypeW
    drive.argtypes, drive.restype = (ctypes.c_wchar_p,), ctypes.c_uint
    require(
        root.is_absolute() and root.resolve() == root and drive(root.anchor) == 3,
        "source privacy requires a canonical fixed guest drive",
    )
    result = root / expected / identifier
    result.mkdir(parents=True, exist_ok=True)
    return result


def previous(root, identifier, phase, expected):
    row = json.loads(
        (root / "Progress" / identifier / phase / "Record.json").read_bytes()
    )
    require(
        row["packet_sha256"] == expected
        and row["case_id"] == identifier
        and row["phase"] == phase
        and row["stage"] == "passed"
        and row["passed"] is True,
        "a through-all source prerequisite is incomplete",
    )
    return row


def case_input(root, job, expected, identifier):
    if identifier.startswith("D"):
        return next(case for case in disclosed_cases() if case["id"] == identifier)
    sealed = previous(root, "D00", "seal", expected)
    base = private_root(job, expected, "D00")
    pack = json.loads(
        checked(
            base / "SealedSpecs.json", sealed["sealed_spec_sha256"], base
        ).read_bytes()
    )
    require(
        pack["schema"] == CASE_SCHEMA and len(pack["cases"]) == 4,
        "the new sealed through-all cohort differs",
    )
    return validate(next(case for case in pack["cases"] if case["id"] == identifier))


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


def identity(row):
    keys = ("process_id", "process_creation_filetime", "file_version", "sha256")
    require(
        row["version_matches"]
        and row["sha256"] == ORACLE
        and row["file_version"] == "34.5.2.0604"
        and type(row["process_creation_filetime"]) is int
        and row["process_creation_filetime"] > 0,
        "unexpected source oracle identity",
    )
    return {key: row[key] for key in keys}


def source_paths(base, case):
    return {
        state: base / "Native" / state.title() / (case["name"] + ".SLDPRT")
        for state in ("source", "edited")
    }


def assert_files(base, case, saved):
    require(
        set(saved) == {"source", "edited"},
        "both through-all source states must be immutable",
    )
    for key, path in source_paths(base, case).items():
        row = saved[key]
        require(
            row["status"] == [True, 0, 0]
            and checked(path, row["sha256"], base).stat().st_size == row["bytes"],
            "a native through-all source sibling changed",
        )


def signature(snapshot):
    return {
        "tree": snapshot["tree"],
        "profiles": snapshot["profiles"],
        **{
            role: {
                key: value
                for key, value in snapshot[role].items()
                if key not in ("depth_forward_m", "depth_reverse_m", "dimensions")
            }
            | {
                "dimensions": [
                    {
                        key: str(value).split("@")[:2] if key == "name" else value
                        for key, value in row.items()
                        if key != "value_m"
                    }
                    for row in snapshot[role]["dimensions"]
                ]
            }
            for role in ("stock", "operation")
        },
    }


def same_geometry(author, actual, expected):
    require(
        actual["bodies"] == expected["bodies"] == 1,
        "native through-all body count changed",
    )
    for key in ("volume", "area"):
        author.rec.close_number(
            "fresh native " + key,
            actual["mass"][key],
            expected["mass"][key],
            absolute=1e-20,
        )
    for axis, (left, right) in enumerate(
        zip(actual["mass"]["com"], expected["mass"]["com"], strict=True)
    ):
        author.rec.close_number(
            f"fresh native centroid {axis}", left, right, absolute=1e-10
        )


def make_sources(author, controller, case, base):
    base.mkdir(parents=True, exist_ok=True)
    author.build(case, controller)
    paths, saved = source_paths(base, case), {}
    snapshots = {}
    for state in ("source", "edited"):
        if state == "edited":
            author.edit_stock(case)
        first = author.snapshot(case, state == "edited")
        paths[state].parent.mkdir(parents=True, exist_ok=False)
        status = list(
            author.rec.call(
                "save independently authored through-all " + state,
                controller.save_as,
                author.model,
                paths[state],
            )
        )
        require(
            status == [True, 0, 0]
            and paths[state].is_file()
            and Path(author.get(author.model, "GetPathName")).samefile(paths[state]),
            "native through-all SaveAs failed or warned",
        )
        saved[state] = {
            "status": status,
            "sha256": digest(paths[state]),
            "bytes": paths[state].stat().st_size,
        }
        snapshots[state] = author.snapshot(case, state == "edited")
        require(
            signature(first) == signature(snapshots[state]),
            "native save changed through-all ownership or its feature tree",
        )
        same_geometry(author, first, snapshots[state])
        if state == "edited":
            require(
                signature(snapshots["source"]) == signature(snapshots["edited"]),
                "stock edit changed through-all semantic ownership",
            )
            require(
                not isclose(
                    snapshots["source"]["mass"]["volume"],
                    snapshots["edited"]["mass"]["volume"],
                    rel_tol=1e-8,
                ),
                "stock-depth edit did not change the through-all body",
            )
        for key, row in saved.items():
            checked(paths[key], row["sha256"], base)
    exports = {}
    for kind, suffix in (("parasolid", ".x_t"), ("step", ".step")):
        path = paths["edited"].with_suffix(suffix)
        status = list(
            author.rec.call(
                "export independent through-all geometry sibling",
                controller.save_as,
                author.model,
                path,
            )
        )
        require(
            status == [True, 0, 0] and path.is_file() and path.stat().st_size > 0,
            "native geometry sibling export failed or warned",
        )
        exports[kind] = {
            "status": status,
            "bytes": path.stat().st_size,
            "sha256": digest(path),
        }
        assert_files(base, case, saved)
    result = {
        **snapshots,
        "saved_files": saved,
        "exports": exports,
        "analytic_geometry_qualified": snapshots["source"][
            "analytic_geometry_qualified"
        ],
        "writer_output_count": 0,
    }
    write_json(base / "SavedAuthor.json", result)
    return result


def reopen_source(author, controller, case, base, edited, authored):
    saved = json.loads(
        checked(
            base / "SavedAuthor.json", authored["saved_author_sha256"], base
        ).read_bytes()
    )
    assert_files(base, case, saved["saved_files"])
    state = "edited" if edited else "source"
    path = source_paths(base, case)[state]
    model, errors, warnings = author.rec.call(
        "fresh read-only open of immutable through-all source",
        controller.open,
        path,
        read_only=True,
    )
    require(
        model is not None
        and errors == warnings == 0
        and Path(author.get(model, "GetPathName")).samefile(path),
        "native through-all fresh open failed or warned",
    )
    author.model = model
    first = author.snapshot(case, edited, rebuild=False)
    second = author.snapshot(case, edited)
    require(
        signature(first) == signature(second) == signature(saved[state]),
        "native through-all source lost exact tree, profile or dimension ownership",
    )
    same_geometry(author, first, saved[state])
    same_geometry(author, second, saved[state])
    assert_files(base, case, saved["saved_files"])
    return {"initial": first, "rebuilt": second, "inputs_unchanged": True}


def measure(case, phase, base, raw, authored, publish, expected_api):
    import Swapp
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity
    from ThroughAllAuthor import ThroughAllAuthor

    require(
        metadata() == expected_api,
        "registered through-all API metadata changed since preflight",
    )
    recorder = SourceRecorder(raw, {"case": case, "phase": phase}, publish)
    result, controller = {"passed": False}, None
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call("verify idle source oracle", Swapp.sweep)
            controller = recorder.call(
                "start fresh through-all source oracle", Swapp.Sw
            )
            result["oracle_identity"] = identity(
                recorder.call(
                    "verify exact source oracle", application_identity, controller.app
                )
            )
            publish(stage="native_source", identity=result["oracle_identity"])
            author = ThroughAllAuthor(controller.app, recorder, Swapp)
            result.update(
                make_sources(author, controller, case, base)
                if phase == "author"
                else reopen_source(
                    author, controller, case, base, phase == "reopen-edited", authored
                )
            )
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
            result["error"] = repr(error)
        finally:
            if controller is not None:
                try:
                    controller.close()
                    result["controller_diagnostics"] = controller.diagnostics
                except Exception as error:
                    recorder.failure(error, cleanup=True)
    result.update(dialogs=monitor.log, progress_windows=monitor.progress)
    result["passed"] = bool(
        result["passed"]
        and not result["dialogs"]
        and not result.get("controller_diagnostics")
        and recorder.data["first_failure"] is None
        and not recorder.data["cleanup_errors"]
    )
    recorder.data.update(
        result=result, passed=result["passed"], finished_at=time.time()
    )
    recorder.flush()
    require(result["passed"], "the native through-all source phase failed")
    value = {"identity": result["oracle_identity"]}
    if phase == "author":
        value.update(
            saved_author_sha256=digest(base / "SavedAuthor.json"),
            native_artifacts=public_artifacts(result["saved_files"]),
            analytic_geometry_qualified=result["analytic_geometry_qualified"],
        )
    return value


def control(seed, raw, publish):
    from InspectFresh import healthy, inspect

    result = {}

    def checkpoint():
        write_json(raw, result)
        if result.get("oracle_identity"):
            publish(
                identity=identity(result["oracle_identity"]), stage="native_control"
            )

    checked(seed, CONTROL)
    inspect(seed, result=result, checkpoint=checkpoint)
    require(
        healthy(result)
        and identity(result["oracle_identity"])
        and digest(seed) == CONTROL,
        "through-all source bracket failed",
    )
    return {"identity": identity(result["oracle_identity"])}


def public_artifacts(saved):
    return {
        state: {key: row[key] for key in ("sha256", "bytes")}
        for state, row in saved.items()
    }


def lock_case(root, job, expected, identifier):
    phases = ("before", "author", "reopen-source", "reopen-edited", "after")
    rows = [previous(root, identifier, phase, expected) for phase in phases]
    require(
        len({row["identity"]["process_creation_filetime"] for row in rows}) == 5
        and all(
            first["finished_at"] <= second["started_at"]
            for first, second in zip(rows, rows[1:])
        ),
        "source lock lacks five ordered independent native phases",
    )
    case = case_input(root, job, expected, identifier)
    base = (
        private_root(job, expected, identifier)
        if identifier.startswith("H")
        else root / "Disclosed" / identifier
    )
    prior = json.loads(
        checked(
            base / "SavedAuthor.json", rows[1]["saved_author_sha256"], base
        ).read_bytes()
    )
    assert_files(base, case, prior["saved_files"])
    require(
        public_artifacts(prior["saved_files"]) == rows[1]["native_artifacts"],
        "native source hashes changed before lock",
    )
    return {
        "source_locked": True,
        "heldout_source_locked": identifier.startswith("H"),
        "native_artifacts": public_artifacts(prior["saved_files"]),
        "source_manifest_sha256": digest(base / "SavedAuthor.json"),
        "analytic_geometry_qualified": prior["analytic_geometry_qualified"],
        "boss_extent_qualified": False,
        "writer_output_count": 0,
    }


def run(args, path, job):
    require(
        os.name == "nt", "through-all source phases run only inside the Windows guest"
    )
    identifier, phase = args.case_id, args.phase
    require(
        (identifier == "D00" and phase in ("metadata", "seal"))
        or (identifier in SLOTS and phase not in ("metadata", "seal")),
        "phase is outside its declared source slot",
    )
    root = path.parent
    output = root / "Progress" / identifier / phase
    output.mkdir(parents=True, exist_ok=False)
    state = {
        "schema": SCHEMA,
        "packet_sha256": args.packet_sha256,
        "case_id": identifier,
        "phase": phase,
        "stage": "verifying",
        "passed": False,
        "started_at": time.time(),
        "writer_output_count": 0,
    }
    allowed = {
        "stage",
        "passed",
        "finished_at",
        "progress_at",
        "identity",
        "private_record_sha256",
        "saved_author_sha256",
        "native_artifacts",
        "source_locked",
        "heldout_source_locked",
        "source_manifest_sha256",
        "sealed_spec_sha256",
        "api_metadata_sha256",
        "analytic_geometry_qualified",
        "boss_extent_qualified",
        "writer_output_count",
    }

    def publish(**changes):
        require(
            set(changes) <= allowed,
            "private through-all source detail cannot be published",
        )
        state.update(changes)
        write_json(output / "Record.json", state)

    publish()
    raw = None
    try:
        private = private_root(job, args.packet_sha256, identifier)
        detail = private / phase
        detail.mkdir(exist_ok=False)
        raw = detail / "Private.json"
        with (detail / "Console.log").open(
            "w", encoding="utf-8"
        ) as stream, redirect_stdout(stream), redirect_stderr(stream):
            if phase == "metadata":
                write_json(raw, metadata())
                copyfile(raw, root / "ApiMetadata.json")
                result = {"api_metadata_sha256": digest(raw)}
            elif phase == "seal":
                previous(root, "D00", "metadata", args.packet_sha256)
                file = private / "SealedSpecs.json"
                require(
                    not file.exists(), "new sealed source specifications are immutable"
                )
                source = job.get("sealed_source")
                if source is None:
                    write_json(file, {"schema": CASE_SCHEMA, "cases": heldout_cases()})
                else:
                    prior_file = Path(source["windows_path"])
                    checked(
                        prior_file, source["sha256"], Path(job["guest_private_base"])
                    )
                    copyfile(prior_file, file)
                    checked(file, source["sha256"], private)
                result = {"sealed_spec_sha256": digest(file)}
            elif phase in ("before", "after"):
                previous(root, "D00", "metadata", args.packet_sha256)
                result = control(root / "Control.SLDPRT", raw, publish)
            elif phase == "lock":
                result = lock_case(root, job, args.packet_sha256, identifier)
            else:
                meta = previous(root, "D00", "metadata", args.packet_sha256)
                previous(root, identifier, "before", args.packet_sha256)
                api = json.loads(
                    checked(
                        root / "ApiMetadata.json", meta["api_metadata_sha256"], root
                    ).read_bytes()
                )
                case = case_input(root, job, args.packet_sha256, identifier)
                base = (
                    private
                    if identifier.startswith("H")
                    else root / "Disclosed" / identifier
                )
                authored = (
                    None
                    if phase == "author"
                    else previous(root, identifier, "author", args.packet_sha256)
                )
                result = measure(case, phase, base, raw, authored, publish, api)
            if not raw.exists():
                write_json(raw, result)
            verify(path, args.packet_sha256)
        publish(
            **result,
            stage="passed",
            passed=True,
            finished_at=time.time(),
            private_record_sha256=digest(raw),
        )
    except Exception as error:
        if raw is not None:
            write_json(raw.with_name("Failure.json"), {"error": repr(error)})
        publish(stage="failed", passed=False, finished_at=time.time())
    if raw is not None and identifier.startswith("D") and phase != "seal":
        disclosed = root / "Disclosed" / identifier
        disclosed.mkdir(parents=True, exist_ok=True)
        for name in ("Private.json", "Failure.json"):
            source = raw.with_name(name)
            if source.exists():
                copyfile(
                    source,
                    disclosed
                    / (phase + ("Failure" if name == "Failure.json" else "") + ".json"),
                )
    return {key: state[key] for key in ("case_id", "phase", "stage", "passed")}


def main():
    parser = argparse.ArgumentParser(
        description="Author one native through-all source phase with guest-private prewriter holdouts"
    )
    parser.add_argument("command", choices=("verify", "run"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--case-id", choices=("D00", *SLOTS))
    parser.add_argument("--phase", choices=PHASES)
    args = parser.parse_args()
    try:
        path = args.packet.resolve(strict=True)
        job = verify(path, args.packet_sha256)
        if args.command == "verify":
            result = {
                "passed": True,
                "native_processes_started": 0,
                "new_heldout_inputs_read": 0,
            }
        else:
            require(
                args.case_id is not None and args.phase is not None,
                "one source slot and phase are required",
            )
            result = run(args, path, job)
    except Exception:
        result = {"passed": False, "stage": "preflight_failed"}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
