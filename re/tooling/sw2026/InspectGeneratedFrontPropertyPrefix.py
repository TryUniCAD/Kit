from __future__ import annotations

import argparse
import json
from pathlib import Path

import InspectGeneratedFrontDrawing as front


PACKET_SHA256 = "29c6525ad6b2978131f81c6cf6ac82229964d9818d6a4f3d5a21382d24074776"
TOOLS_SHA256 = "bc7328761783cbd2f156a1c9b6ef8d7fa1d66b8157cb224759ee2aa1597e4d00"
SOURCE_ARTIFACTS = {
    "GeneratedRequest.json": "f13c84206c729b53f0bd656c1deec5fae4547c4842a020c19a83f395f31b480e",
    "GeneratedConstruction.json": "579187a7a1a6950ced7662a51fe0900d3c8654de9045ad0cc66cd59590b440c8",
    "IsolatedRequest.json": "7d49fc5cfbc3d01c7ea6805c1241354f45817abdc96460958e354e3bef971ce8",
    "IsolatedConstruction.json": "a753333e71d05a9fb45a180e4724bb6db4b65c1078f631d8de9d5ffde41976ca",
    "IsolatedPrefixComparison.json": "e5a2e8eec953dd251fef2fa1c1d6cf709192117b9667278109e262d6b3e047ca",
    "GeneratorSourceSnapshot.json": "60b22302ec251d3d90524aa2a1ec533955f12ed4ccb2906e0020d15410d0f49b",
}
DRAWING_SHA256 = "c236cb7690ea21163965b2e751bfcb5f0d3633ec90dd71c2769545728dd8064a"
CHILD_SHA256 = "ce72214680280a08447afd494895b19a6b4b23a1bf74d718c45fd8a799c3143f"
BASELINE_DRAWING_SHA256 = "b7d9b079e9dcb57552e4fefb2a3d1676a5df6e7dcb5c3a5990778dd82da819f2"
BASELINE_CHILD_SHA256 = "493aea98fb6035ea7058516d90b72c597701b0418abd0e2bb71bb6c884ea8e42"


def read_packet(packet, packet_sha, tools_sha, runner_sha):
    require = front.curves.require
    require(packet_sha == PACKET_SHA256 and tools_sha == TOOLS_SHA256,
            "front property-prefix observer requires the frozen matched packet and tools")
    require(front.curves.digest(Path(__file__)) == runner_sha, "front property-prefix observer bytes changed")
    job = front.read_job(packet, packet_sha, tools_sha)
    source = {}
    for name, expected in SOURCE_ARTIFACTS.items():
        artifact = packet.parent / name
        require(front.curves.digest(artifact) == expected, f"front property-prefix source proof changed: {name}")
        source[name] = json.loads(artifact.read_bytes())
    construction = source["GeneratedConstruction.json"]
    isolated = source["IsolatedConstruction.json"]
    comparison = source["IsolatedPrefixComparison.json"]
    row = job["inputs"][-1]
    require(row["name"] == "GeneratedInput" and row["drawing"]["sha256"] == DRAWING_SHA256
            and row["part"]["sha256"] == CHILD_SHA256
            and construction["drawing"]["sha256"] == DRAWING_SHA256
            and construction["part"]["sha256"] == CHILD_SHA256
            and construction["native_acceptance"] is False and construction["input_runtime_file_access_attempts"] == 0
            and construction["inspection"]["readback_exact"] and isolated["inspection"]["readback_exact"]
            and isolated["native_acceptance"] is False and isolated["input_runtime_file_access_attempts"] == 0,
            "front property-prefix construction proof differs")
    require(job["generated_request_sha256"] == SOURCE_ARTIFACTS["GeneratedRequest.json"]
            and comparison["same_path_request_sha256"] == SOURCE_ARTIFACTS["IsolatedRequest.json"]
            and comparison["before_drawing_sha256"] == BASELINE_DRAWING_SHA256
            and comparison["before_child_sha256"] == comparison["after_child_sha256"] == BASELINE_CHILD_SHA256
            and comparison["after_drawing_sha256"] == isolated["drawing"]["sha256"]
            and comparison["drawing_changed_streams"] == ["docProps/ISolidWorksInformation.xml"]
            and comparison["child_identical"] and comparison["expanded_property_xml_identical"]
            and comparison["sdk_inspection_identical"] and comparison["isolated_twice_identical"]
            and comparison["fresh_path_twice_identical"] and comparison["input_runtime_file_access_attempts"] == 0
            and comparison["native_acceptance"] is False and comparison["heldout_inputs_tested"] == 0,
            "front property-prefix isolated comparison proof differs")
    return job


def run(packet, packet_sha, tools_sha, runner_sha):
    read_packet(packet, packet_sha, tools_sha, runner_sha)
    report = front.run(packet, packet_sha, tools_sha)
    read_packet(packet, packet_sha, tools_sha, runner_sha)
    lanes = report["lanes"]
    accepted = bool(report["interpretable"] and report["generated_trial_passed"]
                    and report["input_files_immutable"] and report["distinct_processes"] == 8
                    and all(lanes.get(name, {}).get("passed") for name in (
                        "ControlBefore", "ReducedControl", "GeneratedPair", "ControlAfter")))
    result = {
        **report,
        "schema": "kit.sw2026.front-drawing-property-prefix-native-result.v1",
        "property_prefix_front_profile_passed": accepted,
        "property_prefix_observer_sha256": runner_sha,
        "source_proof_sha256": SOURCE_ARTIFACTS,
        "generated_drawing_sha256": DRAWING_SHA256,
        "generated_child_sha256": CHILD_SHA256,
    }
    front.curves.write_json(packet.parent / "GeneratedFrontResults" / "GeneratedFrontPropertyPrefixResults.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description="Verify the generated front-view property prefix through linked edit, save and fresh reopen")
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--tools-sha256", required=True)
    parser.add_argument("--runner-sha256", required=True)
    parser.add_argument("--verify-only", action="store_true")
    arguments = parser.parse_args()
    packet = arguments.packet.resolve()
    if arguments.verify_only:
        read_packet(packet, arguments.packet_sha256, arguments.tools_sha256, arguments.runner_sha256)
        print(json.dumps({"custody_verified": True, "packet_sha256": arguments.packet_sha256}))
        return 0
    result = run(packet, arguments.packet_sha256, arguments.tools_sha256, arguments.runner_sha256)
    keys = ("property_prefix_front_profile_passed", "interpretable", "generated_trial_passed",
            "distinct_processes", "input_files_immutable")
    print(json.dumps({key: result[key] for key in keys}))
    return 0 if result["property_prefix_front_profile_passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
