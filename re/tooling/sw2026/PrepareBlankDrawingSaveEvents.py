from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from shutil import copyfile


SOURCE_NAMES = ("Pristine", "ReducedNative", "ThreadFlag")
CASE_NAMES = ("Pristine", "ReducedNative", "Generated")
RUNNER = "InspectBlankDrawingSaveEvents.py"
SAVE_MODE = "InspectDrawingSaveModes.py"
FILE_NAME = "KitBlankSheetProbe.SLDDRW"
SCHEMA = "kit.sw2026.blank-drawing-save-event-trial.v1"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked(path, sha):
    data = path.read_bytes()
    if digest(data) != sha:
        raise ValueError(f"input differs from the frozen digest for {path.name}")
    return data


def prepare(prior_path, prior_sha, receipt_path, receipt_sha, output):
    if output.exists():
        raise ValueError("choose an unused private output directory")
    prior = json.loads(checked(prior_path, prior_sha))
    receipt = json.loads(checked(receipt_path, receipt_sha))
    if (prior["schema"] != "kit.sw2026.blank-drawing-pair.v1" or receipt["packet_sha256"] != prior_sha or
        prior["oracle_sha256"] != receipt["oracle_sha256"] or not receipt["controls_healthy"] or not receipt["inputs_immutable"]):
        raise ValueError("the paired source lacks healthy matched save-mode evidence")
    source_rows = {row["name"]: row for row in prior["cases"]}
    observed = {row["input_sha256"]: row for row in receipt["modes"] if row["mode"] == "RebuildSaveAs"}
    reduced, generated = (observed[source_rows[name]["sha256"]] for name in SOURCE_NAMES[1:])
    if not reduced["passed"] or generated["save_status"] != [False, 1, 0]:
        raise ValueError("the matched reduced save and generated failure must both be measured")
    input_rows = []
    for label, source_name in zip(CASE_NAMES, SOURCE_NAMES, strict=True):
        source = source_rows[source_name]
        original = prior_path.parent / "Inputs" / source_name / source["filename"]
        data = checked(original, source["sha256"])
        if len(data) != source["bytes"] or source["expected"]["view"] is not None:
            raise ValueError("the save observer admits only the pinned blank lanes")
        row = {key: source[key] for key in ("bytes", "sha256", "expected")}
        row["name"] = label
        if label == "Generated":
            row["expected_tree"] = source["expected_tree"]
        input_rows.append((row, data))
    frozen = prior_path.parent / "Tools"
    tools = {name: checked(frozen / name, sha) for name, sha in prior["tool_hashes"].items()}
    tools[SAVE_MODE] = checked(frozen / SAVE_MODE, receipt["runner_sha256"])
    tools[RUNNER] = Path(__file__).with_name(RUNNER).read_bytes()
    output.mkdir(exist_ok=False)
    guest = output / "Tools"
    guest.mkdir(exist_ok=False)
    for name, code in tools.items():
        (guest / name).write_bytes(code)
    for row, data in input_rows:
        path = output / "Inputs" / row["name"] / FILE_NAME
        path.parent.mkdir(parents=True, exist_ok=False)
        path.write_bytes(data)
    packet = {
        "schema": SCHEMA, "writer_output_count": 0, "native_acceptance": False, "heldout_inputs_tested": 0,
        "prior_packet_sha256": prior_sha, "prior_native_receipt_sha256": receipt_sha,
        "oracle_sha256": prior["oracle_sha256"], "control_sha256": prior["control_sha256"],
        "preparer_sha256": digest(Path(__file__).read_bytes()),
        "tool_hashes": {name: digest(code) for name, code in tools.items()}, "cases": [row for row, _ in input_rows],
    }
    manifest = output / "Trial.json"
    encoded = (json.dumps(packet, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    manifest.write_bytes(encoded)
    sha = digest(encoded)
    subprocess.run([sys.executable, "-B", str(guest / RUNNER), str(manifest), "--packet-sha256", sha, "--verify-only"],
                   check=True, capture_output=True, timeout=20)
    return {"packet": str(manifest), "packet_sha256": sha, "preparer_sha256": packet["preparer_sha256"],
            "runner_sha256": packet["tool_hashes"][RUNNER], "save_mode_observer_sha256": packet["tool_hashes"][SAVE_MODE],
            "input_sha256": {row["name"]: row["sha256"] for row, _ in input_rows}}


def main():
    parser = argparse.ArgumentParser(description="Freeze the blank drawing COM save event probe outside the checkout")
    parser.add_argument("prior", type=Path)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--prior-sha256", required=True)
    parser.add_argument("--receipt-sha256", required=True)
    arguments = parser.parse_args()
    workspace = arguments.receipt.resolve().parents[4]
    if arguments.output.resolve().is_relative_to(workspace):
        raise ValueError("choose a private output directory outside the checkout")
    print(json.dumps(prepare(arguments.prior.resolve(), arguments.prior_sha256, arguments.receipt.resolve(),
                             arguments.receipt_sha256, arguments.output.resolve()), sort_keys=True))


if __name__ == "__main__":
    main()
