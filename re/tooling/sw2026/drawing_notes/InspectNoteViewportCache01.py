import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ObservePlainNotePresentation01 import (
    ORACLE,
    CurveAuthor,
    Recorder,
    capture,
    digest,
    drawing_state,
    publish,
    require,
)
from InspectNoteGrid01 import preferences
from InspectNoteViewport02 import pose
from NoteViewportCacheCases import CORE_BASIS_SHA256, cache_basis_passed, omission_cases

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = "kit.sw2026.disclosed-note-viewport-cache.v1"
STAGES = ("Initial", "Rebuilt", "SheetFit")


def verify(path, expected):
    require(
        path.parent.resolve() == ROOT
        and Path(__file__).resolve().parent == ROOT / "Tools"
        and digest(path) == expected,
        "run the exact frozen viewport cache packet",
    )
    job = json.loads(path.read_bytes())
    omissions = omission_cases(job["profile"], job["source_stream_order"])
    roles = ("ControlBefore", "SourceBefore", *omissions, "SourceAfter", "ControlAfter")
    require(
        job["schema"] == SCHEMA
        and job["oracle_sha256"] == ORACLE
        and job["roles"] == list(roles)
        and job["writer_output_count"]
        == job["heldout_inputs_read"]
        == job["document_saves"]
        == job["parameter_edits"]
        == job["preference_writes"]
        == 0
        and job["native_acceptance"] is False,
        "the disclosed read-only cache scope changed",
    )
    for relative, expected_hash in job["files_sha256"].items():
        require(
            digest(ROOT / relative) == expected_hash,
            "a frozen viewport cache file changed: " + relative,
        )
    require(
        job["source_sha256"]
        == "ba31c08e6e1a915509bd8d7db8962577fe0e4bcfccf6468ce4fa92ad5b4800ad"
        and job["control_sha256"]
        == "227f12b5834f73e31d1cb64db9e615418852bfba6c30d6c2700be6e26cc4932b"
        and job["intent_sha256"]
        == "7e6175c03ca5c76ad6a30e981c161d4a46f6b0366d6b39ae7de0e3d5dc52324b",
        "the exact declared disclosed source, intent or pristine control changed",
    )
    require(
        set(job["variants"]) == set(omissions)
        and all(
            job["variants"][name]["omitted"] == list(keys)
            for name, keys in omissions.items()
        ),
        "the individual or combined omission changed",
    )
    require(
        all(
            row["retained_logical_streams_exact"] is True
            and row["only_changes_are_declared_omissions"] is True
            for row in job["variants"].values()
        ),
        "the declared retained-stream proof changed",
    )
    domain = "guest" if os.name == "nt" else "host"
    for row in job["original_sources"].values():
        require(
            digest(Path(row[domain])) == row["sha256"], "the original source changed"
        )
    prior = json.loads((ROOT / "Evidence/DisplayFlagsResult.json").read_bytes())
    require(
        prior["complete"] is True
        and prior["healthy_controls"] is True
        and prior["distinct_processes"] == 8
        and prior["phases"]["Source"]["passed"] is True,
        "the disclosed native note/render observation no longer matches",
    )
    if job["profile"] == "seven":
        basis = (ROOT / "Evidence/ViewportCachesResult.json").read_bytes()
        require(sha256(basis).hexdigest() == CORE_BASIS_SHA256
                and cache_basis_passed(json.loads(basis)), "the earlier graphics omission proof changed")
    api = json.loads((ROOT / "GridApi01.json").read_bytes())
    require(
        api["version"] == [34, 0] and api["cad_processes_started"] == 0,
        "the registered rendering preference metadata changed",
    )
    return job


def native_file(job, role):
    if role.startswith("Control"):
        return ROOT / "Inputs/Pristine/Control.SLDDRW", job["control_sha256"], None
    intent = json.loads((ROOT / "Intent.json").read_bytes())
    if role.startswith("Source"):
        return ROOT / "Inputs/Source/Disclosed01.SLDDRW", job["source_sha256"], intent
    row = job["variants"][role]
    return ROOT / row["file"], row["sha256"], intent


def observe(author, drawing, extension, api, intent, directory, label):
    current = {
        "pose": pose(author),
        "preferences": preferences(author, author.model, extension, api),
    }
    current["bitmap"] = capture(author, directory / (label + ".bmp"))
    current["drawing"] = drawing_state(author, drawing, intent)
    current["whats_wrong"] = int(author.get(extension, "GetWhatsWrongCount"))
    require(
        current["whats_wrong"] == 0, "the drawing has native feature errors or warnings"
    )
    return current


def phase(path, expected, role):
    require(os.name == "nt", "root owns native viewport cache phases")
    job = verify(path, expected)
    require(role in job["roles"], "unexpected native viewport cache phase")
    runtime = job["guest_runtime"]
    require(
        tuple(sys.version_info[:3]) == tuple(map(int, runtime["version"].split(".")))
        and struct.calcsize("P") * 8 == runtime["pointer_bits"]
        and Path(sys.executable).samefile(runtime["executable"]),
        "the native observer runtime changed",
    )
    if role == "SourceBefore" or role in job["variants"]:
        before = json.loads(
            (ROOT / "Inspection/ControlBefore/Result.json").read_bytes()
        )
        require(
            before["passed"] is True, "a healthy pristine leading control is required"
        )
    if role in job["variants"]:
        before = json.loads((ROOT / "Inspection/SourceBefore/Result.json").read_bytes())
        require(
            before["passed"] is True, "the unchanged annotated source must pass first"
        )
    if role in job["variants"] and role != "Repacked":
        before = json.loads((ROOT / "Inspection/Repacked/Result.json").read_bytes())
        require(
            before["passed"] is True, "the full repack must pass before an omission"
        )
    directory = ROOT / "Inspection" / role
    directory.mkdir(parents=True, exist_ok=False)
    source, source_hash, intent = native_file(job, role)
    from OracleIdentity import application_identity
    import Swapp

    recorder = Recorder(
        directory / "Record.json", {"role": role, "packet_sha256": expected}
    )
    row = {
        "role": role,
        "passed": False,
        "input_sha256": source_hash,
        "writer_output_count": 0,
        "document_saves": 0,
        "parameter_edits": 0,
        "preference_writes": 0,
        "viewport_fit_calls": 0,
        "native_acceptance": False,
    }
    controller = author = None
    with Swapp.Dismisser() as dialogs:
        try:
            recorder.call("require idle drawing cache oracle", Swapp.sweep)
            controller = recorder.call(
                "start fresh visible drawing cache oracle", Swapp.Sw, visible=True
            )
            row["identity"] = recorder.call(
                "verify exact drawing cache oracle",
                application_identity,
                controller.app,
            )
            require(
                row["identity"]["version_matches"]
                and row["identity"]["sha256"] == ORACLE
                and row["identity"]["file_version"] == "34.5.2.0604",
                "wrong viewport cache oracle",
            )
            author = CurveAuthor(controller.app, recorder, Swapp)
            require(
                int(author.get(controller.app, "GetDocumentCount")) == 0,
                "the drawing phase is not cold",
            )
            model, errors, warnings = recorder.call(
                "read-only open exact cache diagnostic",
                controller.open,
                source,
                doctype=3,
                read_only=True,
            )
            row["open"] = [errors, warnings]
            row["read_only_requested"] = True
            require(
                model is not None and errors == warnings == 0,
                "the cache diagnostic did not open cleanly",
            )
            author.model = model
            row["actual_path"] = str(author.get(model, "GetPathName"))
            require(
                Path(row["actual_path"]).samefile(source),
                "the native open chose another actual drawing",
            )
            drawing = author.typed(model, "DrawingDoc")
            extension = author.typed(
                author.get(model, "Extension"), "ModelDocExtension"
            )
            api = json.loads((ROOT / "GridApi01.json").read_bytes())
            row["stages"] = {}
            row["stages"]["Initial"] = observe(
                author, drawing, extension, api, intent, directory, "Initial"
            )
            row["rebuild"] = bool(author.get(model, "ForceRebuild3", False))
            require(row["rebuild"], "the cache diagnostic rebuild failed")
            row["stages"]["Rebuilt"] = observe(
                author, drawing, extension, api, intent, directory, "Rebuilt"
            )
            require(
                row["stages"]["Initial"]["drawing"]
                == row["stages"]["Rebuilt"]["drawing"],
                "the actual note or sheet state changed on unchanged rebuild",
            )
            author.get(extension, "ViewZoomToSheet")
            row["viewport_fit_calls"] += 1
            row["stages"]["SheetFit"] = observe(
                author, drawing, extension, api, intent, directory, "SheetFit"
            )
            require(
                all(
                    row["stages"][stage]["preferences"]
                    == row["stages"]["Initial"]["preferences"]
                    for stage in STAGES
                ),
                "the observed drawing preferences changed",
            )
            row["passed"] = True
        except Exception as error:
            recorder.failure(error)
            row["error"] = {"type": type(error).__name__, "error": str(error)}
        finally:
            if author is not None and author.model is not None:
                try:
                    recorder.call(
                        "close owned unsaved diagnostic drawing",
                        controller.close_doc,
                        author.model,
                    )
                except Exception as error:
                    recorder.failure(error, cleanup=True)
            if controller is not None:
                try:
                    controller.close()
                    row["controller_diagnostics"] = controller.diagnostics
                except Exception as error:
                    recorder.failure(error, cleanup=True)
    row.update(dialogs=dialogs.log, progress_windows=dialogs.progress)
    try:
        verify(path, expected)
        row["immutable_inputs"] = True
    except Exception as error:
        recorder.failure(error)
        row["immutable_inputs"] = False
    row["passed"] = bool(
        row["passed"]
        and row["immutable_inputs"]
        and not row["dialogs"]
        and not row.get("controller_diagnostics")
        and recorder.data["first_failure"] is None
        and not recorder.data["cleanup_errors"]
    )
    row["numeric_checks"] = len(recorder.data["checks"])
    recorder.data.update(result=row, passed=row["passed"])
    recorder.flush()
    publish(directory / "Result.json", row)
    return row


def compare(first, second):
    ready = first.get("passed") is True and second.get("passed") is True
    comparisons = {}
    for stage in STAGES:
        left = first.get("stages", {}).get(stage, {})
        right = second.get("stages", {}).get(stage, {})
        comparisons[stage] = {
            "full_bitmap_sha256_exact": bool(
                ready and left["bitmap"]["sha256"] == right["bitmap"]["sha256"]
            ),
            "actual_note_sheet_tree_exact": bool(
                ready and left["drawing"] == right["drawing"]
            ),
            "pose_exact": bool(ready and left["pose"] == right["pose"]),
            "preferences_exact": bool(
                ready and left["preferences"] == right["preferences"]
            ),
        }
    return {
        "all_exact": bool(
            ready and all(all(row.values()) for row in comparisons.values())
        ),
        "stages": comparisons,
    }


def summarize(path, expected):
    job = verify(path, expected)
    rows = {}
    for role in job["roles"]:
        source = ROOT / "Inspection" / role / "Result.json"
        if source.is_file():
            rows[role] = json.loads(source.read_bytes())
    identities = {
        row.get("identity", {}).get("process_creation_filetime")
        for row in rows.values()
    } - {None}
    pristine = compare(rows.get("ControlBefore", {}), rows.get("ControlAfter", {}))
    annotated = compare(rows.get("SourceBefore", {}), rows.get("SourceAfter", {}))
    healthy = pristine["all_exact"] and annotated["all_exact"]
    matches = {
        role: compare(rows.get("SourceBefore", {}), rows.get(role, {}))
        for role in job["variants"]
    }
    complete = bool(
        healthy
        and len(identities) == len(rows) == len(job["roles"])
        and all(row.get("passed") is True for row in rows.values())
    )
    result = {
        "schema": "kit.sw2026.disclosed-note-viewport-cache-result.v1",
        "packet_sha256": expected,
        "profile": job["profile"],
        "diagnostic_completed": complete,
        "controls_healthy": healthy,
        "distinct_processes": len(identities),
        "pristine_before_after": pristine,
        "annotated_before_after": annotated,
        "matches_unchanged_annotated_source": matches,
        "all_diagnostic_copies_match": bool(
            complete and all(row["all_exact"] for row in matches.values())
        ),
        "phases": rows,
        "writer_output_count": 0,
        "document_saves": 0,
        "parameter_edits": 0,
        "preference_writes": 0,
        "heldout_inputs_read": 0,
        "native_acceptance": False,
        "production_cache_omission_qualified": False,
    }
    publish(ROOT / "Result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("verify", "phase", "summary"))
    parser.add_argument("trial", type=Path)
    parser.add_argument("--trial-sha256", required=True)
    parser.add_argument("--phase")
    args = parser.parse_args()
    if args.command == "verify":
        verify(args.trial.resolve(strict=True), args.trial_sha256)
        result = {"verified": True, "native_processes_started": 0}
    elif args.command == "phase":
        require(args.phase is not None, "phase is required")
        result = phase(args.trial.resolve(strict=True), args.trial_sha256, args.phase)
    else:
        result = summarize(args.trial.resolve(strict=True), args.trial_sha256)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return (
        0
        if result.get(
            "verified", result.get("passed", result.get("diagnostic_completed", False))
        )
        else 3
    )


if __name__ == "__main__":
    raise SystemExit(main())
