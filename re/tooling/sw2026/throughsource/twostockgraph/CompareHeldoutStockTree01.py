from difflib import SequenceMatcher
from hashlib import sha256
from pathlib import Path
import json
import os
import sys


ROOT = Path("C:/KitSdkCandidates")
SOURCE = "TwoStockWriterHoldout01"
EVALUATION = "TwoStockWriterEvaluation01"
SOURCE_LOCK = "1c07e988d425da1de7fd53ccdb30f7b18dc6b431236674404bcc1d8f3b21ae2c"
FREEZE = "10660269a55fa4f363ebc5f5d96e3e148a76a7cfdd628f844223a4a631fea8cb"
STAGE = "94a0e10010f7f5f30041eb88787cc149557a2ab959e6371dc62f06299a59e258"
KEYS = ("name", "type", "parent", "error", "warning", "suppressed")


def wire(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def digest(raw):
    return sha256(raw).hexdigest()


def owned(path, expected=None):
    if path.is_symlink() or not path.is_file():
        raise ValueError("missing completed trial record")
    raw = path.read_bytes()
    if expected is not None and digest(raw) != expected:
        raise ValueError("completed trial record changed")
    return json.loads(raw)


def compare(left, right):
    old = [tuple(row[key] for key in KEYS) for row in left]
    new = [tuple(row[key] for key in KEYS) for row in right]
    differences = []
    for operation, a, b, c, d in SequenceMatcher(a=old, b=new, autojunk=False).get_opcodes():
        if operation != "equal":
            differences.append(
                {"operation": operation, "source_start": a, "candidate_start": c,
                 "source_rows": left[a:b], "candidate_rows": right[c:d]}
            )
    return differences


def examine():
    if os.name != "nt":
        raise ValueError("read completed native records inside the Windows guest")
    source_root, trial = ROOT / SOURCE, ROOT / EVALUATION
    lock = owned(source_root / "SourceLock.json", SOURCE_LOCK)
    summary = owned(trial / "Summary.json")
    if (summary["freeze_sha256"], summary["stage_sha256"], summary["source_lock_sha256"]) != (FREEZE, STAGE, SOURCE_LOCK):
        raise ValueError("evaluation identity differs")
    differences, checked_snapshots = {}, {}
    for entry in lock["sources"]:
        slot = entry["slot"]
        case = summary["cases"][slot]
        reference = owned(source_root / slot / "AutoReopen/Record.json", entry["phase_sha256"][1])["result"]
        phases = {
            name: owned(trial / slot / name / "Record.json", metadata["sha256"])["result"]
            for name, metadata in case["native_phases"].items()
        }
        pairs = {
            "initial": (reference["before_edit"], phases["Open"]["before_edit"]),
            "edited": (reference["after_edit"], phases["Open"]["after_edit"]),
            "reopened": (reference["after_edit"], phases["Reopen"]["before_edit"]),
        }
        for phase, (reference_value, candidate_value) in pairs.items():
            left, right = reference_value["tree"], candidate_value["tree"]
            pins = [digest(wire(tree)) for tree in (left, right)]
            if pins != case["comparison"][phase]["native_tree_sha256"]:
                raise ValueError("snapshot tree differs from evaluated hashes")
            key = "/".join(pins)
            checked_snapshots[slot + "/" + phase] = key
            if key not in differences:
                differences[key] = compare(left, right)
    return {"freeze_sha256": FREEZE, "columns": KEYS, "snapshots": checked_snapshots, "differences": differences}


if __name__ == "__main__":
    sys.stdout.buffer.write(wire(examine()))
