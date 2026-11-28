from argparse import ArgumentParser
from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
from itertools import product
import json
from math import isfinite
import os
from pathlib import Path
import re
import sys
from traceback import print_exc


GUEST = r"C:\KitBakedToleranceNative01"
BUILD = "34.5.2.0604"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
CONTROL = "c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57"
CASES = ("Baked01", "Baked02")
PHASES = ["ControlBefore", "Baked01", "Baked01Reopen", "Baked02", "Baked02Reopen", "ControlAfter"]
BASE = "re/tooling/sw2026/"
IMPORTS = BASE + "imported_body_source/"
OBSERVER = Path(__file__).name
TOOLS = {
    **{name: BASE + name for name in
       ("AuthorCurves.py", "AuthorRectangleAnchors.py", "InspectFresh.py", "OracleIdentity.py", "Swapp.py")},
    **{name: IMPORTS + name for name in
       (OBSERVER, "ObserveLocalImportedPart.py", "ObserveKernelBodyRestore.py", "AuthorImportedBody.py", "RunImportedBodySources.py")},
}
JOB_SCHEMA = "kit.sw2026.baked-local-tolerance-native-job.v1"


def require(value, message):
    if not value:
        raise ValueError(message)


def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def artifact(data):
    return {"bytes": len(data), "sha256": sha256(data).hexdigest()}


def checked(path, checksum, size=None):
    require(re.fullmatch("[0-9a-f]{64}", checksum) and path.is_file() and not path.is_symlink()
            and path.resolve(strict=True) == path and 0 < path.stat().st_size <= 64 * 1024**2,
            "unqualified file custody for " + path.name)
    value = path.read_bytes()
    require((size is None or len(value) == size) and artifact(value)["sha256"] == checksum, "file fingerprint differs for " + path.name)
    return value


def verify(path, checksum, *, completed=False, packed_worker=True):
    packet = path.parent
    job = json.loads(checked(path, checksum))
    members = {"Job.json", "Control.SLDPRT", "Candidates", "Tools"}
    require(path.name == "Job.json" and {row.name for row in packet.iterdir()} == members | ({"Native.json", "Saved"} if completed else set())
            and (not packed_worker or Path(__file__).resolve() == packet / "Tools" / OBSERVER)
            and job["schema"] == JOB_SCHEMA and job["guest"] == GUEST and job["oracle_build"] == BUILD
            and job["oracle_sha256"] == ORACLE and job["phases"] == PHASES
            and job["control"]["sha256"] == CONTROL and set(job["cases"]) == set(CASES)
            and set(job["tools"]) == TOOLS.keys() and job["construction_accesses"] == job["heldout_credit"] == 0
            and job["independent_guarded_processes"] == 2 and job["native_processes"] == 0,
            "wrong staged native part or observer inventory")
    checked(packet / "Control.SLDPRT", CONTROL, job["control"]["bytes"])
    require({row.name for row in (packet / "Tools").iterdir()} == TOOLS.keys()
            and {row.name for row in (packet / "Candidates").iterdir()} == {name + ".SLDPRT" for name in CASES},
            "packet contains an alternate candidate or tool")
    for name, row in job["tools"].items():
        checked(packet / "Tools" / name, row["sha256"], row["bytes"])
    for name, row in job["cases"].items():
        part = row["proof"]["part"]
        checked(packet / "Candidates" / (name + ".SLDPRT"), part["sha256"], part["bytes"])
        require(row["proof"]["status"] == "exact" and row["proof"]["oriented_faces"] == 6
                and 0 < row["tolerance_m"] < 1 and type(row["configuration"]) is str
                and type(row["feature"]) is str and all(isfinite(value) for extent in row["bounds_mm"] for value in extent),
                "cold case lacks complete typed source evidence")
    return job


def independent_box(bounds):
    x, y, z = axes = tuple(tuple(value / 1000 for value in extent) for extent in bounds)
    a, b, c = (end - start for start, end in axes)
    require(min(a, b, c) > 0, "independent bounds describe a nonpositive solid")
    midpoints = tuple((lo + hi) / 2 for lo, hi in axes)
    return {"corners_m": tuple(product(x, y, z)), "edges": 12, "faces": 6,
            "com_m": midpoints, "volume_m3": a * b * c,
            "box": {"face_center_m": (*midpoints[:2], z[0]), "size_m": (a, b, c)},
            "area_m2": 2 * (a * b + a * c + b * c)}


def observed_box(observer, body, expected, *, temporary):
    from AuthorImportedBody import SOLID
    from ObserveKernelBodyRestore import measure_body

    raw = measure_body(observer, body, expected, temporary=temporary)
    part = observer.typed(observer.model, "PartDoc")
    (visible,) = observer.get(part, "GetBodies2", SOLID, True) or ()
    observer.exact_object(visible, body, "real body remains the sole visible solid")
    topology, _ = observer.body_topology(body, expected["box"], temporary=temporary)
    return raw | {"visible_solids": 1, "bounds_m": topology["analytic_bounds_m"],
                  "face_edge_incidence": topology["face_edge_incidence"]}


def state(row, case):
    if row is None:
        return None
    same_owner = (row["configuration"] == case["configuration"]
                  and tuple(row["configurations"]) == (case["configuration"],)
                  and row["feature"] == case["feature"] and row["feature_id"] == case["proof"]["feature_id"])
    return {"owners_match": same_owner, "feature_id": row["feature_id"], "shape": row["shape"],
            "tree_sha256": artifact(encode(row["tree_signature"]))["sha256"],
            "tree_rows": len(row["tree_signature"])}


def native(path, checksum, job):
    from AuthorRectangleAnchors import control
    from ObserveLocalImportedPart import phase

    packet, guest = path.parent, Path(GUEST)
    guest.mkdir()
    require(guest.resolve(strict=True) == guest, "guest lease was redirected")
    for name in ("Candidates", "Saved"):
        (guest / name).mkdir()
    seed = guest / "Control.SLDPRT"
    with seed.open("xb") as out:
        out.write(checked(packet / "Control.SLDPRT", CONTROL, job["control"]["bytes"]))
    report = {"schema": "kit.sw2026.baked-local-tolerance-native-result.v1", "job_sha256": checksum,
              "oracle_build": BUILD, "oracle_sha256": ORACLE, "heldout_credit": 0,
              "whole_source_conversions": 0, "phases": {}, "saves": {}}
    rows, lifetimes = report["phases"], []

    def note(role, result, case=None):
        identity = result.get("oracle_identity") or {}
        exact = (identity.get("sha256") == ORACLE and identity.get("file_version") == BUILD
                 and identity.get("version_matches") is True and identity.get("pe_machine") == "0x8664")
        if exact:
            lifetimes.append((identity["process_id"], identity["process_creation_filetime"]))
        row = {"passed": bool(result["passed"] and exact), "record_sha256": result["record_sha256"], "oracle_bound": exact}
        if case is not None:
            row.update(open=result.get("open"), numeric_checks=result["numeric_checks"],
                       cold=state(result.get("cold"), case), rebuilt=state(result.get("rebuilt"), case))
            row["passed"] = bool(row["passed"] and all(row[k] and row[k]["owners_match"] for k in ("cold", "rebuilt")))
        rows[role] = row
        return row

    with (guest / "Observer.log").open("x", encoding="utf-8") as log, redirect_stdout(log), redirect_stderr(log):
        stage = "ControlBefore"
        try:
            before = note(stage, control(guest, stage, seed))
            if before["passed"]:
                for name in CASES:
                    stage = name
                    case = job["cases"][name]
                    expected = independent_box(case["bounds_mm"])
                    part = case["proof"]["part"]
                    filename = name + ".SLDPRT"
                    original = guest / "Candidates" / filename
                    derivative = guest / "Saved" / filename
                    with original.open("xb") as out:
                        out.write(checked(packet / "Candidates" / filename, part["sha256"], part["bytes"]))
                    result = phase(guest, name, original, part["sha256"], expected, case["feature"],
                                   save=derivative, measure_shape=observed_box)
                    row = note(name, result, case)
                    row["source_unchanged"] = bool(checked(original, part["sha256"], part["bytes"]))
                    if "saved_sha256" in result:
                        saved = checked(derivative, result["saved_sha256"])
                        row["save_diagnostics"] = result["save"]
                        row["saved"] = report["saves"][name] = artifact(saved)
                    if row["passed"] and "saved" in row:
                        stage = name + "Reopen"
                        readback = phase(guest, stage, derivative, row["saved"]["sha256"], expected, case["feature"],
                                         reference=result["rebuilt"]["persistent_reference"], measure_shape=observed_box)
                        reopened = note(stage, readback, case)
                        reopened["fresh_readonly"] = readback.get("read_only") is True
                        reopened["passed"] &= reopened["fresh_readonly"]
        except Exception:
            report["failure_stage"] = stage
            print_exc()
        try:
            note("ControlAfter", control(guest, "ControlAfter", seed))
            checked(seed, CONTROL, job["control"]["bytes"])
            verify(path, checksum)
        except Exception:
            report.setdefault("failure_stage", "ControlAfter")
            print_exc()

    report["distinct_native_processes"] = len(set(lifetimes))
    report["controls_healthy"] = all(rows.get(role, {}).get("passed") is True for role in ("ControlBefore", "ControlAfter"))
    report["passed"] = ("failure_stage" not in report and list(rows) == PHASES and all(row["passed"] for row in rows.values())
                        and len(set(lifetimes)) == len(PHASES) and sorted({row[1] for row in lifetimes}) == [row[1] for row in lifetimes])
    saved_directory = packet / "Saved"
    saved_directory.mkdir()
    for name, saved in report["saves"].items():
        file = name + ".SLDPRT"
        with (saved_directory / file).open("xb") as out:
            out.write(checked(guest / "Saved" / file, saved["sha256"], saved["bytes"]))
    data = encode(report)
    with (packet / "Native.json").open("xb") as out:
        out.write(data)
    print(encode({"native_sha256": artifact(data)["sha256"], "passed": report["passed"],
                  "controls_healthy": report["controls_healthy"], "fresh_processes": report["distinct_native_processes"],
                  "published_disclosed_saves": len(report["saves"])}).decode(), end="")
    return 0 if report["passed"] else 3


def main():
    parser = ArgumentParser()
    parser.add_argument("job", type=Path)
    parser.add_argument("--job-sha256", required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    path = args.job.resolve(strict=True)
    job = verify(path, args.job_sha256)
    if args.verify_only:
        print(encode({"verified": True, "job_sha256": args.job_sha256, "native_processes": 0}).decode(), end="")
        return 0
    require(os.name == "nt" and sys.version_info[:2] == (3, 12) and sys.flags.ignore_environment
            and not sys.flags.isolated and sys.dont_write_bytecode,
            "native phase belongs to the Windows 3.12 current-user oracle with -E -B")
    return native(path, args.job_sha256, job)


if __name__ == "__main__":
    sys.exit(main())
