from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import json
import os
from pathlib import Path, PureWindowsPath
import re
import secrets
from shutil import copyfile
import subprocess
import time

from AttachedTopBoxAuthor import AttachedTopBoxAuthor, DRIVERS, PARAMETERS
from AuthorCurves import Recorder, digest, require, write_json
from AuthorRectangleAnchors import CONTROL, ORACLE, control


SCHEMA = "kit.sw2026.attached-top-box-source.v1"
TOOLS = (
    "RunAttachedTopBoxSources.py", "AttachedTopBoxAuthor.py", "AuthorRectangleAnchors.py",
    "AuthorCurves.py", "InspectFresh.py", "OracleIdentity.py", "Swapp.py",
)
ORACLE_VERSION = "34.5.2.0604"
STATES = ("Original", *DRIVERS)
ORIGINAL_F14C = (0.020, 0.030, 0.010)
DISCLOSED_EDITS = (0.027, 0.037, 0.015)


def private_destination(value):
    path = PureWindowsPath(value)
    require(path.is_absolute() and path.drive.casefold() == "c:" and len(path.parts) == 2
            and re.fullmatch(r"KitAttachedTopBoxSources[0-9]{2}", path.name),
            "choose a new C:\\KitAttachedTopBoxSourcesNN guest directory")
    return str(path)


def prepare(args):
    source = Path(__file__).resolve().parent
    parent = source.parent
    require(re.fullmatch(r"[a-f0-9]{40}", args.revision), "supply the committed source revision")
    require(digest(args.control) == CONTROL, "choose the known pristine rectangle control")
    private = private_destination(args.guest_private_root)
    repository = source.parents[3]
    entries = {}
    for filename in TOOLS:
        path = source / filename if (source / filename).is_file() else parent / filename
        require(path.is_file(), f"source tool is unavailable: {filename}")
        tracked = subprocess.check_output([
            "git", "-C", str(repository), "show", f"{args.revision}:{path.relative_to(repository).as_posix()}",
        ])
        require(tracked == path.read_bytes(), f"source tool differs from the requested commit: {filename}")
        entries[filename] = tracked
    target = args.destination.resolve()
    target.mkdir()
    (target / "Tools").mkdir()
    for name, data in entries.items():
        (target / "Tools" / name).write_bytes(data)
    copyfile(args.control, target / "Control.SLDPRT")
    job = target / "Job.json"
    write_json(job, {
        "schema": SCHEMA,
        "source_revision": args.revision,
        "cohort": args.cohort,
        "guest_private_root": private,
        "control_sha256": CONTROL,
        "oracle_sha256": ORACLE,
        "oracle_file_version": ORACLE_VERSION,
        "tools_sha256": {filename: digest(target / "Tools" / filename) for filename in TOOLS},
    })
    print(json.dumps({"job_sha256": digest(job), "cohort": args.cohort}))


def verify(job_path, expected):
    require(digest(job_path) == expected, "frozen source authoring job changed")
    job = json.loads(job_path.read_bytes())
    tools = job_path.parent / "Tools"
    require(job["schema"] == SCHEMA and job["cohort"] in ("disclosed", "sealed")
            and job["control_sha256"] == CONTROL and job["oracle_sha256"] == ORACLE
            and job["oracle_file_version"] == ORACLE_VERSION and re.fullmatch(r"[a-f0-9]{40}", job["source_revision"]),
            "source authoring job has an unexpected profile")
    private_destination(job["guest_private_root"])
    require(Path(__file__).resolve().parent == tools and set(job["tools_sha256"]) == set(TOOLS),
            "use the complete frozen source authoring tools")
    for name, expected in job["tools_sha256"].items():
        require(digest(tools / name) == expected, f"source authoring tool changed: {name}")
    require(digest(job_path.parent / "Control.SLDPRT") == CONTROL, "pristine rectangle control changed")
    return job


def cases(cohort):
    if cohort == "disclosed":
        return {"Disclosed": {"original_m": ORIGINAL_F14C, "edit_m": DISCLOSED_EDITS}}
    require(os.name == "nt", "sealed geometry is sampled only inside the Windows guest")

    def dimensions(ranges):
        return tuple((low + secrets.randbelow(high - low + 1)) / 1e6 for low, high in ranges)

    return {
        "Slot01": {
            "original_m": dimensions(((33000, 43000), (16000, 24000), (5000, 9000))),
            "edit_m": dimensions(((45000, 51000), (25000, 28000), (11000, 14000))),
        },
        "Slot02": {
            "original_m": dimensions(((14000, 19000), (44000, 53000), (15000, 19000))),
            "edit_m": dimensions(((22000, 27000), (54000, 59000), (21000, 27100))),
        },
    }


def state_lengths(case, state):
    sizes = list(case["original_m"])
    if state != "Original":
        index = DRIVERS.index(state)
        sizes[index] = case["edit_m"][index]
    return tuple(sizes)


def sample_path(directory, state):
    return directory / "Native" / (state + ".SLDPRT")


def file_identity(path):
    return {"sha256": digest(path), "bytes": path.stat().st_size}


def unchanged(directory, files):
    for state, row in files.items():
        require(file_identity(sample_path(directory, state)) == row, "saved native source identity changed")


def require_same_history(original, other):
    for name in ("tree", "relations", "origin_relation", "top_parent", "boss_parent", "end_condition"):
        require(original[name] == other[name], f"signed Top source changed its {name}")


def snapshot(author, case, state):
    value = author.snapshot(state_lengths(case, state))
    if "source_text" in case:
        from AuthorPartProperties import SUMMARY_FIELDS, dispatch_property, manager, read_text

        expected = case["source_text"]
        file_owner = manager(author, author.model, "")
        properties = {name: read_text(author, file_owner, name) for name in author.get(file_owner, "GetNames") or ()}
        require(properties.keys() == expected["file"].keys()
                and all(row["raw"] == row["resolved"] == expected["file"][name]
                        and row["type"] == 30 and not row["linked"] for name, row in properties.items()),
                "attached box did not retain its literal FreeCAD file properties")
        summary = {name: str(dispatch_property(author, author.model, "SummaryInfo", SUMMARY_FIELDS[name]))
                   for name in expected["summary"]}
        require(summary == expected["summary"], "attached box did not retain the authored summary")
        value.update(source_properties=properties, source_summary=summary)
    return value


def author_states(author, controller, directory, case, generated_input=None):
    (directory / "Native").mkdir()
    if generated_input is None:
        author.build(controller, case["original_m"])
    else:
        author.model, error, warning = author.rec.call("open exact generated attached Top box", controller.open, generated_input)
        require(author.model is not None and error == warning == 0
                and Path(author.get(author.model, "GetPathName")).samefile(generated_input),
                "generated attached box did not open cleanly")
        author.rec.data["generated_open_status"] = [error, warning]
        require(len(author.get(author.model, "GetBodies2", 0, False) or ()) == 1,
                "fresh generated open did not expose one solid")
        author.rec.flush()
    original = snapshot(author, case, "Original")
    files, observations = {}, {}
    for state in STATES:
        if state != "Original":
            index = DRIVERS.index(state)
            author.edit(PARAMETERS[index], case["edit_m"][index])
            state_observation = snapshot(author, case, state)
            require_same_history(original, state_observation)
        else:
            state_observation = original
        path = sample_path(directory, state)
        status = author.rec.call("save native source sibling", controller.save_as, author.model, path)
        require(tuple(status) == (True, 0, 0), "native source save returned an error or warning")
        files[state] = file_identity(path)
        require(files[state]["bytes"] > 0, "saved native part is empty")
        observations[state] = state_observation
        if state != "Original":
            author.edit(PARAMETERS[index], case["original_m"][index])
            require_same_history(original, snapshot(author, case, "Original"))
    return files, observations


def reopen_states(author, controller, directory, case, authored):
    files, observations = authored["files"], {}
    unchanged(directory, files)
    for state in STATES:
        path = sample_path(directory, state)
        author.model, error, warning = author.rec.call("fresh open signed Top source", controller.open, path, read_only=True)
        require(author.model is not None and error == warning == 0
                and Path(author.get(author.model, "GetPathName")).samefile(path),
                "signed Top source did not open its sealed path cleanly")
        require(len(author.get(author.model, "GetBodies2", 0, False) or ()) == 1, "fresh source open did not expose one solid")
        observed = snapshot(author, case, state)
        require_same_history(authored["observations"][state], observed)
        observations[state] = observed | {"open_errors": error, "open_warnings": warning}
        controller.close_doc(author.model)
        author.model = None
    unchanged(directory, files)
    return files, observations


def oracle_identity(value):
    require(value["sha256"] == ORACLE and value["file_version"] == ORACLE_VERSION
            and value["version_matches"] and value["pe_machine"].casefold() == "0x8664",
            "native source oracle executable differs from SOLIDWORKS 2026 SP05.2 x64")
    return value


def phase(directory, case, name, prior=None, *, generated_input=None):
    import Swapp
    from OracleIdentity import application_identity

    directory.mkdir(parents=True, exist_ok=True)
    rec = Recorder(directory / (name + ".json"), {"source": case, "phase": name})
    result, controller, author, preference = {"passed": False}, None, None, None
    with Swapp.Dismisser() as dialogs:
        try:
            rec.call("verify idle vendor oracle", Swapp.sweep)
            controller = rec.call("start fresh 2026 source oracle", Swapp.Sw)
            require(controller.revision == "34.5.2", "native source oracle COM revision differs")
            result["oracle_identity"] = oracle_identity(rec.call("verify source oracle identity", application_identity, controller.app))
            author = AttachedTopBoxAuthor(controller.app, rec, Swapp)
            if name == "Author":
                preference = bool(author.get(author.app, "GetUserPreferenceToggle", 10))
                author.get(author.app, "SetUserPreferenceToggle", 10, False)
                require(not author.get(author.app, "GetUserPreferenceToggle", 10), "interactive dimension prompt is still enabled")
                files, observed = author_states(author, controller, directory, case, generated_input)
            else:
                files, observed = reopen_states(author, controller, directory, case, prior)
            result.update(passed=True, files=files, observations=observed)
        except Exception as error:
            rec.failure(error)
        finally:
            if preference is not None:
                try:
                    author.get(author.app, "SetUserPreferenceToggle", 10, preference)
                    require(bool(author.get(author.app, "GetUserPreferenceToggle", 10)) == preference,
                            "native dimension prompt preference was not restored")
                except Exception as error:
                    rec.failure(error, cleanup=True)
            if controller is not None:
                try:
                    if author is not None and author.model is not None:
                        controller.close_doc(author.model)
                    controller.close()
                    result["controller_diagnostics"] = controller.diagnostics
                except Exception as error:
                    rec.failure(error, cleanup=True)
    result["dialogs"] = dialogs.log
    result["passed"] = bool(result["passed"] and not dialogs.log and not result.get("controller_diagnostics")
                            and not rec.data["first_failure"] and not rec.data["cleanup_errors"])
    if result["passed"]:
        try:
            unchanged(directory, result["files"])
        except Exception as error:
            rec.failure(error)
            result["passed"] = False
    result["numeric_checks"] = len(rec.data["checks"])
    result["first_failure"] = rec.data["first_failure"]
    if generated_input is not None:
        result["generated_open_status"] = rec.data.get("generated_open_status")
    rec.data.update(result=result, passed=result["passed"], finished_at=time.time())
    rec.flush()
    return result | {"record_sha256": digest(rec.path)}


def run(job_path, expected):
    require(os.name == "nt", "native source authoring runs in the Windows guest")
    job = verify(job_path, expected)
    root = Path(job["guest_private_root"])
    root.mkdir()
    public = job_path.parent / "Result.json"
    require(not public.exists(), "source receipt already exists")
    private_cases = cases(job["cohort"])
    spec = root / "SourceSpecifications.json"
    write_json(spec, private_cases)
    status = {
        "schema": SCHEMA, "job_sha256": expected, "cohort": job["cohort"], "spec_sha256": digest(spec),
        "source_revision": job["source_revision"], "tools_sha256": job["tools_sha256"],
        "oracle_sha256": ORACLE, "oracle_file_version": ORACLE_VERSION,
        "phases": [], "sources": {}, "passed": False,
        "writer_outputs": 0, "native_writer_acceptance": False, "heldout_payloads_shared": 0,
    }
    if job["cohort"] == "disclosed":
        status["disclosed_source_spec"] = private_cases
    write_json(public, status)

    def measure(label, function, *args):
        status["stage"] = label
        write_json(public, status)
        record = function(*args)
        value = record.get("oracle_identity")
        identity = {} if value is None else oracle_identity(value)
        status["phases"].append({
            "name": label, "passed": record["passed"], "record_sha256": record["record_sha256"],
            "process_id": identity.get("process_id"), "process_creation_filetime": identity.get("process_creation_filetime"),
        })
        write_json(public, status)
        require(record["passed"], "source phase failed")
        return record

    seed = job_path.parent / "Control.SLDPRT"
    with (root / "Oracle.log").open("x", encoding="utf-8") as log, redirect_stdout(log), redirect_stderr(log):
        try:
            measure("ControlBefore", control, root, "ControlBefore", seed)
            for name, case in private_cases.items():
                directory = root / name
                authored = measure(name + "Author", phase, directory, case, "Author")
                reopened = measure(name + "Reopen", phase, directory, case, "Reopen", authored)
                status["sources"][name] = {
                    "files": reopened["files"], "author_record_sha256": authored["record_sha256"],
                    "reopen_record_sha256": reopened["record_sha256"],
                }
                write_json(public, status)
        except Exception as error:
            status["failure"] = {"stage": status["stage"], "type": type(error).__name__}
            print(repr(error))
        finally:
            try:
                measure("ControlAfter", control, root, "ControlAfter", seed)
            except Exception as error:
                status["final_control_failure"] = type(error).__name__
                print(repr(error))
    verify(job_path, expected)
    identities = {(value["process_id"], value["process_creation_filetime"])
                  for value in status["phases"] if value["process_id"] is not None}
    status["distinct_processes"] = len(identities)
    status["controls_healthy"] = [item["passed"] for item in status["phases"]
                                  if item["name"] in ("ControlBefore", "ControlAfter")] == [True, True]
    status["passed"] = (status["controls_healthy"] and len(status["sources"]) == len(private_cases)
                        and len(identities) == len(status["phases"]) == 2 * len(private_cases) + 2
                        and "failure" not in status and "final_control_failure" not in status)
    status["heldout_sources_locked"] = len(private_cases) if status["passed"] and job["cohort"] == "sealed" else 0
    status["stage"] = "source_batch_passed" if status["passed"] else "source_batch_failed"
    write_json(public, status)
    print(json.dumps({key: status[key] for key in ("stage", "passed", "controls_healthy", "distinct_processes", "heldout_sources_locked")}))
    return 0 if status["passed"] else 3


def main():
    parser = argparse.ArgumentParser(description="Author and verify independent native Top-plane box sources")
    modes = parser.add_subparsers(dest="mode", required=True)
    host = modes.add_parser("prepare")
    host.add_argument("control", type=Path)
    host.add_argument("destination", type=Path)
    host.add_argument("--guest-private-root", required=True)
    host.add_argument("--cohort", choices=("disclosed", "sealed"), required=True)
    host.add_argument("--revision", required=True)
    guest = modes.add_parser("run")
    guest.add_argument("job", type=Path)
    guest.add_argument("--job-sha256", required=True)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args)
        return 0
    return run(args.job.resolve(strict=True), args.job_sha256)


if __name__ == "__main__":
    raise SystemExit(main())
