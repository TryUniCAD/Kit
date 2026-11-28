from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from AuthorCurves import digest, require


DISCLOSED = {
    "N01NestedSingle": "3f793c6aa6d5fd8569f7ed627e7c12b44ec380c2deeecb36a62a817e546e67d3",
    "N02MixedRepeated": "a980abd0a602a587d9277a05e12a84cddba657c8513ff3418128f8056645aa37",
}


def observation(root, name, sha):
    folder = root / name
    path = folder / "Reopen.json"
    require(folder.resolve() == folder and path.resolve() == path and digest(path) == sha, "disclosed reopen log does not match its pinned identity")
    result = json.loads(path.read_bytes())["result"]
    require(not result["passed"] and result["open_errors"] == result["open_warnings"] == 0 and
            result["native_files_match_persisted"] and "initial" in result and "rebuilt" in result, "disclosed reopen gate differs")
    row, = result["dialogs"]
    require(row["kind"] == "unclassified-owned-dialog" and row["dismissed"] is False and row["process_id"] == result["oracle_identity"]["process_id"],
            "disclosed progress observation lacks the exact owned process")
    return row


def reproduce(root):
    originals = [(name, observation(root, name, sha)) for name, sha in DISCLOSED.items()]
    row = originals[0][1]
    later = row["text"][1:]
    inputs = [(name, source, True) for name, source in originals]
    inputs.extend(("established " + status.replace("\n", " "), row | {"text": [status, *later]}, True)
                  for status in ("Open\nComponents", "Opening -2\nComponents", "Loaded\nComponents"))
    inputs.extend(("malformed " + status, row | {"text": [status, *later]}, False) for status in (
        "Opening Component 0 of 2", "Opening Component 3 of 2", "Opening Component 2 of 0", "Opening Component -1 of 2",
        "Opening Component 2 of 2 items", "Opening Component 2 out of 2",
    ))
    inputs.extend([
        ("named modal", row | {"dialog": "SOLIDWORKS"}, False),
        ("unexpected modal action", row | {"buttons": [*row["buttons"], "OK"]}, False),
        ("warning alongside stages", row | {"text": [*row["text"], "Unable to open the referenced component."]}, False),
        ("missing assembly stage", row | {"text": [row["text"][0], *row["text"][2:]]}, False),
        ("different graphics stage", row | {"text": row["text"][:2] + ["Saving\nGraphics"] + row["text"][3:]}, False),
    ])
    program = Path(__file__).with_name("ObserveAssemblyLoad.py")
    result = subprocess.run([sys.executable, "-B", str(program), "--classify"], input=json.dumps([item[1] for item in inputs]).encode(),
                            capture_output=True, check=True, timeout=15)
    actual = json.loads(result.stdout)
    expected = [item[2] for item in inputs]
    require(actual == expected and not result.stderr, "frozen classifier process returned an unexpected result")
    return {
        "schema": "kit.sw2026.indexed-assembly-progress-classification.v1", "passed": True,
        "classifier_sha256": digest(program), "reproducer_sha256": digest(Path(__file__)),
        "disclosed_observations": [{"name": name, "record_sha256": DISCLOSED[name], "first_status": value["text"][0], "dismissed": False}
                                    for name, value in originals],
        "classifications": [{"case": item[0], "progress": seen} for item, seen in zip(inputs, actual, strict=True)],
        "native_acceptance": False, "original_batch_reclassified": False, "heldout_inputs_read": 0,
    }


def main():
    parser = argparse.ArgumentParser(description="Replay disclosed assembly progress observations through the classifier process")
    parser.add_argument("disclosed_results", type=Path)
    print(json.dumps(reproduce(parser.parse_args().disclosed_results.resolve(strict=True)), indent=2))


if __name__ == "__main__":
    main()
