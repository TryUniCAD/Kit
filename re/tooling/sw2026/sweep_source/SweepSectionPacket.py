import argparse
from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
import json
import os
from pathlib import Path, PureWindowsPath
import re
import subprocess
import sys


tool_directory = Path(__file__).resolve().parent
sys.path.insert(0, str(tool_directory))
if tool_directory.name == "sweep_source":
    tooling = tool_directory.parent
    sys.path.extend(str(tooling / name) for name in ("", "imported_body_source", "edge_fillet_source"))

from AuthorRectangleAnchors import CONTROL, ORACLE, control
from AuthorCurves import digest, require, write_json
from ObserveCylinderExchange import checked, unique_object
from ObserveKernelExchange import phase as exchange_phase
from RunImportedBodySources import VERSION, oracle_identity
from SweepSectionOracle import export_phase, measure_disk


SCHEMA = "kit.sw2026.disclosed-sweep-section-exchange.v1"
EVIDENCE_PATH = "re/solidworks/measurements/2026/OrdinarySweepSectionTransport01.json"
EVIDENCE_SHA256 = "052d2ffb1d01e68a68a17169e7834b899d219a4cffa14394f5662f0cd25e6f0e"
CASES = {
    "Section3773": (0.003773, "7a9e5e0b6e30805dacc82e2443eebe00100e0b05d6dcbca578ba126bbfe06637"),
    "Section5159": (0.005159, "2f3666f352e66181c5a2d7b1aa5fd522268499fe41624cb15b58fe85209fc31a"),
}
TOOL_PATHS = {
    "": ("AuthorCurves.py", "AuthorRectangleAnchors.py", "InspectFresh.py", "OracleIdentity.py", "Swapp.py"),
    "edge_fillet_source/": ("FilletApi.py", "FilletModel.py"),
    "imported_body_source/": ("AuthorImportedBody.py", "ObserveCylinderExchange.py", "ObserveKernelBodyRestore.py",
                             "ObserveKernelExchange.py", "RunImportedBodySources.py"),
    "sweep_source/": ("SweepSectionOracle.py", "SweepSectionPacket.py"),
}
FILES = {f"Tool/{name}" for names in TOOL_PATHS.values() for name in names} | {
    "Control.SLDPRT", *(name + ".x_b" for name in CASES),
}
JOB = "Job.json"
CONTROL_ROLES = ("ApplicationBefore", "AuthorBefore", "ImportBefore", "AuthorAfter", "ImportAfter", "ApplicationAfter")
PHASES = (*CONTROL_ROLES[:3], *CASES, *CONTROL_ROLES[3:])


def guest_location(value):
    location = PureWindowsPath(value)
    require(location.is_absolute() and location.drive == "C:" and len(location.parts) == 3
            and location.name == "Packet" and re.fullmatch(r"KitSweepSectionExchange[0-9]{2}", location.parent.name),
            "use a new guest-local C:\\KitSweepSectionExchangeNN\\Packet")
    return str(location)


def as_json(data):
    return (json.dumps(data, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def read_job(path, pin):
    require(path.name == JOB and path.is_file() and not path.is_symlink(), "expected a regular sheet job")
    job = json.loads(checked(path, pin), object_pairs_hook=unique_object)
    require(job["schema"] == SCHEMA and (job["oracle_version"], job["oracle_sha256"]) == (VERSION, ORACLE)
            and job["section_receipt_sha256"] == EVIDENCE_SHA256
            and re.fullmatch(r"[0-9a-f]{40}", job["revision"]) and re.fullmatch(r"[0-9a-f]{40}", job["tree"]),
            "unbound sheet oracle job")
    guest_location(job["guest_packet"])
    root = path.parent
    seen = {file.relative_to(root).as_posix() for file in root.rglob("*") if file.is_file()}
    require(set(job["files"]) == FILES and seen == FILES | {JOB}, "sheet packet file closure differs")
    require(job["files"]["Control.SLDPRT"]["sha256"] == CONTROL, "stock application control differs")
    for name, (_, sha) in CASES.items():
        require(job["files"][name + ".x_b"] == {"sha256": sha, "bytes": 873}, "generated bare disk differs")
    blobs = {}
    for name, info in job["files"].items():
        file = root / name
        require(file.resolve() == file, f"packet member redirected: {name}")
        blobs[name] = checked(file, info["sha256"], info["bytes"])
    return job, blobs


def create_packet(output, job, blobs):
    require(output.is_absolute() and not output.exists() and set(blobs) == FILES, "use a fresh packet and its exact files")
    output.mkdir(parents=True, exist_ok=False)
    (output / "Tool").mkdir()
    for name, data in blobs.items():
        with (output / name).open("xb") as handle:
            handle.write(data)
    job["files"] = {name: {"sha256": sha256(data).hexdigest(), "bytes": len(data)} for name, data in blobs.items()}
    raw = as_json(job)
    with (output / JOB).open("xb") as handle:
        handle.write(raw)
    pin = sha256(raw).hexdigest()
    read_job(output / JOB, pin)
    return pin


def freeze(args):
    root = Path(__file__).resolve().parents[4]
    require(re.fullmatch(r"[0-9a-f]{40}", args.revision) and args.output.is_absolute()
            and args.output == args.output.resolve() and not args.output.is_relative_to(root),
            "use a full committed revision and fresh external path")

    def git(*options):
        return subprocess.check_output(("git", "-C", str(root), *options))

    require(git("rev-parse", args.revision + "^{commit}").decode().strip() == args.revision
            and sha256(git("show", f"{args.revision}:{EVIDENCE_PATH}")).hexdigest() == EVIDENCE_SHA256,
            "unbound transport source revision")
    blobs = {f"Tool/{name}": git("show", f"{args.revision}:re/tooling/sw2026/{parent}{name}")
             for parent, names in TOOL_PATHS.items() for name in names}
    blobs["Control.SLDPRT"] = checked(args.control, CONTROL)
    for name, (_, sha) in CASES.items():
        blobs[name + ".x_b"] = checked(args.generated / (name + ".x_b"), sha, 873)
    job = {"schema": SCHEMA, "oracle_version": VERSION, "oracle_sha256": ORACLE,
           "section_receipt_sha256": EVIDENCE_SHA256, "revision": args.revision,
           "tree": git("rev-parse", args.revision + "^{tree}").decode().strip(),
           "guest_packet": guest_location(args.guest_packet)}
    return {"job_sha256": create_packet(args.output, job, blobs), "bound_files": len(blobs), "native_processes": 0}


def native_paths(path, job, *, staged):
    require(os.name == "nt" and sys.version_info[:2] == (3, 12), "use Windows CPython 3.12 for guest operations")
    packet = Path(guest_location(job["guest_packet"]))
    capture = packet.parent / "Records"
    require((not staged or (path.parent == packet == packet.resolve() and Path(__file__).resolve().parent == packet / "Tool"))
            and capture.resolve() == capture and not capture.exists(), "use the fresh exact guest packet and result paths")
    return packet, capture


def phase_identity(row):
    identified = oracle_identity(row["oracle_identity"])
    return identified["process_id"], identified["process_creation_filetime"]


def same_disk_across_rebuild(result):
    if result["passed"]:
        keys = ("sheets", "faces", "edges", "vertices")
        if any(result["cold"][key] != result["rebuilt"][key] for key in keys):
            result.update(passed=False, topology_failure="sheet rebuild changed boundary topology")
    return result


def run(path, pin, job, blobs):
    import Swapp

    packet, capture = native_paths(path, job, staged=True)
    capture.mkdir(exist_ok=False)
    rows = {}
    ids = set()
    result = {"schema": SCHEMA, "job_sha256": pin, "oracle_version": VERSION, "oracle_sha256": ORACLE,
              "candidate_hashes": {name: sha for name, (_, sha) in CASES.items()}, "phases": rows,
              "candidate_scope": "bare Parasolid section sheets", "native_sweep_writer_outputs": 0,
              "heldout_count": 0, "passed": False}

    def attempt(role, action, *parameters):
        try:
            rows[role] = action(*parameters)
        except Exception as error:
            rows[role] = {"passed": False, "phase_error": repr(error)}
        row = rows[role]
        if row.get("oracle_identity") or row["passed"]:
            try:
                identity = phase_identity(row)
                require(identity not in ids, "phase used a previously observed SOLIDWORKS process")
                ids.add(identity)
            except Exception as error:
                row.update(passed=False, identity_failure=repr(error))
        return row["passed"]

    def import_disk(role, radius, raw):
        return same_disk_across_rebuild(exchange_phase(capture, role, radius, raw, "exchange", observe_body=measure_disk))

    def native_export(label, radius, *, enabled):
        author, native_import = "Author" + label, "Import" + label
        if enabled and attempt(author, export_phase, capture, author, radius):
            entry = rows[author]["export"]

            def restore():
                raw = checked(capture / (author + "Disk.x_b"), entry["sha256"], entry["bytes"])
                return import_disk(native_import, radius, raw)

            return attempt(native_import, restore)
        return False

    first, second = (radius for radius, _ in CASES.values())
    with ((capture / "Oracle.log").open("x", encoding="utf-8") as log, redirect_stdout(log), redirect_stderr(log)):
        try:
            initial = attempt("ApplicationBefore", control, capture, "ApplicationBefore", packet / "Control.SLDPRT")
            if native_export("Before", first, enabled=initial):
                for name, (radius, _) in CASES.items():
                    attempt(name, import_disk, name, radius, blobs[name + ".x_b"])
        finally:
            native_export("After", second, enabled=True)
            attempt("ApplicationAfter", control, capture, "ApplicationAfter", packet / "Control.SLDPRT")
        try:
            Swapp.sweep()
            _, final = read_job(path, pin)
            require(final == blobs, "packet changed during inspection")
            for label in ("Before", "After"):
                entry = rows.get("Author" + label, {}).get("export")
                if entry:
                    checked(capture / ("Author" + label + "Disk.x_b"), entry["sha256"], entry["bytes"])
            result.update(final_idle=True, inputs_unchanged=True)
        except Exception as error:
            result["final_guard_failure"] = repr(error)
    authors = tuple(rows.get("Author" + role, {}) for role in ("Before", "After"))
    same_authoring = all(authors[0].get(key) is not None and authors[0][key] == authors[1].get(key)
                         for key in ("api", "source_template_sha256"))
    result.update(distinct_processes=len(ids), same_native_authoring=same_authoring,
                  controls_healthy=all(rows.get(name, {}).get("passed") for name in CONTROL_ROLES))
    result["passed"] = bool(result.get("final_idle") and result.get("inputs_unchanged") and result["controls_healthy"]
                            and same_authoring and tuple(rows) == PHASES and len(ids) == len(PHASES)
                            and all(row["passed"] for row in rows.values()))
    write_json(capture / "Result.json", result)
    print(json.dumps({"passed": result["passed"], "result_sha256": digest(capture / "Result.json"),
                      "distinct_processes": len(ids)}))
    return 0 if result["passed"] else 3


def main():
    parser = argparse.ArgumentParser(description="Freeze or verify the two disclosed sweep disk exchange candidates")
    sub = parser.add_subparsers(dest="action", required=True)
    prepare = sub.add_parser("freeze")
    prepare.add_argument("--revision", required=True)
    prepare.add_argument("--generated", required=True, type=Path)
    prepare.add_argument("--control", required=True, type=Path)
    prepare.add_argument("--output", required=True, type=Path)
    prepare.add_argument("--guest-packet", required=True)
    for action in ("verify", "stage-guest", "run"):
        command = sub.add_parser(action)
        command.add_argument("--job", required=True, type=Path)
        command.add_argument("--pin", required=True)
    args = parser.parse_args()
    if args.action == "freeze":
        print(json.dumps(freeze(args)))
        return 0
    require(not args.job.is_symlink(), "sheet job cannot be a symlink")
    path = args.job.resolve(strict=True)
    require(Path(__file__).resolve().parent == path.parent / "Tool", "use the exact packet tool")
    job, blobs = read_job(path, args.pin)
    if args.action == "run":
        return run(path, args.pin, job, blobs)
    if args.action == "stage-guest":
        packet, _ = native_paths(path, job, staged=False)
        require(create_packet(packet, job, blobs) == args.pin, "guest packet transfer changed the job")
    print(json.dumps({"job_sha256": args.pin, "bound_files": len(blobs), "native_processes": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
