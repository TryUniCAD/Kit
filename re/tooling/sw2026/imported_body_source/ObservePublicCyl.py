from argparse import ArgumentParser
from contextlib import redirect_stdout
from hashlib import sha256
from io import StringIO
import json
import os
from pathlib import Path
import re
from runpy import run_path
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory


HERE = Path(__file__).resolve()
REPO = HERE.parents[4]
RESEARCH = "re/tooling/sw2026"
IMPORT = "imported_body_source"
TOOL = f"{IMPORT}/{HERE.name}"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
CONTROL = "c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57"
GUEST = r"C:\KitPublicPeriodic01"
NAME = "ObliqueCylinder.SLDPRT"
SCHEMA = "kit.sw2026.periodic-cylinder-public-native.v1"
OBLIQUE = {
    "face_center_m": [-0.007125, 0.013375, 0.024625],
    "axis": [2 / 3, -1 / 3, 2 / 3],
    "radius_m": 0.0059375,
    "height_m": 0.0325,
}
SUPPORT = (
    "AuthorCurves.py",
    "AuthorRectangleAnchors.py",
    "InspectFresh.py",
    "OracleIdentity.py",
    "Swapp.py",
)
OBSERVERS = (
    "AuthorImportedBody.py",
    "ObserveCylinderExchange.py",
    "ObserveKernelBodyRestore.py",
    "ObserveKernelExchange.py",
    "ObserveLocalCylinderPart.py",
    "ObserveLocalImportedPart.py",
    "RunImportedBodySources.py",
)
BUILD_TOOLS = (
    "SealedCylinderModel.py",
    "SealedCylinderPacket.py",
    "VerifyBareImportPackage.py",
    "VerifyPublicCyl.py",
)
TEST_SUPPORT = (
    "tests/__init__.py",
    "tests/Convert/__init__.py",
    "tests/Convert/Solidworks/__init__.py",
    "tests/Convert/Solidworks/Research/ConstructionGuard.py",
)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(data):
    return sha256(data).hexdigest()


def file_bytes(path, expected):
    require(path.is_file() and not path.is_symlink(), f"invalid frozen file: {path.name}")
    data = path.read_bytes()
    require(digest(data) == expected, f"frozen file hash differs: {path.name}")
    return data


def publish(path, data):
    payload = data if isinstance(data, bytes) else (
        json.dumps(data, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")
    with path.open("xb") as stream:
        stream.write(payload)
    return digest(payload)


def tracked_extract(revision, folder, archive):
    for tree, prefix, paths in (
        (revision, "", ("src", *TEST_SUPPORT)),
        (
            f"{revision}:{RESEARCH}", f"{RESEARCH}/",
            (*SUPPORT, "serial", TOOL, *(f"{IMPORT}/{name}" for name in (*BUILD_TOOLS, *OBSERVERS))),
        ),
        (
            f"{revision}:re/solidworks/measurements/2026", "re/solidworks/measurements/2026/",
            ("GeneratedLocalCylinderPartNative01.json",),
        ),
    ):
        subprocess.run(
            ("git", "archive", "--format=tar", "--output", str(archive),
             "--prefix", prefix, tree, *paths),
            cwd=REPO,
            check=True,
        )
        with tarfile.open(archive) as bundle:
            bundle.extractall(folder, filter="data")


def freeze(destination, revision, control):
    require(
        re.fullmatch(r"[0-9a-f]{40}", revision)
        and not destination.exists()
        and not destination.resolve().is_relative_to(REPO),
        "use an unused external packet and a full Git revision",
    )
    seed = file_bytes(control, CONTROL)
    destination.mkdir()
    code = destination / "Kit"
    code.mkdir()
    with TemporaryDirectory(prefix="kit-periodic-native-lock-") as scratch:
        tracked_extract(revision, code, Path(scratch) / "Files.tar")
    require(
        (code / RESEARCH / TOOL).read_bytes() == HERE.read_bytes(),
        "the packet method differs from the tracked revision",
    )
    publish(destination / "Control.SLDPRT", seed)
    inventory = {
        path.relative_to(code).as_posix(): digest(path.read_bytes())
        for path in sorted(code.rglob("*"))
        if path.is_file()
    }
    require(len(inventory) > 5000, "the committed SDK closure is incomplete")
    job = {
        "schema": SCHEMA,
        "revision": revision,
        "oracle_version": "34.5.2.0604",
        "oracle_sha256": ORACLE,
        "guest": GUEST,
        "configuration": "Inspection",
        "authored_boundary_si": OBLIQUE,
        "file_inventory": inventory,
        "control_sha256": CONTROL,
    }
    identity = publish(destination / "Job.json", job)
    return {"job_sha256": identity, "code_files": len(inventory), "revision": revision}


def verify_job(job_path, checksum):
    job = json.loads(file_bytes(job_path, checksum))
    packet = job_path.parent.resolve()
    code = packet / "Kit"
    require(
        job_path.name == "Job.json"
        and job["schema"] == SCHEMA
        and job["guest"] == GUEST
        and job["oracle_version"] == "34.5.2.0604"
        and job["oracle_sha256"] == ORACLE
        and re.fullmatch(r"[0-9a-f]{40}", job["revision"])
        and job["configuration"] == "Inspection"
        and job["authored_boundary_si"] == OBLIQUE
        and job["control_sha256"] == CONTROL
        and HERE == (code / RESEARCH / TOOL).resolve(),
        "the frozen public cylinder profile differs",
    )
    require(len(job["file_inventory"]) > 5000, "the committed SDK closure is incomplete")
    for relative, identity in job["file_inventory"].items():
        path = code / relative
        require(path.resolve().is_relative_to(code), "a code path escaped its lock")
        file_bytes(path, identity)
    file_bytes(packet / "Control.SLDPRT", CONTROL)
    sys.path[:0] = [str(code / relative) for relative in (
        f"{RESEARCH}/{IMPORT}", RESEARCH, f"{RESEARCH}/serial", "src", "",
    )]
    return packet, code, job


def build(packet, code, checksum, verify_only):
    destination = Path(GUEST) / "Candidate" / NAME
    require(os.name == "nt" and not destination.parents[1].exists(),
            "use an untouched guest-local SDK destination")
    require(not (packet / "Build.json").exists(), "the locked build receipt already exists")
    if verify_only:
        return {"job_sha256": checksum, "verified": True, "native_processes": 0}
    output = StringIO()
    worker = code / RESEARCH / IMPORT / "VerifyPublicCyl.py"
    sys.argv = [str(worker), "--windows-output", str(destination)]
    with redirect_stdout(output):
        run_path(str(worker), run_name="__main__")
    proof = json.loads(output.getvalue())
    require(
        proof["schema"] == "kit.sw2026.public-periodic-cylinder-windows.v1"
        and proof["construction_runtime_input_reads"] == proof["native_processes_started"] == 0
        and proof["windows_disclosed"]["native_caps"] == ["brep", "configurations"]
        and proof["windows_disclosed"]["part"]["bytes"] == destination.stat().st_size
        and proof["windows_disclosed"]["part"]["sha256"] == digest(destination.read_bytes()),
        "the guarded SDK publication did not bind the file at its actual path",
    )
    lock = {"job_sha256": checksum, "destination": str(destination), "result": proof}
    return {"build_sha256": publish(packet / "Build.json", lock),
            "job_sha256": checksum, "candidate": proof["windows_disclosed"]["part"]}


def measure(packet, job, checksum, build_hash):
    require(os.name == "nt", "native execution belongs to the Windows guest")
    from AuthorRectangleAnchors import control
    from ObserveLocalCylinderPart import periodic_shape
    from ObserveLocalImportedPart import phase

    lock = json.loads(file_bytes(packet / "Build.json", build_hash))
    directory = Path(GUEST)
    candidate = directory / "Candidate" / NAME
    require(lock["job_sha256"] == checksum and Path(lock["destination"]) == candidate,
            "the published candidate belongs to a different job")
    identity = lock["result"]["windows_disclosed"]["part"]["sha256"]
    file_bytes(candidate, identity)
    result_path = packet / "Result.json"
    require(not result_path.exists(), "the locked native receipt already exists")
    seed = directory / "Control.SLDPRT"
    publish(seed, file_bytes(packet / seed.name, CONTROL))
    saves = directory / "NativeSave"
    saves.mkdir()
    saved = saves / NAME
    expected = {"faces": 3, "model": job["authored_boundary_si"]}
    before = control(directory, "ControlBefore", seed)
    require(before["passed"], "the preflight native control did not pass")
    opened = phase(directory, "Candidate", candidate, identity, expected, "Imported geometry",
                   save=saved, measure_shape=periodic_shape)
    reopened = None
    if opened["passed"]:
        reopened = phase(
            directory, "FreshReopen", saved, opened["saved_sha256"], expected, "Imported geometry",
            reference=opened["cold"]["persistent_reference"], measure_shape=periodic_shape,
        )
    after = control(directory, "ControlAfter", seed)
    rows = [row for row in (before, opened, reopened, after) if row is not None]
    process_ids = {
        (item["oracle_identity"]["process_id"], item["oracle_identity"]["process_creation_filetime"])
        for item in rows if item.get("oracle_identity")
    }
    geometry = [snapshot for row in (opened, reopened) if row and row["passed"]
                for snapshot in (row["cold"], row["rebuilt"])]
    owners = [
        (row["feature_id"], row["persistent_reference"], row["tree_signature"])
        for row in geometry
    ]
    passed = (
        len(rows) == len(process_ids) == len(geometry) == 4
        and all(row["passed"] for row in rows)
        and all(row["oracle_identity"]["sha256"] == ORACLE for row in rows)
        and all(row["configuration"] == "Inspection" and row["configurations"] == ("Inspection",)
                and row["feature_id"] == 18 and row["application_state"]["needs_rebuild"] == 0
                for row in geometry)
        and all(owner == owners[0] for owner in owners)
        and reopened["read_only"] and not opened["read_only"]
        and tuple(opened["save"]) == (True, 0, 0)
    )
    file_bytes(candidate, identity)
    result = {
        "schema": SCHEMA, "passed": passed, "writer_revision": job["revision"],
        "oracle_version": job["oracle_version"], "oracle_sha256": ORACLE,
        "job_sha256": checksum, "build_sha256": build_hash,
        "candidate": lock["result"]["windows_disclosed"], "authored_boundary_si": OBLIQUE,
        "controls_healthy": before["passed"] and after["passed"],
        "distinct_native_processes": len(process_ids),
        "candidate_numeric_checks": sum(row["numeric_checks"] for row in (opened, reopened) if row),
        "phases": dict(zip(("control_before", "candidate", "fresh_reopen", "control_after"),
                           (before, opened, reopened, after), strict=True)),
        "heldout_cases": 0, "original_fcstd_conversions": 0,
    }
    return {"result_sha256": publish(result_path, result), "passed": passed,
            "candidate_numeric_checks": result["candidate_numeric_checks"],
            "controls_healthy": result["controls_healthy"]}


def main():
    parser = ArgumentParser(description="Verify an ordinary staged periodic cylinder in Windows")
    commands = parser.add_subparsers(dest="mode", required=True)
    stage = commands.add_parser("freeze")
    stage.add_argument("destination", type=Path)
    stage.add_argument("revision")
    stage.add_argument("control", type=Path)
    for mode in ("verify", "build", "measure"):
        argument = commands.add_parser(mode)
        argument.add_argument("job", type=Path)
        argument.add_argument("job_sha256")
        if mode == "measure":
            argument.add_argument("build_sha256")
    args = parser.parse_args()
    if args.mode == "freeze":
        result = freeze(args.destination, args.revision, args.control)
    else:
        packet, code, job = verify_job(args.job, args.job_sha256)
        if args.mode == "measure":
            result = measure(packet, job, args.job_sha256, args.build_sha256)
        else:
            result = build(packet, code, args.job_sha256, args.mode == "verify")
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("passed", True) else 3


if __name__ == "__main__":
    raise SystemExit(main())
