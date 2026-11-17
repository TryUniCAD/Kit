from __future__ import annotations

import argparse
import json
from pathlib import Path
from shutil import copyfile

from CheckBlankDrawingThreadFlag import compare
from CheckDrawingDefinitions import digest, require
from InspectBlankDrawing import input_path as previous_path, read_packet as read_previous_packet
from InspectBlankDrawingPair import CASES, SCHEMA, TOOL_NAMES, input_path, read_packet


TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[2]


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def prepare(*, baseline, baseline_sha, candidate, candidate_sha, output):
    require(not output.is_relative_to(ROOT) and not output.exists(), "pair staging requires a new directory outside the repository")
    first = read_previous_packet(baseline, baseline_sha)
    second = read_previous_packet(candidate, candidate_sha)
    require(first["cases"][:3] == second["cases"][:3], "the two source packets have different native controls")
    for key in ("generator_input_sha256", "authored_spec_sha256", "source_lock_sha256", "oracle_sha256"):
        require(first[key] == second[key], f"drawing source packets disagree on {key}")
    old, new = first["cases"][-1], second["cases"][-1]
    offline = compare(previous_path(baseline.parent, old).read_bytes(), previous_path(candidate.parent, new).read_bytes())
    comparison = TOOLS.parent.parent / "solidworks/measurements/2026/GeneratedBlankDrawingThreadFlag01.json"
    published = json.loads(comparison.read_bytes())
    require(all(published[key] == value for key, value in offline.items()), "drawing pair differs from the frozen cosmetic-thread comparison")

    output.mkdir(exist_ok=False)
    tool_directory = output / "Tools"
    tool_directory.mkdir()
    tool_hashes = {}
    for tool in TOOL_NAMES:
        code = (TOOLS / tool).read_bytes()
        (tool_directory / tool).write_bytes(code)
        tool_hashes[tool] = digest(code)
    for tool, identity in first["tool_hashes"].items():
        if tool in tool_hashes:
            require(tool_hashes[tool] == identity, f"the paired runner changed its existing native helper: {tool}")
    rows = []
    origin = ((baseline, first["cases"][0]), (baseline, first["cases"][2]), (baseline, old), (candidate, new))
    for name, (packet, row) in zip(CASES, origin, strict=True):
        staged = {**row, "name": name}
        path = input_path(output, staged)
        path.parent.mkdir(parents=True, exist_ok=False)
        copyfile(previous_path(packet.parent, row), path)
        rows.append(staged)
    offline_bytes = encode(offline)
    (output / "OfflinePair.json").write_bytes(offline_bytes)
    request = {"schema": SCHEMA, "native_acceptance": False, "source_trial_shas": [baseline_sha, candidate_sha],
               "control_sha256": first["control_sha256"], "oracle_sha256": first["oracle_sha256"],
               "offline_pair_sha256": digest(offline_bytes), "published_pair_sha256": digest(comparison.read_bytes()),
               "tool_hashes": tool_hashes, "cases": rows}
    packet = output / "Trial.json"
    raw = encode(request)
    packet.write_bytes(raw)
    read_packet(packet, digest(raw))
    return {"packet_sha256": digest(raw), "tool_hashes": tool_hashes}


def main():
    parser = argparse.ArgumentParser(description="Stage immutable paired drawing inputs and the pinned Windows observer")
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--baseline-sha256", required=True)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--candidate-sha256", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(baseline=args.baseline.resolve(), baseline_sha=args.baseline_sha256,
                             candidate=args.candidate.resolve(), candidate_sha=args.candidate_sha256,
                             output=args.out.resolve()), sort_keys=True))


if __name__ == "__main__":
    main()
