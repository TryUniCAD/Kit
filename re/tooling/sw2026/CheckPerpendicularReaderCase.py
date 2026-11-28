import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def check_code(root, source_file, freeze_file):
    require(digest(freeze_file.read_bytes()) == "47aa5d22d3a158653f8b3e8bff35c28a9e2dcd8b44286713028504e8217bfa1d",
            "the pre D02 reader freeze changed")
    freeze = json.loads(freeze_file.read_bytes())
    require(digest(source_file.read_bytes()) == freeze["full_source_manifest_sha256"], "the pre D02 full source manifest differs")
    source = json.loads(source_file.read_bytes())
    actual = {path.relative_to(root).as_posix(): digest(path.read_bytes()) for path in sorted((root / "src").rglob("*.py"))}
    require(actual == source["current"], "the reader SDK changed after its pre D02 freeze")
    for name, fingerprint in freeze["tools"].items():
        require(digest(Path(__file__).with_name(name).read_bytes()) == fingerprint, "a frozen rule or audit tool changed before D02")
    return freeze


def custody(packet):
    lock_data = (packet / "Progress/D02/lock/Record.json").read_bytes()
    require(digest(lock_data) == "bf16c18d8224dd2b03ffa9f484d6b7130ef33f3fe12ba21f3f7698f01d08e105", "the disclosed D02 lock record differs")
    lock = json.loads(lock_data)
    require(lock["passed"] and lock["source_locked"] and lock["heldout_source_locked"] is False,
            "the released D02 source lock is not qualified")
    identities, phases = [], []
    for phase in ("before", "author", "reopen-source", "reopen-edited", "after"):
        data = (packet / "Progress/D02" / phase / "Record.json").read_bytes()
        record = json.loads(data)
        require(record["passed"] and record["stage"] == "passed" and record["case_id"] == "D02"
                and record["packet_sha256"] == lock["packet_sha256"] and record["writer_output_count"] == 0,
                "a disclosed D02 native phase did not qualify")
        identity = record["identity"]
        require(identity["file_version"] == "34.5.2.0604" and identity["sha256"] == "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe",
                "the native D02 build identity differs")
        identities.append([identity["process_id"], identity["process_creation_filetime"]])
        phases.append({"phase": phase, "sha256": digest(data)})
    require(len({tuple(item) for item in identities}) == 5, "the source native identities are not independent")
    case = packet / "Disclosed/D02"
    native_data = (case / "SavedAuthor.json").read_bytes()
    require(digest(native_data) == lock["source_manifest_sha256"], "the D02 saved native observation manifest differs")
    for label in ("Source", "Edited"):
        for role, name in (("parent", "PerpendicularTurnedTopRight.SLDASM"), ("child", "PerpendicularDatum.SLDPRT")):
            data = (case / "Native" / label / name).read_bytes()
            expected = lock["native_artifacts"][label.lower()][role]
            require(len(data) == expected["bytes"] and digest(data) == expected["sha256"], "a disclosed D02 native artifact changed")
    return {"lock_sha256": digest(lock_data), "packet_sha256": lock["packet_sha256"],
            "saved_native_observation_sha256": digest(native_data), "phases": phases, "native_creation_identities": identities,
            "files": lock["native_artifacts"]}, json.loads(native_data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "use a fresh disclosed regression output")
    root = args.root.resolve()
    freeze = check_code(root, args.source_manifest, args.freeze)
    source, observed = custody(args.packet)
    sys.path.insert(0, str(root / "src"))
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    args.output.mkdir(parents=True)
    cases, pids = [], []
    for label in ("Source", "Edited"):
        parent = args.packet / "Disclosed/D02/Native" / label / "PerpendicularTurnedTopRight.SLDASM"
        child = parent.with_name("PerpendicularDatum.SLDPRT")
        blob = SldprtArchive.from_bytes(parent.read_bytes()).require("Contents/Config-0-MatesList")
        request = {"path": str(parent), "sha256": digest(parent.read_bytes()), "bytes": parent.stat().st_size,
                   "stream_sha256": digest(blob), "child_path": str(child), "child_sha256": digest(child.read_bytes()),
                   "expected": observed[label.lower()]}
        result = subprocess.run([sys.executable, "-I", "-B", str(Path(__file__).with_name("AuditPerpendicularReader.py")), "--root", str(root)],
                                input=json.dumps(request), text=True, capture_output=True, timeout=90, check=False)
        (args.output / (label + ".stdout.json")).write_text(result.stdout)
        (args.output / (label + ".stderr.txt")).write_text(result.stderr)
        require(result.returncode == 0, "the unchanged frozen D02 reader rejected: " + result.stderr[-1200:])
        value = json.loads(result.stdout)
        require(value["passed"], "the D02 linked or public semantics differ")
        pids.append(value["pid"])
        cases.append({"case": label, "file_sha256": request["sha256"], "child_sha256": request["child_sha256"],
                      "public": value["public"], "typed_owners": value["typed_owners"], "codec": value["codec"]})
    require(len(set(pids)) == 2 and check_code(root, args.source_manifest, args.freeze) == freeze
            and custody(args.packet)[0] == source, "the frozen code or native input changed during D02 evaluation")
    receipt = {"schema": "kit.sw2026.perpendicular-reader-disclosed-D02-regression.v1", "passed": True,
               "task_id": "B04-SW2026-MATES-PERPENDICULAR", "scope": "separate positive disclosed regression after D01 rule freeze",
               "code_freeze_sha256": digest(args.freeze.read_bytes()), "source_manifest_sha256": freeze["full_source_manifest_sha256"],
               "baseline_D01_proof_sha256": freeze["proof_sha256"], "regression_tool_sha256": digest(Path(__file__).read_bytes()),
               "native_source": source, "cases": cases, "local_worker_processes": 2, "local_process_ids": pids,
               "frozen_implementation_unchanged": True, "native_processes_started": 0, "writer_output_count": 0,
               "heldout_inputs_read": False, "native_generated_perpendicular_acceptance": False, "full_family_coverage": False}
    data = (json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    (args.output / "Regression.json").write_bytes(data)
    print(json.dumps({"passed": True, "cases": 2, "regression_sha256": digest(data), "frozen_implementation_unchanged": True}))


if __name__ == "__main__":
    main()
