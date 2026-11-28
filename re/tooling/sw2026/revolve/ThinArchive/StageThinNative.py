from argparse import ArgumentParser
from pathlib import Path, PureWindowsPath
from subprocess import check_output
import json

from AuditThinArchive import SOURCE_LOCK, checked_bytes, load_lock, phase
from AuditRevEndOwners import digest, require
from BuildThinControls import HERE, LOCK_SHA256, PREWRITER_LOCK, ROOT, encode
from AuthorRevolveFamilies import ORACLE, TOOLS
from RunThinNative import SCHEMA


def stage(args):
    target = args.output.resolve()
    guest = args.guest_root
    require(not target.exists() and not target.is_relative_to(ROOT) and guest.is_absolute()
            and guest.drive.casefold() == "c:", "use a fresh external packet and an absolute guest C drive root")
    lock, cases = load_lock(args.capture)
    control = checked_bytes(args.control, lock["control_sha256"])
    spec = checked_bytes(args.spec, lock["spec_sha256"])
    receipt_raw = (args.generated / "BuildReceipt.json").read_bytes()
    report = json.loads(receipt_raw)
    revision = check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    tree = check_output(["git", "rev-parse", "HEAD:src"], cwd=ROOT, text=True).strip()
    require(report["schema"] == "kit.sw2026.thin-revolve-generated-discovery.v1"
            and report["writer_revision"] == revision and report["writer_sdk_tree"] == tree
            and report["model_spec_sha256"] == lock["spec_sha256"]
            and report["prewriter_lock_revision"] == PREWRITER_LOCK and report["prewriter_lock_sha256"] == LOCK_SHA256
            and PureWindowsPath(report["logical_candidate_directory"]) == guest / "Candidates"
            and not report["public_writer"] and not report["native_acceptance"], "candidate receipt does not match this frozen writer or run")
    for name, sha in report["tools"].items():
        checked_bytes(HERE / name, sha)
    require(tuple(report["rows"]) == tuple(cases), "candidate set differs from disclosed source lock")
    contents = {"ModelSpec.json": spec, "Control.SLDPRT": control, "BuildReceipt.json": receipt_raw,
                "SourceLock.json": checked_bytes(args.capture / "SourceLock.json", SOURCE_LOCK)}
    for name in TOOLS:
        contents["Tools/" + name] = (HERE.parents[1] / name).read_bytes()
    for name in ("CompareThinNative.py", "RunThinNative.py"):
        contents["Tools/" + name] = (HERE / name).read_bytes()
    for case, row in cases.items():
        proof = report["rows"][case]
        require(proof["runtime_external_access_attempts"] == 0 and len(proof["typed_streams"]) == 10
                and all(item["byte_identity"] for item in proof["typed_streams"].values()), "generated candidate has incomplete guards")
        asset = case + ".SLDPRT"
        contents["Candidates/" + asset] = checked_bytes(args.generated / asset, proof["sha256"])
        contents["Sources/" + asset] = checked_bytes(args.capture / case / asset, row["native_sha256"])
        names = {"reopen": case + ".reopen.json", "edited-reopen": case + "-edited.edited-reopen.json"}
        for native_phase in row["phases"]:
            label = native_phase["phase"]
            if label in names:
                phase(args.capture, case, native_phase)
                name = names[label]
                contents["References/" + name] = checked_bytes(args.capture / case / name, native_phase["sha256"])
    job = {"schema": SCHEMA, "logical_root": str(guest), "oracle_sha256": ORACLE,
           "writer_revision": revision, "writer_sdk_tree": tree, "source_lock_sha256": SOURCE_LOCK,
           "files": {path: digest(data) for path, data in sorted(contents.items())}}
    job_raw = encode(job)
    contents["NativeJob.json"] = job_raw
    target.mkdir()
    for name, raw in contents.items():
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(raw)
    print(json.dumps({"packet": str(target), "job_sha256": digest(job_raw), "candidate_count": len(cases),
                      "planned_native_processes": 2 + 4 * len(cases)}))


def main():
    parser = ArgumentParser(description="Freeze the disclosed thin candidates and same-case native comparators")
    for option in ("generated", "capture", "control", "spec", "output"):
        parser.add_argument("--" + option, type=Path, required=True)
    parser.add_argument("--guest-root", type=PureWindowsPath, required=True)
    stage(parser.parse_args())


if __name__ == "__main__":
    main()
