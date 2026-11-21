from __future__ import annotations

from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
from subprocess import check_output
import sys
from tarfile import TarInfo, open as open_tar
import time


SCHEMA = "kit.sw2026.ordinary-revolve-end-heldout-evaluation.v1"
TOOLS = "re/tooling/sw2026/"
THIS = TOOLS + "revolve/EndModes/EvaluateHeldoutRevolveEnds.py"
LOCK = "re/solidworks/measurements/2026/RevolveEndHeldoutSourceLock01.json"
LOCK_SHA = "977cfab507c7c77910b752bb8c46e4968a0ddfdf7efc9a8d582d99a2c7b364b9"
DISCLOSED = "re/solidworks/measurements/2026/SdkOrdinaryRevolveEndNative01.json"
LOCK_COMMIT = "01130d8a12516201e2280fe0a11fbe0e303d0ed1"
WRITER = "59cc0c0380132f8bd03ce8b0de815b5d6b3da6e4"
HOST = Path("/Users/odin/Documents/UniCAD/Oracle121Takeover")
SHARE = PureWindowsPath(r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover")
OLD = PureWindowsPath(r"C:\KitSdkCandidates\RevolveEndHeldout01")


def digest(raw):
    return sha256(raw).hexdigest()


def checked(path, pin):
    raw = path.read_bytes()
    if digest(raw) != pin:
        raise ValueError("sealed input changed: " + path.name)
    return raw


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def publish(path, raw):
    with path.open("xb") as file:
        file.write(raw)
    return digest(raw)


def admitted_lock(payload):
    assert digest(payload) == LOCK_SHA
    lock = json.loads(payload)
    assert lock["passed"] and lock["split"] == "heldout" and lock["distinct_processes"] == 14
    assert lock["control-before"]["passed"] and lock["control-after"]["passed"] and lock["idle_after"]
    assert lock["writer_output_count"] == 0 and lock["heldout_writer_acceptance"] is False
    assert len(lock["sources"]) == 4 and all(row["passed"] and not row["reused_authored_phase"] for row in lock["sources"])
    return lock


def freeze(name):
    root = Path(__file__).resolve().parents[5]
    assert name.startswith("RevolveEndEvaluation") and name.removeprefix("RevolveEndEvaluation").isdigit()
    output = HOST / name
    assert not output.exists()

    def git(*arguments):
        return check_output(("git", "-C", str(root), *arguments))

    def object_bytes(revision, filename):
        return git("show", f"{revision}:{filename}")

    method = git("rev-parse", "HEAD").decode().strip()
    git("merge-base", "--is-ancestor", LOCK_COMMIT, WRITER)
    git("merge-base", "--is-ancestor", WRITER, method)
    lock = admitted_lock(object_bytes(method, LOCK))
    observed = json.loads(object_bytes(method, DISCLOSED))
    writer_tree = git("rev-parse", f"{WRITER}:src").decode().strip()
    assert observed["passed"] and observed["application_idle"] and observed["distinct_processes"] == 10
    assert observed["writer_source_tree"] == writer_tree and observed["writer_revision"] == WRITER
    assert lock["finished_at"] < int(git("show", "-s", "--format=%ct", WRITER))
    assert object_bytes(method, THIS) == Path(__file__).read_bytes()
    research_tools = git("ls-tree", "-r", "--name-only", method, TOOLS + "revolve").decode().splitlines()
    names = {LOCK, DISCLOSED, *(path for path in research_tools if path.endswith(".py"))}
    names.update(TOOLS + name for name in (
        "InspectGeneratedRevolveEnds.py", "AuthorRevolveEnds.py", "AuthorRevolveSources.py",
        "AuthorCurves.py", "InspectFresh.py", "OracleIdentity.py", "Swapp.py",
    ))
    exact = {path: object_bytes(method, path) for path in sorted(names)}
    assert exact[TOOLS + "revolve/EndModes/BuildOrdinaryEndRevolves.py"] == object_bytes(
        WRITER, TOOLS + "revolve/EndModes/BuildOrdinaryEndRevolves.py")
    combined = BytesIO()
    old = git("archive", "--format=tar", WRITER, "src")
    with open_tar(fileobj=BytesIO(old), mode="r:") as source, open_tar(fileobj=combined, mode="w:gz") as target:
        for member in source:
            assert member.isfile() or member.isdir()
            target.addfile(member, source.extractfile(member) if member.isfile() else None)
        for path, raw in exact.items():
            info = TarInfo(path)
            info.mode, info.size = 0o644, len(raw)
            target.addfile(info, BytesIO(raw))
    packed = combined.getvalue()
    manifest = {"schema": SCHEMA, "method_revision": method, "writer_revision": WRITER, "writer_source_tree": writer_tree,
                "source_lock_sha256": LOCK_SHA, "disclosed_sha256": digest(exact[DISCLOSED]), "pack_sha256": digest(packed),
                "files": {name: digest(data) for name, data in exact.items()},
                "frozen_at": time.time(), "private": str(OLD.parent / name), "module_sha256": digest(exact[THIS]),
                "guest_packet": str(SHARE / name), "sealed_inputs_read_by_freeze": 0}
    output.mkdir()
    publish(output / Path(THIS).name, exact[THIS])
    publish(output / "Code.tar.gz", packed)
    return {"freeze_sha256": publish(output / "Freeze.json", encode(manifest)), "writer_source_tree": writer_tree}


def open_packet(packet, pin, create):
    raw = checked(packet / "Freeze.json", pin)
    manifest = json.loads(raw)
    assert manifest["schema"] == SCHEMA and manifest["writer_revision"] == WRITER
    assert manifest["module_sha256"] == digest(Path(__file__).read_bytes())
    assert Path(manifest["guest_packet"]).resolve() == packet.resolve()
    private = Path(manifest["private"])
    source = private / "Code"
    archive = checked(packet / "Code.tar.gz", manifest["pack_sha256"])
    with open_tar(fileobj=BytesIO(archive), mode="r:gz") as bundle:
        members = bundle.getmembers()
        names = [member.name for member in members]
        assert len(set(name.casefold() for name in names)) == len(names)
        assert all((member.isfile() or member.isdir()) and not name.startswith("/")
                   and "\\" not in name and ":" not in name and ".." not in PurePosixPath(name).parts
                   and (name == "src" or name.startswith("src/") or name in manifest["files"])
                   for name, member in zip(names, members, strict=True))
        if create:
            source.mkdir(parents=True)
            bundle.extractall(source, members=members, filter="data")
        files = {member.name: member for member in members if member.isfile()}
        assert set(files) == {path.relative_to(source).as_posix() for path in source.rglob("*") if path.is_file()}
        for name, member in files.items():
            path = source / name
            assert not path.is_symlink() and path.read_bytes() == bundle.extractfile(member).read()
    for name, sha in manifest["files"].items():
        checked(source / name, sha)
    lock = admitted_lock(checked(source / LOCK, LOCK_SHA))
    spec_path = Path(SHARE / "RevolveEndHeldout01" / "Tool" / "Spec.json")
    spec = json.loads(checked(spec_path, lock["spec_sha256"]))
    case_rows = {row["name"]: row for row in lock["sources"]}
    assert spec["split"] == "heldout" and len(spec["cases"]) == len(case_rows) == 4
    assert {case["name"] for case in spec["cases"]} == set(case_rows)
    assert all(case["mode"] == case_rows[case["name"]]["mode"] for case in spec["cases"])
    return manifest, private, source, lock, spec["cases"], case_rows


def prepare(packet, pin):
    manifest, root, source, _, cases, _ = open_packet(packet, pin, True)
    sys.path.insert(0, str(source / TOOLS / "revolve/EndModes"))
    from BuildOrdinaryEndRevolves import build_one

    output = root / "Generated"
    output.mkdir()
    requests = [{"case": case, "destination": str(output / (case["name"] + ".SLDPRT")),
                 "epoch": int(manifest["frozen_at"])} for case in cases]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(build_one, requests))
    rows = {}
    for case, (raw, proof) in zip(cases, results, strict=True):
        name = case["name"]
        path = output / (name + ".SLDPRT")
        assert publish(path, raw) == proof["archive_sha256"]
        rows[name] = {"candidate_sha256": proof["archive_sha256"], "path_and_stream_equal": proof["path_and_stream_equal"],
                      "runtime_external_access_attempts": proof["runtime_external_access_attempts"],
                      "exact_streams": len(proof["streams"]), "keyword_order": proof["keyword_dimension_order"]}
    generation = {"schema": SCHEMA, "freeze_sha256": pin, "generated_at": time.time(), "writer_source_tree": manifest["writer_source_tree"],
                  "cases": rows, "original_native_files_read_during_generation": 0}
    return {"generation_sha256": publish(root / "Generation.json", encode(generation)), "generated_cases": len(rows)}


def native(packet, pin, generation_pin):
    manifest, root, source, lock, cases, case_rows = open_packet(packet, pin, False)
    generation = json.loads(checked(root / "Generation.json", generation_pin))
    assert generation["freeze_sha256"] == pin and generation["writer_source_tree"] == manifest["writer_source_tree"]
    assert generation["original_native_files_read_during_generation"] == 0
    sys.path.insert(0, str(source / TOOLS))
    import Swapp
    from AuthorCurves import require, write_json
    from AuthorRevolveEnds import read_constants
    from InspectFresh import healthy, inspect
    from InspectGeneratedRevolveEnds import FullRevolveEndObserver, run_candidate, run_cycle

    FullRevolveEndObserver.constants = read_constants()
    output = root / "Native"
    output.mkdir()
    control = Path(SHARE / "GeneratedOrdinaryRevolveNative01" / "Control" / "RevolveFull.SLDPRT")
    checked(control, lock["control_sha256"])
    oracle = lock["oracle_sha256"]
    identities, records = [], {}
    report = {"schema": SCHEMA, "freeze_sha256": pin, "generation_sha256": generation_pin,
              "writer_revision": WRITER, "writer_source_tree": manifest["writer_source_tree"], "method_revision": manifest["method_revision"],
              "source_lock_sha256": LOCK_SHA, "disclosed_sha256": manifest["disclosed_sha256"], "oracle_sha256": oracle,
              "build": "34.5.2.0604", "original_native_files_read_during_generation": 0, "cases": records}

    def append_processes(phases):
        identities.extend(row["oracle_identity"]["process_creation_filetime"] for row in phases if "oracle_identity" in row)

    def control_check(label):
        result = inspect(control)
        path = output / (label + ".json")
        write_json(path, result)
        append_processes([result])
        report[label] = {"passed": healthy(result) and result["sha256"] == lock["control_sha256"]
                         and result["oracle_identity"]["sha256"] == oracle, "receipt_sha256": digest(path.read_bytes())}

    try:
        control_check("control-before")
        if report["control-before"]["passed"]:
            for case in cases:
                name = case["name"]
                baseline = case_rows[name]
                original = Path(OLD / name / (name + ".SLDPRT"))
                source_digest = baseline["native_sha256"]
                abstract = generation["cases"][name]
                candidate = root / "Generated" / (name + ".SLDPRT")
                row = {"passed": False, "source_sha256": source_digest, **abstract}
                records[name] = row
                try:
                    reference = output / (name + "-source")
                    samples, hashes = run_cycle(case, original, source_digest, reference, oracle, FullRevolveEndObserver)
                    append_processes(samples)
                    row["reference_receipt_sha256"] = hashes
                    require(len(samples) == 2 and all(r["passed"] for r in samples), "sealed original native reference phase failed")
                    files = {"original": str(reference / "Initial.json"), "original_sha256": hashes[0],
                             "edited": str(reference / "FreshReopen.json"), "edited_sha256": hashes[1],
                             "candidate": str(candidate), "candidate_sha256": abstract["candidate_sha256"]}
                    comparison, phases = run_candidate(case, files, output / name, oracle, FullRevolveEndObserver)
                    append_processes(phases)
                    row["candidate_receipt_sha256"] = comparison["native_phase_sha256"]
                    if not comparison["passed"]:
                        row["first_failure"] = comparison.get("first_failure", "candidate lifecycle failed")
                    else:
                        row["comparisons"] = {label: {"tree_rows": pair["tree_rows"], "mass_checks": pair["mass_checks"]}
                                              for label, pair in comparison["comparisons"].items()}
                        row["passed"] = digest(original.read_bytes()) == source_digest
                except Exception as error:
                    row["failure_type"] = type(error).__name__
    finally:
        control_check("control-after")
    report.update(distinct_processes=len(set(identities)), application_idle=not Swapp.application_pids() and not Swapp.owned_process_ids(),
                  controls_unchanged=digest(control.read_bytes()) == lock["control_sha256"])
    report["passed"] = bool(report.get("control-before", {}).get("passed") and report["control-after"]["passed"]
                            and report["controls_unchanged"] and report["application_idle"]
                            and len(identities) == report["distinct_processes"] == 18 and len(records) == 4
                            and all(row["passed"] for row in records.values()))
    report["heldout_writer_cases_qualified"] = len(records) if report["passed"] else 0
    result = publish(packet / "NativeReceipt.json", encode(report))
    return {"passed": report["passed"], "heldout_writer_cases_qualified": report["heldout_writer_cases_qualified"], "receipt_sha256": result}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("action", choices=("freeze", "prepare", "native"))
    parser.add_argument("packet")
    parser.add_argument("--pin")
    parser.add_argument("--generation-pin")
    args = parser.parse_args()
    if args.action == "freeze":
        result = freeze(args.packet)
    elif args.action == "prepare":
        result = prepare(Path(args.packet), args.pin)
    else:
        result = native(Path(args.packet), args.pin, args.generation_pin)
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(int(result.get("passed") is False))
