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

from AuthorCurves import Recorder, digest, require, write_json
from AuthorImportedBody import ImportedBodyAuthor
from AuthorRectangleAnchors import CONTROL, ORACLE, control


SCHEMA = "kit.sw2026.imported-body-source.v1"
VERSION = "34.5.2.0604"
OWN_TOOLS = ("RunImportedBodySources.py", "AuthorImportedBody.py")
CONTROL_TOOLS = ("AuthorRectangleAnchors.py", "AuthorCurves.py", "InspectFresh.py", "OracleIdentity.py", "Swapp.py")
DISCLOSED = {"face_center_m": (0.007, -0.011, 0.004), "size_m": (0.019, 0.027, 0.013)}
COHORTS = ("disclosed", "sealed", "contrast", "topology", "sealed-topology")
PUBLIC_COHORTS = ("contrast", "topology")
SEALED_COHORTS = ("sealed", "sealed-topology")
SEALED_TOPOLOGY_TOOLS = (
    "SealedCylinderSource.py",
    "ObserveCylinderExchange.py",
    "ObserveKernelBodyRestore.py",
    "ObserveKernelExchange.py",
)


def private_destination(value):
    path = PureWindowsPath(value)
    require(path.is_absolute() and path.drive.casefold() == "c:" and len(path.parts) == 2
            and re.fullmatch(r"KitImportedBodySources[0-9]{2}", path.name),
            "choose a new C:\\KitImportedBodySourcesNN guest directory")
    return str(path)


def own_tools(cohort):
    return OWN_TOOLS + (SEALED_TOPOLOGY_TOOLS if cohort == "sealed-topology" else ())


def prepare(args):
    source = Path(__file__).resolve().parent
    repository = source.parents[3]
    require(re.fullmatch(r"[a-f0-9]{40}", args.revision), "supply the committed source revision")
    require(digest(args.control) == CONTROL, "choose the known pristine rectangle control")
    private = private_destination(args.guest_private_root)
    target = args.destination.resolve()
    require(not target.is_relative_to(repository), "keep the source packet outside the Kit checkout")
    tool_sources = [*(source / name for name in own_tools(args.cohort)), *(source.parent / name for name in CONTROL_TOOLS)]
    entries = {}
    for file in tool_sources:
        relative = file.relative_to(repository).as_posix()
        tracked = subprocess.check_output(["git", "-C", str(repository), "show", f"{args.revision}:{relative}"])
        require(tracked == file.read_bytes(), f"source tool differs from the committed revision: {file.name}")
        entries[file.name] = tracked
    target.mkdir()
    tools = target / "Tools"
    tools.mkdir()
    for name, content in entries.items():
        (tools / name).write_bytes(content)
    seed = target / "Control.SLDPRT"
    copyfile(args.control, seed)
    require(digest(seed) == CONTROL, "copied pristine rectangle control changed")
    job = target / "Job.json"
    write_json(job, {"schema": SCHEMA, "source_revision": args.revision, "cohort": args.cohort,
                     "guest_private_root": private, "control_sha256": CONTROL, "oracle_sha256": ORACLE,
                     "oracle_version": VERSION, "tools_sha256": {name: digest(tools / name) for name in entries}})
    print(json.dumps({"cohort": args.cohort, "job_sha256": digest(job)}))


def verify(job_path, expected):
    require(digest(job_path) == expected, "frozen source job changed")
    job = json.loads(job_path.read_bytes())
    tools = job_path.parent / "Tools"
    require(job["schema"] == SCHEMA and job["cohort"] in COHORTS
            and job["oracle_version"] == VERSION and job["oracle_sha256"] == ORACLE
            and job["control_sha256"] == CONTROL and re.fullmatch(r"[a-f0-9]{40}", job["source_revision"]),
            "source job profile differs")
    private_destination(job["guest_private_root"])
    required_tools = set(own_tools(job["cohort"]) + CONTROL_TOOLS)
    require(Path(__file__).resolve().parent == tools and set(job["tools_sha256"]) == required_tools,
            "run the complete frozen source tools")
    if job["cohort"] == "sealed-topology":
        require(job_path.name == "Job.json" and not job_path.is_symlink() and not tools.is_symlink(),
                "use the regular frozen sealed source packet")
        require({item.name for item in job_path.parent.iterdir()} <= {"Job.json", "Tools", "Control.SLDPRT", "Result.json"}
                and {item.name for item in tools.iterdir()} == required_tools
                and all(item.is_file() and not item.is_symlink() for item in tools.iterdir())
                and (job_path.parent / "Control.SLDPRT").is_file()
                and not (job_path.parent / "Control.SLDPRT").is_symlink(),
                "sealed source packet contains unbound inputs or private outputs")
    for name, expected_digest in job["tools_sha256"].items():
        require(digest(tools / name) == expected_digest, f"source tool changed: {name}")
    require(digest(job_path.parent / "Control.SLDPRT") == CONTROL, "pristine rectangle control changed")
    return job


def cases(cohort):
    if cohort == "disclosed":
        return {"Disclosed": DISCLOSED}
    if cohort == "contrast":
        feature_name = "Transfer Δ17"
        return {
            "OtherShape": {"face_center_m": (-0.018, 0.021, -0.008), "size_m": (0.010, 0.039, 0.021)},
            "RenamedFeature": DISCLOSED | {"feature_name": feature_name},
            "RenamedBody": DISCLOSED | {"feature_name": feature_name, "body_name": "Casting Ω72"},
        }
    if cohort == "topology":
        return {
            "CylinderZ": {"face_center_m": (-0.008, 0.019, 0.004), "axis": (0.0, 0.0, 1.0),
                          "radius_m": 0.012, "height_m": 0.031},
            "CylinderReverseY": {"face_center_m": (0.013, 0.023, -0.017), "axis": (0.0, -1.0, 0.0),
                                 "radius_m": 0.0075, "height_m": 0.019},
        }
    if cohort == "sealed-topology":
        from SealedCylinderSource import private_specification

        return private_specification()["cases"]
    require(os.name == "nt", "sample held-out inputs only inside the Windows guest")

    def metres(ranges):
        return tuple((low + secrets.randbelow(high - low + 1)) / 1e6 for low, high in ranges)

    return {
        "Slot01": {"face_center_m": metres(((-32000, -18000), (4000, 13000), (-16000, -5000))),
                   "size_m": metres(((31000, 41000), (7000, 12000), (44000, 53000)))},
        "Slot02": {"face_center_m": metres(((18000, 35000), (-21000, -5000), (8000, 18000))),
                   "size_m": metres(((10000, 15000), (49000, 59000), (22000, 31000)))},
    }


def oracle_identity(record):
    require(record["sha256"] == ORACLE and record["file_version"] == VERSION and record["version_matches"]
            and record["pe_machine"].casefold() == "0x8664", "native source executable differs from 2026 SP05.2 x64")
    require(record["process_id"] > 0 and record["process_creation_filetime"] > 0, "native process identity is incomplete")
    return record


def file_identity(path):
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def compare_observations(before, after):
    require(before["feature"] == after["feature"] and before["tree"] == after["tree"],
            "import feature identity or tree changed")
    require(before["body_name"] == after["body_name"] and before["topology"] == after["topology"],
            "imported body identity or topology changed")


def author_phase(observer, controller, path, case):
    feature = observer.author(controller, case)
    observer.rebuild()
    before = observer.observe(feature, case)
    saved = observer.rec.call("save native imported source", controller.save_as, observer.model, path)
    require(tuple(saved) == (True, 0, 0), "native import save returned an error or warning")
    require(Path(observer.get(observer.model, "GetPathName")).samefile(path), "native save selected a different path")
    token = observer.persistent_reference(feature)
    owner = observer.resolve_feature(token)
    observer.exact_object(owner, feature, "saved feature resolved from the preserved reference")
    after = observer.observe(owner, case)
    compare_observations(before, after)
    identity = file_identity(path)
    require(identity["bytes"] > 0, "native import save is empty")
    return {"source": identity, "feature_reference": token, "post_save": after, "save": tuple(saved)}


def reopen_phase(observer, controller, path, case, authored):
    require(file_identity(path) == authored["source"], "native source changed before reopen")
    observer.model, error, warning = observer.rec.call("open native import source read-only", controller.open,
                                                       path, read_only=True)
    require(observer.model is not None and error == warning == 0
            and Path(observer.get(observer.model, "GetPathName")).samefile(path), "native source did not open cleanly")
    feature = observer.resolve_feature(authored["feature_reference"])
    cold = observer.observe(feature, case)
    compare_observations(authored["post_save"], cold)
    observer.rebuild()
    rebuilt = observer.observe(observer.resolve_feature(authored["feature_reference"]), case)
    compare_observations(cold, rebuilt)
    return {"source": authored["source"], "cold": cold, "rebuilt": rebuilt,
            "open_errors": error, "open_warnings": warning}


def phase(directory, case, name, prior=None, *, author_type=ImportedBodyAuthor, expected_observations=0):
    import Swapp
    from OracleIdentity import application_identity

    directory.mkdir(exist_ok=True)
    rec = Recorder(directory / (name + ".json"), {"source": case, "phase": name})
    path = directory / "Source.SLDPRT"
    result, controller, observer = {"passed": False}, None, None
    with Swapp.Dismisser() as dialogs:
        try:
            rec.call("verify idle oracle", Swapp.sweep)
            controller = rec.call("launch fresh source oracle", Swapp.Sw)
            require(controller.revision == "34.5.2", "native COM revision differs")
            result["oracle_identity"] = oracle_identity(rec.call("bind exact source oracle", application_identity, controller.app))
            observer = author_type(controller.app, rec, Swapp)
            measured = (author_phase(observer, controller, path, case) if prior is None
                        else reopen_phase(observer, controller, path, case, prior))
            if expected_observations:
                periodic_count = len(rec.data.get("periodic_observations", ()))
                require(periodic_count == expected_observations, "sealed cylinder phase lacks both periodic observations")
                measured["periodic_observations"] = periodic_count
            result.update(measured, passed=True)
        except Exception as error:
            rec.failure(error)
        finally:
            if controller is not None:
                try:
                    if observer is not None and observer.model is not None:
                        controller.close_doc(observer.model)
                    controller.close()
                    result["controller_diagnostics"] = controller.diagnostics
                except Exception as error:
                    rec.failure(error, cleanup=True)
    result["dialogs"] = dialogs.log
    if result["passed"]:
        try:
            require(file_identity(path) == result["source"], "native source changed after process exit")
        except Exception as error:
            rec.failure(error)
    result["passed"] = bool(result["passed"] and not dialogs.log and not result.get("controller_diagnostics")
                            and not rec.data["first_failure"] and not rec.data["cleanup_errors"])
    rec.data.update(result=result, passed=result["passed"], finished_at=time.time())
    rec.flush()
    return result | {"record_sha256": digest(rec.path)}


def run(job_path, expected):
    require(os.name == "nt", "run the source protocol in the oracle guest")
    job = verify(job_path, expected)
    root = Path(job["guest_private_root"])
    public = job_path.parent / "Result.json"
    require(not public.exists(), "source receipt already exists")
    root.mkdir()
    seed = root / "Control.SLDPRT"
    copyfile(job_path.parent / seed.name, seed)
    require(digest(seed) == CONTROL, "the guest-local pristine control changed")
    sealed_topology = job["cohort"] == "sealed-topology"
    author_type, required_observations = ImportedBodyAuthor, 0
    if sealed_topology:
        from SealedCylinderSource import (
            OBSERVATIONS_PER_PHASE, SLOT_NAMES, SOURCE_PROFILE, SealedCylinderAuthor,
            private_specification,
        )

        specification = private_specification()
        author_type, required_observations = SealedCylinderAuthor, OBSERVATIONS_PER_PHASE
    else:
        specification = cases(job["cohort"])
    specifications = root / "SourceSpecifications.json"
    write_json(specifications, specification)
    specifications_digest = digest(specifications)
    if sealed_topology:
        frozen = json.loads(specifications.read_bytes())
        require(digest(specifications) == specifications_digest and tuple(frozen["cases"]) == SLOT_NAMES,
                "sealed cylinder specification changed before native authoring")
        private_cases = frozen["cases"]
    else:
        private_cases = specification
    status = {"schema": SCHEMA, "source_revision": job["source_revision"], "cohort": job["cohort"],
              "job_sha256": expected, "specifications_sha256": specifications_digest,
              "specifications_locked_at_unix_s": time.time(),
              "tools_sha256": job["tools_sha256"], "oracle_sha256": ORACLE, "oracle_version": VERSION,
              "phases": [], "sources": {}, "passed": False, "heldout_sources_locked": 0,
              "writer_outputs": 0, "native_writer_acceptance": False, "heldout_payloads_shared": 0}
    if job["cohort"] == "disclosed":
        status["disclosed_specification"] = DISCLOSED
    if sealed_topology:
        status.update(source_profile=SOURCE_PROFILE, periodic_source_observations=0)
    write_json(public, status)

    def measure(label, function, *args, **options):
        status["stage"] = label
        write_json(public, status)
        result = function(*args, **options)
        identity = result.get("oracle_identity")
        if identity is not None:
            oracle_identity(identity)
        status["phases"].append({"name": label, "passed": result["passed"],
                                 "record_sha256": result["record_sha256"],
                                 "process_id": identity["process_id"] if identity else None,
                                 "process_creation_filetime": identity["process_creation_filetime"] if identity else None})
        write_json(public, status)
        require(result["passed"] and identity is not None, "native source phase failed")
        return result

    with (root / "Oracle.log").open("x", encoding="utf-8") as log, redirect_stdout(log), redirect_stderr(log):
        try:
            measure("ControlBefore", control, root, "ControlBefore", seed)
            phase_options = {"author_type": author_type, "expected_observations": required_observations} if sealed_topology else {}
            for name, case in private_cases.items():
                directory = root / name
                authored = measure(name + "Author", phase, directory, case, "Author", **phase_options)
                reopened = measure(name + "Reopen", phase, directory, case, "Reopen", authored, **phase_options)
                status["sources"][name] = {"source_sha256": reopened["source"]["sha256"],
                                           "author_record_sha256": authored["record_sha256"],
                                           "reopen_record_sha256": reopened["record_sha256"]}
                if job["cohort"] == "disclosed":
                    data = reopened["cold"]
                    status["disclosed_observation"] = {key: data[key] for key in ("feature", "body_count", "topology", "mass_si")}
                if job["cohort"] in PUBLIC_COHORTS:
                    data = reopened["cold"]
                    status["sources"][name]["observed"] = {key: data[key] for key in
                                                            ("feature", "body_name", "body_count", "topology", "mass_si")}
                if sealed_topology:
                    status["periodic_source_observations"] += authored["periodic_observations"] + reopened["periodic_observations"]
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
        try:
            verify(job_path, expected)
            require(digest(specifications) == status["specifications_sha256"], "private specifications changed")
            for name, result in status["sources"].items():
                require(digest(root / name / "Source.SLDPRT") == result["source_sha256"], "locked source changed")
            if sealed_topology:
                require(len({result["source_sha256"] for result in status["sources"].values()}) == len(private_cases)
                        and status["periodic_source_observations"] == 2 * required_observations * len(private_cases),
                        "sealed cylinder custody lacks distinct originals and all measured states")
        except Exception as error:
            status["custody_failure"] = type(error).__name__
            print(repr(error))

    identities = {(row["process_id"], row["process_creation_filetime"]) for row in status["phases"]
                  if row["process_id"] is not None}
    status["distinct_processes"] = len(identities)
    status["controls_healthy"] = [row["passed"] for row in status["phases"]
                                  if row["name"] in ("ControlBefore", "ControlAfter")] == [True, True]
    status["passed"] = (status["controls_healthy"] and len(status["sources"]) == len(private_cases)
                        and len(identities) == len(status["phases"]) == 2 * len(private_cases) + 2
                        and not {"failure", "final_control_failure", "custody_failure"} & status.keys())
    status["heldout_sources_locked"] = len(private_cases) if status["passed"] and job["cohort"] in SEALED_COHORTS else 0
    if status["passed"] and job["cohort"] in PUBLIC_COHORTS:
        try:
            for name, result in status["sources"].items():
                destination = job_path.parent / (name + ".SLDPRT")
                require(not destination.exists(), "the disclosed contrast output already exists")
                copyfile(root / name / "Source.SLDPRT", destination)
                require(digest(destination) == result["source_sha256"], "the disclosed contrast copy changed")
        except Exception as error:
            status["passed"] = False
            status["disclosed_copy_failure"] = type(error).__name__
    if status["passed"]:
        status["source_batch_locked_at_unix_s"] = time.time()
    status["stage"] = "source_batch_passed" if status["passed"] else "source_batch_failed"
    write_json(public, status)
    print(json.dumps({key: status[key] for key in ("stage", "passed", "controls_healthy", "distinct_processes", "heldout_sources_locked")}))
    return 0 if status["passed"] else 3


def main():
    parser = argparse.ArgumentParser(description="Author and measure native SOLIDWORKS imported-body sources")
    modes = parser.add_subparsers(dest="mode", required=True)
    planning = modes.add_parser("prepare")
    planning.add_argument("control", type=Path)
    planning.add_argument("destination", type=Path)
    planning.add_argument("--guest-private-root", required=True)
    planning.add_argument("--cohort", choices=COHORTS, required=True)
    planning.add_argument("--revision", required=True)
    native = modes.add_parser("run")
    native.add_argument("job", type=Path)
    native.add_argument("--job-sha256", required=True)
    native.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args)
        return 0
    if args.verify_only:
        require(not args.job.is_symlink(), "use a regular source job")
        job = verify(args.job.resolve(), args.job_sha256)
        print(json.dumps({"verified": True, "cohort": job["cohort"], "native_processes": 0}))
        return 0
    return run(args.job.resolve(), args.job_sha256)


if __name__ == "__main__":
    raise SystemExit(main())
