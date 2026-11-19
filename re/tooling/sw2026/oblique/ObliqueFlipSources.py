import argparse
from hashlib import sha256
import json
import os
from pathlib import Path, PureWindowsPath
import shutil
import sys
import time
import traceback

from ObliqueFlipPlan import (
    CONTROL,
    ORACLE,
    NAMES,
    cases,
    document_plan,
    prediction,
    require,
    validate,
)

SCHEMA = "kit.sw2026.oblique-flip-source-packet.v1"
OWNED = (
    "ObliqueCylinderPlan.py",
    "ObliqueCylinderApi.py",
    "AuthorObliqueCylinder.py",
    "ObliqueFlipPlan.py",
    "AuthorObliqueFlip.py",
    "ObliqueFlipSources.py",
    "ObliqueCylinderInvoke.py",
)
SHARED = (
    "AuthorCurves.py",
    "AuthorAssemblySources.py",
    "InspectCircleSketch.py",
    "InspectFresh.py",
    "ObserveAssemblyLoad.py",
    "OracleIdentity.py",
    "Swapp.py",
    "ReferencePlaneDimensions.py",
    "ReferencePlaneSourcePlan.py",
)
PHASES = ("before", "author", "original_reopen", "edited_reopen", "after")


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def checked(path, expected):
    path = Path(path)
    require(
        path.is_file() and not path.is_symlink() and digest(path) == expected,
        "frozen input identity differs: " + path.name,
    )
    return path


def verify(path, expected):
    root = Path(path).resolve().parent
    packet = json.loads(checked(path, expected).read_bytes())
    require(
        packet["schema"] == SCHEMA
        and packet["oracle_sha256"] == ORACLE
        and packet["control_sha256"] == CONTROL,
        "unexpected oblique native packet",
    )
    require(
        packet["writer_output_count"] == 0
        and packet["heldout_execution_enabled"] is False,
        "source packet cannot enable a writer or hidden case",
    )
    require(
        Path(__file__).resolve().parent == root / "Tools",
        "run only the frozen packet tools",
    )
    require(
        set(packet["tools_sha256"]) == set(OWNED + SHARED),
        "unexpected source tool closure",
    )
    for name, sha in packet["tools_sha256"].items():
        checked(root / "Tools" / name, sha)
    checked(root / "Control.SLDPRT", CONTROL)
    actual = json.loads(
        checked(root / "Disclosed.json", packet["disclosed_sha256"]).read_bytes()
    )
    require(actual == document_plan(), "disclosed neutral author inputs differ")
    checked(root / "Predictions.json", packet["predictions_sha256"])
    return root, packet


def prepare(args):
    root = args.output.resolve()
    source = args.source_root.resolve()
    require(
        not root.exists() and root.parent.is_dir() and not root.is_relative_to(source),
        "choose an unused private output packet",
    )
    checked(args.control, CONTROL)
    inherited = checked(
        args.api_manifest,
        "fd0e7f771459a1fb10ab460907699b728544526117f54d59ebfd127847e04812",
    )
    guest = PureWindowsPath(args.guest_root)
    python = PureWindowsPath(args.guest_python)
    require(
        guest.is_absolute() and ".." not in guest.parts and python.is_absolute(),
        "use explicit absolute guest paths",
    )
    root.mkdir()
    (root / "Tools").mkdir()
    shutil.copyfile(args.control, root / "Control.SLDPRT")
    tools = {}
    for name in OWNED + SHARED:
        path = (
            Path(__file__).parent / name
            if name in OWNED
            else source / "re/tooling/sw2026" / name
        )
        shutil.copyfile(path, root / "Tools" / name)
        tools[name] = digest(root / "Tools" / name)
    write(root / "Disclosed.json", document_plan())
    predictions = {
        case["id"]: {str(index): prediction(case, index) for index in range(5)}
        for case in cases()
    }
    write(
        root / "Predictions.json",
        {
            "schema": "kit.sw2026.oblique-flip-independent-predictions.v1",
            "cases": predictions,
            "native_observations_used": False,
        },
    )
    write(
        root / "Protocol.json",
        {
            "schema": SCHEMA,
            "oracle_sha256": ORACLE,
            "control_sha256": CONTROL,
            "tools_sha256": tools,
            "disclosed_sha256": digest(root / "Disclosed.json"),
            "predictions_sha256": digest(root / "Predictions.json"),
            "prior_api_manifest_sha256": digest(inherited),
            "writer_output_count": 0,
            "heldout_execution_enabled": False,
            "native_acceptance": False,
            "guest_root": str(guest),
            "guest_python": str(python),
            "call_scope": {
                "angle_plane": "InsertRefPlane(16|optional256, positive radians,4,0,0,0)",
                "hinges": "InsertAxis2(True) from two actual principal planes, mark0 for each",
                "direction": "InsertAxis2(True) from the two actual angular planes",
                "extrusion": "FeatureExtrusion3 with end4, profile0/end1/direction16",
                "length_driver": "D1@HeightLimit",
                "sign_convention_independently_predicted_and_not_adapted": True,
                "angle_policy": "right-handed actual directed hinge, positive magnitude and explicit reverse; frozen directed hinge checks before plane creation",
                "prior_prediction_failure_preserved": True,
            },
        },
    )
    packet_sha = digest(root / "Protocol.json")
    commands = [
        {
            "name": "verify",
            "argv": [
                str(python),
                "-B",
                str(guest / "Tools/ObliqueFlipSources.py"),
                "verify",
                str(guest / "Protocol.json"),
                "--packet-sha256",
                packet_sha,
            ],
        },
        {
            "name": "metadata",
            "argv": [
                str(python),
                "-B",
                str(guest / "Tools/ObliqueFlipSources.py"),
                "metadata",
                str(guest / "Protocol.json"),
                "--packet-sha256",
                packet_sha,
            ],
        },
    ]
    for case in cases():
        for phase in (*PHASES, "lock"):
            commands.append(
                {
                    "name": case["id"] + "/" + phase,
                    "argv": [
                        str(python),
                        "-B",
                        str(guest / "Tools/ObliqueFlipSources.py"),
                        "phase",
                        str(guest / "Protocol.json"),
                        "--packet-sha256",
                        packet_sha,
                        "--case-id",
                        case["id"],
                        "--phase",
                        phase,
                    ],
                }
            )
    commands.append(
        {
            "name": "summary",
            "argv": [
                str(python),
                "-B",
                str(guest / "Tools/ObliqueFlipSources.py"),
                "summary",
                str(guest / "Protocol.json"),
                "--packet-sha256",
                packet_sha,
            ],
        }
    )
    write(
        root / "Recipe.json",
        {
            "schema": "kit.sw2026.oblique-flip-source-recipe.v1",
            "packet_sha256": packet_sha,
            "commands": commands,
            "transport": "root alone invokes each argv via prlctl exec --current-user Windows 11; serial fresh phases; no automatic process termination",
            "always_run_trailing_control_after_native_failure": True,
            "progress_path": str(guest / "Progress"),
            "native_execution_attempted": False,
        },
    )
    return {
        "packet_sha256": packet_sha,
        "recipe_sha256": digest(root / "Recipe.json"),
        "tools_sha256": tools,
        "native_launches": 0,
        "heldout_reads": 0,
    }


def prior(root, case_id, phase, packet_sha):
    path = root / "Progress" / case_id / phase / "Record.json"
    value = json.loads(path.read_bytes())
    require(
        value["packet_sha256"] == packet_sha
        and value["case_id"] == case_id
        and value["phase"] == phase
        and value["passed"] is True,
        "native phase prerequisite did not pass: " + case_id + "/" + phase,
    )
    return value


def saved(root, case, packet_sha):
    row = prior(root, case["id"], "author", packet_sha)
    value = json.loads(
        checked(
            root / "Disclosed" / case["id"] / "SavedAuthor.json",
            row["saved_author_sha256"],
        ).read_bytes()
    )
    require(
        value["case"] == case, "saved native case differs from frozen neutral source"
    )
    for role, file in value["files"].items():
        actual = root / "Disclosed" / case["id"] / "Native" / file["name"]
        require(
            file["status"] == [True, 0, 0]
            and checked(actual, file["sha256"]).stat().st_size == file["bytes"],
            "native source sibling identity differs",
        )
    return value


def native_phase(root, packet, case, phase, expected_api, recorder):
    import Swapp
    from AuthorObliqueFlip import ObliqueFlipAuthor
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity

    source_dir = root / "Disclosed" / case["id"] / "Native"
    prediction_file = json.loads(
        checked(root / "Predictions.json", packet["predictions_sha256"]).read_bytes()
    )
    targets = prediction_file["cases"][case["id"]]
    result, controller = {"passed": False}, None
    with AssemblyLoadMonitor() as monitor:
        try:
            recorder.call("verify idle source oracle", Swapp.sweep)
            controller = recorder.call("launch fresh oblique source oracle", Swapp.Sw)
            result["oracle_identity"] = recorder.call(
                "verify exact native build", application_identity, controller.app
            )
            recorder.data["result"] = result
            recorder.flush()
            require(
                result["oracle_identity"]["version_matches"]
                and result["oracle_identity"]["sha256"] == ORACLE
                and controller.revision == "34.5.2",
                "unexpected source oracle identity",
            )
            author = ObliqueFlipAuthor(
                controller.app, recorder, Swapp, expected_api, targets
            )
            if phase == "author":
                source_dir.mkdir(exist_ok=False)
                author.build(case, controller)
                result["initial"] = author.snapshot(case, 0)
                path = source_dir / (case["name"] + ".SLDPRT")
                status = list(
                    recorder.call(
                        "save independent original oblique source",
                        controller.save_as,
                        author.model,
                        path,
                    )
                )
                require(
                    status == [True, 0, 0] and path.is_file(),
                    "original native source save failed or warned",
                )
                files = {
                    "original": {
                        "name": path.name,
                        "status": status,
                        "sha256": digest(path),
                        "bytes": path.stat().st_size,
                    }
                }
                result["files"] = files
                result["edits"] = []
                for index in range(4):
                    author.edit(case, index)
                    observed = author.snapshot(case, index + 1)
                    require(
                        observed["feature_tree"] == result["initial"]["feature_tree"],
                        "native history changed during source driver edits",
                    )
                    result["edits"].append(observed)
                    recorder.flush()
                edited = source_dir / (case["name"] + "Edited.SLDPRT")
                status = list(
                    recorder.call(
                        "save independently edited oblique sibling",
                        controller.save_as,
                        author.model,
                        edited,
                    )
                )
                require(
                    status == [True, 0, 0]
                    and edited.is_file()
                    and digest(path) == files["original"]["sha256"],
                    "edited native save failed, warned or changed original",
                )
                files["edited"] = {
                    "name": edited.name,
                    "status": status,
                    "sha256": digest(edited),
                    "bytes": edited.stat().st_size,
                }
                result["exports"] = {}
                for suffix in (".x_t", ".step"):
                    target = source_dir / (case["name"] + "Edited" + suffix)
                    export_status = list(
                        recorder.call(
                            "export disclosed oblique geometry sibling",
                            controller.save_as,
                            author.model,
                            target,
                        )
                    )
                    require(
                        export_status == [True, 0, 0] and target.is_file(),
                        "native geometry export failed or warned",
                    )
                    result["exports"][suffix] = {
                        "sha256": digest(target),
                        "bytes": target.stat().st_size,
                        "status": export_status,
                    }
            else:
                authored = saved(root, case, recorder.data["job"]["packet_sha256"])
                role, steps = (
                    ("original", 0) if phase == "original_reopen" else ("edited", 4)
                )
                file = authored["files"][role]
                path = source_dir / file["name"]
                author.model, errors, warnings = recorder.call(
                    "fresh read immutable native oblique source",
                    controller.open,
                    path,
                    read_only=True,
                )
                result["open_errors"], result["open_warnings"] = errors, warnings
                require(
                    author.model is not None and errors == warnings == 0,
                    "source reopen failed or warned",
                )
                actual_path = Path(str(author.get(author.model, "GetPathName")))
                require(
                    actual_path.samefile(path),
                    "fresh reopen resolved a different native file",
                )
                require(
                    bool(author.get(author.model, "ForceRebuild3", False)),
                    "fresh source rebuild failed",
                )
                result["observed"] = author.snapshot(case, steps)
                expected_tree = authored["initial"]["feature_tree"]
                require(
                    result["observed"]["feature_tree"] == expected_tree,
                    "actual source history changed on fresh reopen",
                )
                require(digest(path) == file["sha256"], "read-only source changed")
                result["files"] = authored["files"]
            result["passed"] = True
        except Exception as error:
            recorder.failure(error)
            result["error"] = repr(error)
        finally:
            if controller is not None:
                recorder.data["stage"] = "closing owned oracle"
                recorder.flush()
                controller.close()
                result["controller_diagnostics"] = controller.diagnostics
    result["dialogs"], result["progress_windows"] = monitor.log, monitor.progress
    result["passed"] = bool(
        result["passed"]
        and not result["dialogs"]
        and not result.get("controller_diagnostics")
        and not recorder.data["cleanup_errors"]
    )
    recorder.data["result"] = result
    recorder.data["passed"] = result["passed"]
    recorder.flush()
    require(result["passed"], "native oblique source phase failed")
    for file in result["files"].values():
        checked(source_dir / file["name"], file["sha256"])
    output = {
        "identity": result["oracle_identity"],
        "numeric_checks": len(recorder.data["checks"]),
    }
    if phase == "author":
        snapshot = root / "Disclosed" / case["id"] / "SavedAuthor.json"
        write(
            snapshot,
            {
                "case": case,
                "initial": result["initial"],
                "edited": result["edits"][-1],
                "files": result["files"],
                "source_writer_output_count": 0,
            },
        )
        output["saved_author_sha256"] = digest(snapshot)
    return output


def phase(args, root, packet):
    require(
        os.name == "nt", "native author phases run only in the root-owned Windows guest"
    )
    from AuthorCurves import Recorder
    from ObliqueCylinderApi import metadata

    (case,) = [validate(value) for value in cases() if value["id"] == args.case_id]
    progress = root / "Progress" / case["id"] / args.phase
    progress.mkdir(parents=True, exist_ok=False)
    state = {
        "schema": SCHEMA,
        "packet_sha256": args.packet_sha256,
        "case_id": case["id"],
        "phase": args.phase,
        "stage": "starting",
        "passed": False,
        "started_at": time.time(),
        "writer_output_count": 0,
    }
    write(progress / "Record.json", state)
    raw = root / "Disclosed" / case["id"] / (args.phase + ".json")
    raw.parent.mkdir(parents=True, exist_ok=True)
    recorder = Recorder(
        raw,
        {
            "case_id": case["id"],
            "phase": args.phase,
            "packet_sha256": args.packet_sha256,
        },
    )
    try:
        meta = json.loads((root / "Progress/Metadata.json").read_bytes())
        require(
            meta["packet_sha256"] == args.packet_sha256 and meta["passed"] is True,
            "registered metadata preflight is missing",
        )
        expected_api = json.loads(
            checked(root / "ApiMetadata.json", meta["api_metadata_sha256"]).read_bytes()
        )
        require(metadata() == expected_api, "registered API changed after preflight")
        if args.phase in ("before", "after"):
            from InspectFresh import healthy, inspect

            checked(root / "Control.SLDPRT", CONTROL)
            result = inspect(root / "Control.SLDPRT", checkpoint=recorder.flush)
            recorder.data["result"] = result
            recorder.flush()
            require(
                healthy(result)
                and result["oracle_identity"]["sha256"] == ORACLE
                and digest(root / "Control.SLDPRT") == CONTROL,
                "oblique native bracket is unhealthy",
            )
            state["identity"] = result["oracle_identity"]
        else:
            prior(root, case["id"], "before", args.packet_sha256)
            if args.phase != "author":
                saved(root, case, args.packet_sha256)
            state.update(
                native_phase(root, packet, case, args.phase, expected_api, recorder)
            )
        verify(args.packet, args.packet_sha256)
        state.update(
            passed=True, stage="passed", finished_at=time.time(), raw_sha256=digest(raw)
        )
    except Exception as error:
        recorder.failure(error)
        state.update(
            passed=False,
            stage="failed",
            error=repr(error),
            finished_at=time.time(),
            raw_sha256=digest(raw),
        )
    recorder.data.update(passed=state["passed"], finished_at=state["finished_at"])
    recorder.flush()
    state["raw_sha256"] = digest(raw)
    write(progress / "Record.json", state)
    return state


def lock(root, packet_sha, case_id):
    rows = [prior(root, case_id, name, packet_sha) for name in PHASES]
    identities = [row["identity"]["process_creation_filetime"] for row in rows]
    require(
        len(set(identities)) == 5,
        "source lock lacks five independent fresh native processes",
    )
    require(
        all(
            first["finished_at"] <= second["started_at"]
            for first, second in zip(rows, rows[1:])
        ),
        "source phases were not serially ordered",
    )
    (case,) = [case for case in cases() if case["id"] == case_id]
    value = saved(root, case, packet_sha)
    path = root / "Progress" / case_id / "lock" / "Record.json"
    require(not path.exists(), "source lock is immutable")
    result = {
        "schema": SCHEMA,
        "case_id": case_id,
        "packet_sha256": packet_sha,
        "source_locked": True,
        "heldout_source_locked": False,
        "passed": True,
        "phase_sha256": {
            name: digest(root / "Progress" / case_id / name / "Record.json")
            for name in PHASES
        },
        "files": value["files"],
        "distinct_native_processes": 5,
        "healthy_controls": 2,
        "writer_output_count": 0,
    }
    write(path, result)
    return result


def main():
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="mode", required=True)
    mode = subs.add_parser("prepare")
    mode.add_argument("--source-root", type=Path, required=True)
    mode.add_argument("--output", type=Path, required=True)
    mode.add_argument("--control", type=Path, required=True)
    mode.add_argument("--api-manifest", type=Path, required=True)
    mode.add_argument("--guest-root", required=True)
    mode.add_argument("--guest-python", required=True)
    for name in ("verify", "metadata", "phase", "summary"):
        mode = subs.add_parser(name)
        mode.add_argument("packet", type=Path)
        mode.add_argument("--packet-sha256", required=True)
        if name == "phase":
            mode.add_argument("--case-id", choices=("F01", "F02"), required=True)
            mode.add_argument("--phase", choices=(*PHASES, "lock"), required=True)
    args = parser.parse_args()
    if args.mode == "prepare":
        result = prepare(args)
    else:
        root, packet = verify(args.packet, args.packet_sha256)
        if args.mode == "verify":
            result = {
                "passed": True,
                "packet_sha256": args.packet_sha256,
                "native_launches": 0,
                "heldout_reads": 0,
            }
        elif args.mode == "metadata":
            from ObliqueCylinderApi import metadata

            require(
                not (root / "Progress/Metadata.json").exists(),
                "metadata phase is immutable",
            )
            try:
                observed = metadata()
                write(root / "ApiMetadata.json", observed)
                result = {
                    "passed": True,
                    "packet_sha256": args.packet_sha256,
                    "api_metadata_sha256": digest(root / "ApiMetadata.json"),
                    "native_launches": 0,
                }
                write(root / "Progress/Metadata.json", result)
            except Exception as error:
                result = {
                    "passed": False,
                    "packet_sha256": args.packet_sha256,
                    "native_launches": 0,
                    "error": repr(error),
                    "traceback": traceback.format_exc(),
                }
                write(root / "MetadataFailure.json", result)
        elif args.mode == "phase":
            result = (
                lock(root, args.packet_sha256, args.case_id)
                if args.phase == "lock"
                else phase(args, root, packet)
            )
        else:
            rows = [
                json.loads(
                    (root / "Progress" / case["id"] / "lock/Record.json").read_bytes()
                )
                for case in cases()
            ]
            require(
                all(
                    row["passed"] and row["packet_sha256"] == args.packet_sha256
                    for row in rows
                ),
                "both disclosed source locks are required",
            )
            phases = [
                prior(root, case["id"], name, args.packet_sha256)
                for case in cases()
                for name in PHASES
            ]
            identities = [
                row["identity"]["process_creation_filetime"] for row in phases
            ]
            require(
                len(set(identities)) == 10,
                "the two source cases must have ten distinct native process identities",
            )
            result = {
                "passed": True,
                "packet_sha256": args.packet_sha256,
                "source_cases_locked": 2,
                "distinct_native_processes": len(set(identities)),
                "healthy_controls": 4,
                "writer_output_count": 0,
                "heldout_inputs_read": 0,
                "locks_sha256": {
                    case["id"]: digest(
                        root / "Progress" / case["id"] / "lock/Record.json"
                    )
                    for case in cases()
                },
            }
            write(root / "Summary.json", result)
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "passed",
                    "packet_sha256",
                    "case_id",
                    "phase",
                    "stage",
                    "native_launches",
                    "heldout_reads",
                    "source_cases_locked",
                )
                if key in result
            }
        )
    )
    return 0 if result.get("passed", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
