from argparse import ArgumentParser
from hashlib import sha256
from json import dumps, loads
import os
from pathlib import Path, PurePosixPath
from time import monotonic_ns, time


SCHEMA = "kit.sw2026.disclosed-gr-messenger-ownership.v1"
ROLES = ("ControlBefore", "NativeSource", "Generated", "ControlAfter")
CASES = {
    "ControlBefore": "Inputs/Control.SLDDRW", "NativeSource": "Inputs/NativeSource/Disclosed01.SLDDRW",
    "Generated": "Inputs/Generated/Disclosed01.SLDDRW", "ControlAfter": "Inputs/Control.SLDDRW",
}
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
TOOLS = {
    "AuthorCurves.py", "AuthorDrawingSources.py", "AuthorPlainDrawingNotes.py", "DrawingCacheCases.py",
    "InspectDrawingCache.py", "ObservePlainNotePresentation01.py", "InspectNoteGrid01.py",
    "OracleIdentity.py", "Swapp.py", "OwnedMessengerMemory.py", "InspectMessengerOwnership.py",
}
FILES = {"Inputs/Control.SLDDRW", "Inputs/NativeSource/Disclosed01.SLDDRW", "Inputs/Generated/Disclosed01.SLDDRW",
         "Inputs/Intent.json", "Inputs/GridApi01.json", "NativeReadPlan.json"}
STAGES = ("after_open", "before_rebuild", "after_rebuild", "after_redraw")


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def inside(root, name):
    relative = PurePosixPath(name)
    require(isinstance(name, str) and "\\" not in name and not relative.is_absolute()
            and relative.as_posix() == name and all(part not in (".", "..") for part in relative.parts),
            "packet path is not canonical and relative")
    selected = root
    for part in relative.parts:
        selected = selected / part
        require(not selected.is_symlink(), "packet contains a symbolic link")
    resolved = selected.resolve(strict=True)
    require(resolved.is_relative_to(root) and resolved.is_file(), "packet file escapes the frozen root")
    return resolved


def check_job(path, expected):
    require(not path.is_symlink() and path.is_file(), "job is absent or a symbolic link")
    root = path.resolve(strict=True).parent
    require(digest(path) == expected, "messenger job digest differs")
    job = loads(path.read_bytes())
    require(job["schema"] == SCHEMA and job["roles"] == list(ROLES) and job["cases"] == CASES,
            "messenger packet scope differs")
    require(job["oracle_sha256"] == ORACLE and job["process_access_mask"] == "0x410"
            and job["heldout_inputs_read"] == 0 and job["document_saves"] == 0
            and job["debugger_attaches"] == 0 and job["process_memory_writes"] == 0,
            "messenger packet changes read-only ownership scope")
    require(Path(__file__).resolve().parent == root / "Tools" and job["tools"].keys() == TOOLS
            and job["files"].keys() == FILES, "messenger packet file closure differs")
    require({item.name for item in (root / "Tools").iterdir() if item.is_file()} == TOOLS,
            "messenger tool directory has unlisted files")
    for name, expected_hash in job["tools"].items():
        require(digest(inside(root, "Tools/" + name)) == expected_hash, "messenger tool digest differs: " + name)
    for name, expected_hash in job["files"].items():
        require(digest(inside(root, name)) == expected_hash, "messenger input digest differs: " + name)
    return root, job


def target_identity(snapshot):
    row = snapshot["target_owner"]
    return {"name": row["module"]["name"], "sha256": row["module"]["sha256"], "rva": row["rva"]}


def phase(directory, source, expected, intent, api, job_hash):
    import Swapp
    from ObservePlainNotePresentation01 import CurveAuthor, Recorder, drawing_state, publish
    from InspectNoteGrid01 import preferences
    from OracleIdentity import application_identity
    from OwnedMessengerMemory import OwnedProcess

    directory.mkdir()
    row = {"passed": False, "input_sha256": expected, "snapshots": {}, "job_sha256": job_hash,
           "document_saves": 0, "document_read_only": True}
    recorder = Recorder(directory / "Record.json", {"role": directory.name, "job_sha256": job_hash})
    controller = author = memory = None

    def snapshot(label):
        recorder.data["stage"] = "read owned messenger " + label
        recorder.flush()
        observed = {"observer_monotonic_ns": monotonic_ns(), **memory.snapshot()}
        row["snapshots"][label] = observed
        recorder.data["result"] = row
        recorder.flush()

    with Swapp.Dismisser() as dialogs:
        try:
            require(digest(source) == expected, "drawing changed before messenger observation")
            Swapp.sweep()
            controller = Swapp.Sw(visible=True)
            identity = application_identity(controller.app)
            row["identity"] = identity
            require(identity["version_matches"] and identity["sha256"] == ORACLE
                    and identity["pe_machine"] == "0x8664", "wrong exact messenger oracle")
            author = CurveAuthor(controller.app, recorder, Swapp)
            model, errors, warnings = controller.open(source, doctype=3, read_only=True)
            row["open"] = [errors, warnings]
            require(model is not None and errors == warnings == 0, "messenger drawing did not open cleanly")
            author.model = model
            memory = OwnedProcess(identity, Swapp.owned_process_ids)
            snapshot("after_open")
            drawing = author.typed(model, "DrawingDoc")
            extension = author.typed(author.get(model, "Extension"), "ModelDocExtension")
            row["initial"] = drawing_state(author, drawing, intent)
            row["initial_preferences"] = preferences(author, model, extension, api)
            row["initial_dirty"] = bool(author.get(model, "GetSaveFlag"))
            snapshot("before_rebuild")
            row["rebuild"] = bool(author.get(model, "ForceRebuild3", False))
            snapshot("after_rebuild")
            require(row["rebuild"], "messenger observation rebuild failed")
            author.get(model, "GraphicsRedraw2")
            snapshot("after_redraw")
            row["rebuilt"] = drawing_state(author, drawing, intent)
            row["rebuilt_preferences"] = preferences(author, model, extension, api)
            row["rebuilt_dirty"] = bool(author.get(model, "GetSaveFlag"))
            require(row["initial"] == row["rebuilt"], "drawing presentation changed during messenger observation")
            require(row["initial_preferences"] == row["rebuilt_preferences"],
                    "document preference switches changed during messenger observation")
            row["target_identities"] = {stage: target_identity(row["snapshots"][stage]) for stage in STAGES}
            row["target_owner_stable"] = all(value == row["target_identities"][STAGES[0]]
                                             for value in row["target_identities"].values())
            row["messenger_pointer_stable"] = len({value["messenger"] for value in row["snapshots"].values()}) == 1
            row["passed"] = True
        except Exception as error:
            if memory is not None:
                row["last_memory_partial"] = memory.partial
            recorder.failure(error)
        finally:
            if memory is not None:
                try:
                    row["rpm_calls"] = memory.read_count
                    row["rpm_bytes"] = memory.read_bytes
                    memory.close()
                    row["query_read_handle_closed"] = True
                except Exception as error:
                    recorder.failure(error, cleanup=True)
            if author is not None and author.model is not None:
                try:
                    recorder.call("close owned drawing without save", controller.close_doc, author.model)
                except Exception as error:
                    recorder.failure(error, cleanup=True)
            if controller is not None:
                try:
                    controller.close()
                except Exception as error:
                    recorder.failure(error, cleanup=True)
                row["controller_diagnostics"] = controller.diagnostics
    row["immutable_input"] = digest(source) == expected
    row["dialogs"] = dialogs.log
    row["first_failure"] = recorder.data["first_failure"]
    row["passed"] = bool(row["passed"] and row["immutable_input"] and not row["dialogs"]
                         and not row.get("controller_diagnostics") and not recorder.data["cleanup_errors"])
    recorder.data.update(result=row, passed=row["passed"], finished_at=time())
    recorder.flush()
    publish(directory / "Result.json", row)
    return row


def run(root, job, job_path, expected):
    require(os.name == "nt", "messenger observation requires the sole root-owned Windows guest")
    from ObservePlainNotePresentation01 import publish

    output = root / "Inspection"
    output.mkdir()
    intent = loads(inside(root, "Inputs/Intent.json").read_bytes())
    api = loads(inside(root, "Inputs/GridApi01.json").read_bytes())
    require(api["version"] == [34, 0] and api["cad_processes_started"] == 0, "wrong preference metadata release")
    rows = {}
    for role in ROLES:
        if role not in ("ControlBefore", "ControlAfter") and not rows["ControlBefore"]["passed"]:
            rows[role] = {"passed": False, "skipped": "leading pristine control failed"}
            continue
        rows[role] = phase(output / role, inside(root, CASES[role]), job["files"][CASES[role]],
                           None if role in ("ControlBefore", "ControlAfter") else intent, api, expected)
    check_job(job_path, expected)
    births = {row["identity"]["process_creation_filetime"] for row in rows.values() if "identity" in row}
    complete = len(births) == len(ROLES) and all(row["passed"] for row in rows.values())
    controls = all(rows[role]["passed"] for role in ("ControlBefore", "ControlAfter"))
    controls = bool(controls and rows["ControlBefore"]["initial"] == rows["ControlAfter"]["initial"]
                    and rows["ControlBefore"]["initial_preferences"] == rows["ControlAfter"]["initial_preferences"])
    comparisons = {}
    if complete:
        for stage in STAGES:
            comparisons[stage] = {
                "native_source": rows["NativeSource"]["target_identities"][stage],
                "generated": rows["Generated"]["target_identities"][stage],
                "target_owner_equal": rows["NativeSource"]["target_identities"][stage]
                                      == rows["Generated"]["target_identities"][stage],
            }
    report = {
        "schema": SCHEMA, "job_sha256": expected, "data_collected": bool(complete and controls),
        "distinct_processes": len(births), "healthy_controls": controls, "phases": rows,
        "source_generated_comparison": comparisons, "process_access_mask": "0x410",
        "debugger_attaches": 0, "breakpoints": 0, "injected_calls": 0, "process_memory_writes": 0,
        "document_saves": 0, "bitmap_saves": 0, "settings_writes": 0, "heldout_inputs_read": 0,
        "runtime_dispatch_invocation_observed": False, "target_module_complete_memory_hash_verified": False,
        "writer_qualified": False, "heldout_accepted": False,
    }
    path = output / "Result.json"
    publish(path, report)
    print(dumps({key: value for key, value in report.items() if key not in ("phases", "source_generated_comparison")}
                | {"result_sha256": digest(path)}))
    return 0 if report["data_collected"] else 3


def main():
    parser = ArgumentParser()
    parser.add_argument("mode", choices=("verify", "run"))
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--job-sha256", required=True)
    args = parser.parse_args()
    root, job = check_job(args.job, args.job_sha256)
    if args.mode == "verify":
        print(dumps({"passed": True, "job_sha256": args.job_sha256, "tools": len(job["tools"]),
                     "files": len(job["files"]), "native_processes": 0, "cad_calls": 0}))
        return 0
    return run(root, job, args.job, args.job_sha256)


if __name__ == "__main__":
    raise SystemExit(main())
