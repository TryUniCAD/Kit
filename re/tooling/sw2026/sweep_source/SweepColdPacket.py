from argparse import ArgumentParser
import json
import os
from pathlib import Path, PureWindowsPath
from subprocess import check_output, run
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from SweepModel import PHASES, predictions, require, validate_spec
from SweepPacket import BUILD, CONTROL, ORACLE, TOOL_FILES, TOOLS, digest, job_bytes, predictions_match
from SweepPacket import valid_hash, windows_paths, write_new


SCHEMA = "kit.sw2026.standard-sweep-cold-discovery.v1"
PRIVATE_SCHEMA = "kit.sw2026.standard-sweep-cold-heldout.v1"
PREWRITER = "9a98691d85fbbdbbaea74f34c14e71b893ac63f1"
LOCK = "8f8f12a4aa98efd7d50ea9d199898a140e1a0f7d4695c2ae53571c68e20b1fab"
SOURCE_LOCK = "563aef5da24478ab83b881092561dd09066ad9b8e3999ca1da106e00e22420ca"
SEALED_LOCK = "ccc0897416c0f5a9165e49f160274bef9000155b7c8dc3c85e2f2ae77cb4452b"
API = "07909437b4c7068ec0ddbb0025d6f6990d6c4bb65767bc778cddfc3577cfdffe"
SPEC = "e62d1d09ac26cc0ae9538a846b0800023441403b5d04ac432a8f6b1da8e71023"
ADDED_TOOLS = ("SweepColdPacket.py", "RunSweepCold.py", "SweepColdPhase.py", "SweepColdCompare.py")
CANDIDATES = tuple(f"Candidates/{name}.SLDPRT" for name in ("SweepArcNear", "SweepArcWide"))
SEALED_CANDIDATES = tuple(f"Candidates/{name}.SLDPRT" for name in ("Slot01", "Slot02"))
COMMON_FILES = TOOL_FILES | {f"Tool/{name}" for name in ADDED_TOOLS} | {
    "Control.SLDPRT", "Spec.json", "Predictions.json", "ExpectedApi.json",
}
FILES = COMMON_FILES | {"DisclosedComparison.json", *CANDIDATES}
PRIVATE_FILES = COMMON_FILES | {"ProtectedComparison.json", *SEALED_CANDIDATES}


def verify(manifest, pin, *, permit_private=False):
    require(valid_hash(pin) and manifest.name == "SweepJob.json" and manifest.is_file() and not manifest.is_symlink()
            and digest(manifest) == pin, "cold sweep packet is not hash bound")
    job = json.loads(manifest.read_bytes())
    private = job["cohort"] == "heldout"
    if private:
        require(permit_private and os.name == "nt" and sys.version_info[:2] == (3, 12)
                and manifest.parent.resolve() == Path(job["guest_packet"]).resolve()
                and manifest.parent.resolve().drive.casefold() == "c:"
                and all(valid_hash(job[key]) for key in ("method_sha256", "generation_sha256", "spec_sha256")),
                "protected cold sweep packet is confined to its fresh local Windows location")
    require((job["schema"], job["cohort"]) == ((PRIVATE_SCHEMA, "heldout") if private else (SCHEMA, "disclosed"))
            and job["writer_outputs"] == 2 and job["oracle_build"] == BUILD and job["oracle_sha256"] == ORACLE
            and job["source_lock_sha256"] == (SEALED_LOCK if private else SOURCE_LOCK) and job["prewriter_lock_sha256"] == LOCK
            and job["registered_api_sha256"] == API and valid_hash(job["writer_revision"], 40)
            and valid_hash(job["sdk_tree"], 40), "wrong scoped cold-sweep custody")
    windows_paths(job["guest_packet"], job["guest_capture"], job["guest_checkout"])
    parent = manifest.parent.resolve()
    files = PRIVATE_FILES if private else FILES
    candidates = SEALED_CANDIDATES if private else CANDIDATES
    require(set(job["files"]) == files and set(job["candidates"]) == set(candidates)
            and {item.relative_to(parent).as_posix() for item in parent.rglob("*") if item.is_file()}
            == files | {manifest.name}, "cold sweep packet contains an unbound file")
    fixed = {"Control.SLDPRT": CONTROL, "Spec.json": job["spec_sha256"] if private else SPEC, "ExpectedApi.json": API}
    for relative, info in job["files"].items():
        item = parent / relative
        require(item.is_file() and not item.is_symlink() and item.resolve() == item
                and item.stat().st_size == info["bytes"] and digest(item) == info["sha256"]
                and info["sha256"] == fixed.get(relative, info["sha256"]), f"cold sweep member differs: {relative}")
    for relative, locator in job["candidates"].items():
        require(PureWindowsPath(locator) == PureWindowsPath(job["guest_packet"], relative),
                "candidate self locator differs from its immutable staged path")
    spec = json.loads((parent / "Spec.json").read_bytes())
    validate_spec(spec)
    expected = json.loads((parent / "Predictions.json").read_bytes())
    require(spec["cohort"] == job["cohort"] and predictions_match(expected, predictions(spec)),
            "cold sweep geometric predictions differ")
    return job, spec, expected


def create(output, job, data):
    private = job["cohort"] == "heldout"
    require(output.is_absolute() and not output.exists() and set(data) == (PRIVATE_FILES if private else FILES),
            "expected an unused absolute packet root")
    output.mkdir(parents=True, exist_ok=False)
    for relative, raw in sorted(data.items()):
        item = output / relative
        item.parent.mkdir(parents=True, exist_ok=True)
        with item.open("xb") as stream:
            stream.write(raw)
    job = job | {"files": {name: {"bytes": len(raw), "sha256": digest(output / name)} for name, raw in data.items()}}
    manifest = output / "SweepJob.json"
    write_new(manifest, job)
    pin = digest(manifest)
    verify(manifest, pin, permit_private=private)
    return pin


def local_roots(manifest, job):
    require(os.name == "nt" and sys.version_info[:2] == (3, 12), "native sweep requires root-owned Windows CPython 3.12")
    source, capture, checkout = (Path(job[key]).resolve() for key in ("guest_packet", "guest_capture", "guest_checkout"))
    windows_paths(str(source), str(capture), str(checkout))
    require(manifest.parent.resolve() == source and Path(__file__).resolve().parent == source / "Tool",
            "native sweep must run from the immutable local guest packet")
    return source, capture


def stage(manifest, pin):
    require(os.name == "nt" and sys.version_info[:2] == (3, 12), "guest staging requires Windows CPython 3.12")
    job, _, _ = verify(manifest, pin)
    dest, capture = (Path(job[key]).resolve() for key in ("guest_packet", "guest_capture"))
    require(not dest.exists() and not capture.exists(), "cold sweep guest paths already exist")
    data = {name: (manifest.parent / name).read_bytes() for name in FILES}
    require(create(dest, job, data) == pin, "staged cold sweep identity differs")
    return {"job_sha256": pin, "files": len(data), "native_processes": 0}


def frozen_comparison(folder):
    from AuditSweepArchive import checked, load_disclosed
    from SweepColdCompare import projection

    _, source, _ = load_disclosed(folder)
    cases = []
    for item in source["sources"]:
        row = {"original": None, "section": None, "path": None}
        evidence = {}
        for phase in item["phases"]:
            ordinal, name, sha = phase["slot"], phase["phase"], phase["receipt_sha256"]
            require(name in PHASES and phase["passed"], "unexpected independent phase")
            if name in ("section-edit", "path-edit"):
                continue
            record = json.loads(checked(folder / f"Slot{ordinal + 1:02d}-{name}.json", sha))
            require(record["passed"] and record["source_immutable"], "native comparison phase failed")
            role = "original" if name == "author" else name.split("-")[0]
            evidence[role] = sha
            row[role] = projection(record["authored" if role == "original" else "reopened"])
        require(all(row.values()) and all(valid_hash(value) for value in item["artifact_sha256"].values()),
                "incomplete independent native comparison")
        cases.append({"slot": item["slot"], "native_source_sha256": item["artifact_sha256"],
                      "source_receipt_sha256": evidence, "states": row})
    return job_bytes({"source_lock_sha256": SOURCE_LOCK, "cases": cases})


def freeze(args):
    root = HERE.parents[3]
    def git(*arguments):
        return check_output(("git", "-C", str(root), *arguments))
    revision = git("rev-parse", "HEAD").decode().strip()
    require(not args.output.resolve().is_relative_to(root)
            and not git("diff", "--name-only", revision, "--", "src", "re/tooling/sw2026")
            and run(("git", "-C", str(root), "merge-base", "--is-ancestor", PREWRITER, revision),
                    check=False).returncode == 0, "freeze the exact clean writer descended from the prewriter lock")
    require(digest(args.control) == CONTROL, "frozen disclosure control differs")
    packet, capture, checkout = windows_paths(args.guest_packet, args.guest_capture, args.guest_checkout)
    spec = git("show", f"{revision}:re/tooling/sw2026/sweep_source/DisclosedSweepInputs.json")
    data = {f"Tool/{name}": git("show", f"{revision}:{parent}/{name}")
            for parent, names in TOOLS.items() for name in names}
    data.update({f"Tool/{name}": git("show", f"{revision}:re/tooling/sw2026/sweep_source/{name}") for name in ADDED_TOOLS})
    locators = {relative: str(PureWindowsPath(packet, relative)) for relative in CANDIDATES}
    for relative, locator in locators.items():
        command = (sys.executable, "-I", "-B", str(HERE / "AuditColdSweep.py"),
                   "--emit", PureWindowsPath(relative).stem, "--locator", locator)
        data[relative] = run(command, check=True, capture_output=True).stdout
    data |= {"Control.SLDPRT": args.control.read_bytes(), "ExpectedApi.json": (args.disclosed / "RegisteredApi.json").read_bytes(),
             "Spec.json": spec, "Predictions.json": job_bytes(predictions(json.loads(spec))),
             "DisclosedComparison.json": frozen_comparison(args.disclosed)}
    job = {"schema": SCHEMA, "cohort": "disclosed", "writer_revision": revision,
           "sdk_tree": git("rev-parse", f"{revision}:src").decode().strip(),
           "oracle_build": BUILD, "oracle_sha256": ORACLE, "registered_api_sha256": API,
           "source_lock_sha256": SOURCE_LOCK, "prewriter_lock_sha256": LOCK, "writer_outputs": len(CANDIDATES),
           "guest_packet": packet, "guest_capture": capture, "guest_checkout": checkout, "candidates": locators}
    pin = create(args.output, job, data)
    return {"job_sha256": pin, "bound_files": len(data), "native_processes": 0, "writer_revision": revision}


if __name__ == "__main__":
    parser = ArgumentParser(description="Freeze only the disclosed model-only sweep packet")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--disclosed", type=Path, required=True)
    parser.add_argument("--guest-packet", required=True)
    parser.add_argument("--guest-capture", required=True)
    parser.add_argument("--guest-checkout", required=True)
    print(json.dumps(freeze(parser.parse_args()), sort_keys=True))
