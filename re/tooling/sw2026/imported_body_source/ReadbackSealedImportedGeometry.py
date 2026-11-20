from argparse import ArgumentParser
from hashlib import sha256
import json
from math import isclose
import os
from pathlib import Path
import sys


RESULT = "2eddd9242ad840fc4a424d4269ed7404634637f56ae94fe56ed917e7095626fe"
REVISION = "a2a8125d136a43f750dafee4f0f4d93d04255301"
SOURCE_ROOT = Path(r"C:\KitImportedBodySources04")
GENERATED_ROOT = Path(r"C:\KitImportedEvaluation01")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked(path, expected):
    data = path.read_bytes()
    require(sha256(data).hexdigest() == expected, "sealed readback checksum differs")
    return data


def evaluate(packet):
    from ProjectDisclosedImport import decode_import, rectangular_boundary
    from ReplayImportedBaseBody import measure

    result = json.loads(checked(packet / "Result.json", RESULT))
    require(result["writer_revision"] == REVISION and result["controls_healthy"]
            and result["complete_heldout_geometry_lifecycles"] == 2, "expected exact completed geometry receipt")
    verified = {}
    for slot, evidence in result["cases"].items():
        require(slot in ("Slot01", "Slot02"), "unexpected source slot")
        stages = (("original", SOURCE_ROOT / slot / "Source.SLDPRT", evidence["input_sha256"]),
                  ("generated", GENERATED_ROOT / (slot + ".SLDPRT"), evidence["candidate_sha256"]),
                  ("saved", GENERATED_ROOT / (slot + "Saved.SLDPRT"), evidence["saved_candidate_sha256"]))
        baseline, import_name = None, None
        rows = {}
        for phase, path, checksum in stages:
            document = decode_import(checked(path, checksum))
            feature, = (row for row in document.feature_timeline if row.kind == "imported")
            require(len(document.bodies) == 1, "sealed readback lost the sole body")
            boundary = rectangular_boundary(document.brep, document.bodies[0].id)
            if baseline is None:
                baseline, import_name = boundary, feature.name
            require(feature.name == import_name and
                    all(isclose(actual, expected, rel_tol=0.0, abs_tol=1e-9)
                        for actual_axis, expected_axis in zip(boundary.limits, baseline.limits, strict=True)
                        for actual, expected in zip(actual_axis, expected_axis, strict=True)),
                    "sealed readback changed import identity or its complete physical boundary")
            replay = measure(path, checksum)
            require(len(replay["matched_streams"]) == 5, "the five linked streams must re-emit exactly")
            rows[phase] = {"source_sha256": checksum, "checked_complete_physical_boundary": True,
                           "same_import_name": True, "linked_streams": replay["matched_streams"]}
        verified[slot] = rows
    return {"schema": "kit.sw2026.sealed-import-geometry-readback.v1", "native_result_sha256": RESULT,
            "sdk_revision": REVISION, "case_count": len(verified), "valid_models": 6,
            "exact_linked_streams": 30, "heldout_payloads_shared": 0, "cases": verified}


if __name__ == "__main__":
    parser = ArgumentParser(description="Read the sealed import artifacts solely inside the oracle guest")
    parser.add_argument("packet", type=Path)
    args = parser.parse_args()
    require(os.name == "nt", "sealed original inputs must stay inside Windows")
    packet = args.packet.resolve(strict=True)
    root = packet / "Code"
    sys.path[:0] = [str(root), str(root / "src"), str(root / "re/tooling/sw2026"),
                    str(root / "re/tooling/sw2026/serial"), str(root / "re/tooling/sw2026/imported_body_source")]
    try:
        receipt = evaluate(packet)
    except Exception as error:
        trace = GENERATED_ROOT / "ReadbackFailure.json"
        trace.write_text(json.dumps({"error": repr(error)}) + "\n", encoding="utf-8")
        print(json.dumps({"passed": False, "error_type": type(error).__name__}))
        raise SystemExit(1)
    with (packet / "Readback.json").open("x", encoding="utf-8") as target:
        json.dump(receipt, target, indent=2, sort_keys=True, allow_nan=False)
        target.write("\n")
    print(json.dumps({"passed": True, "valid_models": receipt["valid_models"], "exact_linked_streams": receipt["exact_linked_streams"]}))
