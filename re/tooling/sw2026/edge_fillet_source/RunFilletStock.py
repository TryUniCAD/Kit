from argparse import ArgumentParser
from json import dumps, loads
from pathlib import Path
from subprocess import TimeoutExpired, run
import os
import sys

from FilletModel import predict, require
from FilletPacket import CONTROL, job_bytes
from FilletStockPacket import (
    NAMES, ORACLE_AUTHORITY, PHASES, REGISTERED_API,
    load_job, pinned, sha, stock_target, write_new,
)

SCHEMA = "kit.sw2026.edge-fillet-stock-acquisition.v1"
TIMEOUT = 180
SKETCH = "Sketch1"
BOSS = "Boss-Extrude1"


def windows_paths(folder, root):
    require(os.name == "nt", "the licensed stock acquisition is Windows-only")
    base = Path(root)
    require(base.is_dir() and base.resolve() == base and not base.is_junction()
            and folder == base / "Packet" and folder.resolve() == folder and not folder.is_junction()
            and Path(__file__).resolve().parent == folder / "Tool", "stock job must run from its exact direct local packet")
    return base / "Candidates", base / "NativeSaved", base / "Run01"


def measure(author, case, label):
    model = author.model
    configuration = author.get(author.get(model, "ConfigurationManager"), "ActiveConfiguration")
    require(str(author.get(configuration, "Name")) == "Default", "stock active configuration differs")
    diagnostics = int(author.get(author.get(model, "Extension"), "GetWhatsWrongCount"))
    require(diagnostics == 0, "stock contains native diagnostics")
    tree = author.feature_tree(required_names=(SKETCH, BOSS))
    require(not any("fillet" in row["type"].casefold() for row in tree), "unexpected fillet in stock-only tree")
    feature = author.inspect_feature(BOSS, SKETCH, case["size_mm"][2], True)
    require(not feature["reverse"], "stock boss does not use forward blind depth")
    profile, inverse = author.inspect_profile(SKETCH, author.profile(case))
    expected = predict(case)
    measured = author.measure_body(expected, inverse, label)
    boss = author.get(model, "FeatureByName", BOSS)
    endpoints = tuple(author.transform(point, inverse) for point in expected["source_edge"])
    _, edge = author.find_edge(endpoints, boss)
    return {"configuration": "Default", "diagnostics": diagnostics, "tree": tree,
            "boss": feature, "profile": profile, "body": measured, "edge": edge}


def candidate_phase(case, candidate, pin, target, record_path):
    import Swapp
    from AuthorCurves import Recorder
    from FilletApi import installed_registration
    from FilletAuthor import FilletAuthor
    from FilletSourcePhase import has_exact_identity
    from OracleIdentity import application_identity

    pinned(candidate, pin)
    require(not target.exists() and not target.is_symlink(), "native stock save path is occupied")
    record = Recorder(record_path, {"case": case["name"], "candidate_sha256": pin})
    record.data.update(schema="kit.sw2026.edge-fillet-stock-phase.v1", native_save_sha256=None)
    session = None
    with Swapp.Dismisser() as monitor:
        try:
            constants, api = record.call("inspect exact registered SOLIDWORKS API", installed_registration, Swapp)
            require(sha(job_bytes(api)) == REGISTERED_API, "stock probe's registered API differs")
            record.data["registered_api_sha256"] = REGISTERED_API
            session = record.call("launch fresh versioned SOLIDWORKS COM", Swapp.Sw)
            identity = record.call("verify actual native process identity", application_identity, session.app)
            record.data["oracle_identity"] = identity
            record.flush()
            require(has_exact_identity(identity) and session.revision == "34.5.2", "stock probe needs exact native build")
            author = FilletAuthor(session.app, record, constants)
            author.model, errors, warnings = record.call("open guarded model-only stock", session.open, candidate)
            record.data["open_status"] = {"opened": author.model is not None, "errors": errors, "warnings": warnings}
            record.flush()
            require(record.data["open_status"] == {"opened": True, "errors": 0, "warnings": 0}
                    and Path(str(author.get(author.model, "GetPathName"))) == candidate,
                    "stock did not open cleanly at its encoded locator")
            record.data["cold"] = record.call("measure cold stock before explicit rebuild", measure, author, case, "cold",
                                               parameters=[case["name"]])
            record.flush()
            record.call("explicitly rebuild native stock", author.clean_rebuild)
            record.data["rebuilt"] = record.call("measure rebuilt native stock", measure, author, case, "rebuilt",
                                                  parameters=[case["name"]])
            record.flush()
            require(record.data["cold"]["tree"] == record.data["rebuilt"]["tree"], "explicit rebuild changed the stock tree")
            status = record.call("save native stock derivative separately", session.save_as, author.model, target)
            record.data["native_save_status"] = list(status)
            record.flush()
            require(status == (True, 0, 0) and target.is_file() and target.resolve() == target
                    and Path(str(author.get(author.model, "GetPathName"))) == target,
                    "native stock save did not publish a clean separate derivative")
            saved = target.read_bytes()
            require(bool(saved), "native stock derivative is empty")
            record.data["native_save_sha256"] = sha(saved)
        except Exception as error:
            record.failure(error)
        finally:
            if session is not None:
                try:
                    session.close()
                except Exception as error:
                    record.failure(error, cleanup=True)
                record.data["controller_diagnostics"] = session.diagnostics
    record.data["dialogs"] = monitor.log
    try:
        pinned(candidate, pin)
        record.data["candidate_unchanged"] = True
        if record.data["native_save_sha256"]:
            pinned(target, record.data["native_save_sha256"])
    except Exception as error:
        record.failure(error)
    record.data["passed"] = bool(record.data["native_save_sha256"] and record.data.get("candidate_unchanged")
                                 and not record.data["first_failure"] and not record.data["cleanup_errors"]
                                 and not record.data["dialogs"] and not record.data.get("controller_diagnostics"))
    record.flush()
    return record.data["passed"]


def worker(job, folder, root, cases, paths, phase):
    import Swapp
    from FilletSourcePhase import run_control

    candidates, saved, run_dir = paths
    location = run_dir / phase
    require(all(path.is_dir() and path.resolve() == path and not path.is_junction()
                for path in (*paths, location)) and not Swapp.application_pids(),
            "stock phase needs owned direct paths and an idle oracle")
    record = location / "Record.json"
    require(not record.exists() and not record.is_symlink(), "stock phase record path is occupied")
    if phase not in NAMES:
        return run_control(folder / "Control.SLDPRT", record)
    name = f"{phase}.SLDPRT"
    candidate = candidates / name
    pin = job["construction"][phase]["sha256"]
    require(str(candidate) == stock_target(root, phase), "candidate path differs from its encoded locator")
    return candidate_phase(cases[phase], candidate, pin, saved / name, record)


def phase_result(role, record, pin, status, stderr, timed_out):
    from FilletSourcePhase import has_exact_identity

    raw = record.read_bytes() if record.is_file() else b""
    data = loads(raw) if raw else {}
    identity = data.get("oracle_identity", {})
    process = [identity.get("process_id"), identity.get("process_creation_filetime")]
    exact = has_exact_identity(identity) and all(type(value) is int and value > 0 for value in process)
    failure = data.get("first_failure") or {}
    summary = {"passed": bool(status == 0 and not stderr and exact and data.get("passed") is True),
               "worker_exit_code": status, "worker_timed_out": timed_out, "process": process if exact else None,
               "executable_build": identity.get("file_version"), "executable_sha256": identity.get("sha256"),
               "raw_receipt_sha256": sha(raw) if raw else None, "failure_type": failure.get("type"),
               "failure_stage": failure.get("stage"), "dialogs_observed": bool(data.get("dialogs")),
               "cleanup_diagnostics": bool(data.get("cleanup_errors") or data.get("controller_diagnostics"))}
    if role not in NAMES:
        return summary | {"control_sha256": data.get("sha256")}
    cold, rebuilt = data.get("cold", {}), data.get("rebuilt", {})
    checks = data.get("checks", ())
    return summary | {"candidate_sha256": pin, "candidate_unchanged": data.get("candidate_unchanged", False),
                      "native_save_sha256": data.get("native_save_sha256"), "open_status": data.get("open_status"),
                      "cold_counts": cold.get("body", {}).get("counts"),
                      "rebuilt_counts": rebuilt.get("body", {}).get("counts"),
                      "registered_api_sha256": data.get("registered_api_sha256"),
                      "edge_endpoints_m": rebuilt.get("edge", {}).get("endpoints_m"),
                      "body_vertices_m": rebuilt.get("body", {}).get("vertices_m"),
                      "numeric_checks": len(checks), "numeric_passed": sum(row["passed"] for row in checks)}


def launch(job_path, job_pin, run_dir, role, candidate_pin):
    location = run_dir / role
    location.mkdir(exist_ok=False)
    command = (sys.executable, "-E", "-B", str(Path(__file__).resolve()), "--job", str(job_path),
               "--job-sha256", job_pin, "--phase", role)
    try:
        result = run(command, cwd=Path(__file__).resolve().parent, capture_output=True, timeout=TIMEOUT, check=False)
        stdout, stderr, status, timed_out = result.stdout, result.stderr, result.returncode, False
    except TimeoutExpired as error:
        stdout, stderr, status, timed_out = error.stdout or b"", error.stderr or b"", None, True
    write_new(location / "Stdout.txt", stdout)
    write_new(location / "Stderr.txt", stderr)
    return phase_result(role, location / "Record.json", candidate_pin, status, stderr, timed_out)


def acquire(job_path, pin, job, folder, paths):
    import Swapp

    candidates, saved, run_dir = paths
    require(not Swapp.application_pids() and all(not item.exists() and not item.is_symlink() for item in paths),
            "stock trial requires an idle oracle and fresh disjoint output paths")
    for path in paths:
        path.mkdir(exist_ok=False)
    for name in NAMES:
        basename = f"{name}.SLDPRT"
        raw = pinned(folder / "Stock" / basename, job["construction"][name]["sha256"])
        write_new(candidates / basename, raw)
    phases = {}
    for role in PHASES:
        if Swapp.application_pids():
            break
        if role in NAMES and not phases["ControlBefore"]["passed"]:
            continue
        phases[role] = launch(job_path, pin, run_dir, role, job["construction"].get(role, {}).get("sha256"))
    processes = [tuple(row["process"]) for row in phases.values() if row["process"]]
    idle = not Swapp.application_pids()
    controls = all(phases.get(role, {}).get("passed") and phases[role]["control_sha256"] == CONTROL
                   for role in ("ControlBefore", "ControlAfter"))
    unchanged = {name: sha((candidates / f"{name}.SLDPRT").read_bytes()) == job["construction"][name]["sha256"]
                 if (candidates / f"{name}.SLDPRT").is_file() else False for name in NAMES}
    comparison_valid = controls and len(processes) == len(set(processes)) == len(PHASES) and idle
    passed = comparison_valid and all(phases[name]["passed"] and unchanged[name] for name in NAMES)
    result = {"schema": SCHEMA, "stock_job_sha256": pin, "oracle": ORACLE_AUTHORITY,
              "phases": phases, "distinct_native_processes": len(set(processes)), "oracle_idle_after": idle,
              "candidate_unchanged_after_bracket": unchanged, "comparison_valid": comparison_valid,
              "passed": passed, "fillet_writer_output_count": 0, "heldout_sources_read": 0}
    raw = job_bytes(result)
    write_new(run_dir / "Result.json", raw)
    print(dumps({"result_sha256": sha(raw), "passed": passed, "comparison_valid": comparison_valid}, sort_keys=True))
    return passed


def main():
    parser = ArgumentParser()
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--job-sha256", required=True)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--verify-packet", action="store_true")
    modes.add_argument("--phase", choices=PHASES)
    args = parser.parse_args()
    job, folder, root, cases = load_job(args.job, args.job_sha256)
    if args.verify_packet:
        if os.name == "nt":
            windows_paths(folder, root)
        print(dumps({"stock_job_sha256": args.job_sha256, "files_verified": len(job["files"]),
                     "native_processes": 0}, sort_keys=True))
        return 0
    paths = windows_paths(folder, root)
    if args.phase:
        return 0 if worker(job, folder, root, cases, paths, args.phase) else 1
    return 0 if acquire(args.job.absolute(), args.job_sha256, job, folder, paths) else 1


if __name__ == "__main__":
    raise SystemExit(main())
