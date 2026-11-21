from __future__ import annotations

import argparse
import json
from pathlib import Path

import InspectBlankDrawing as blank


PACKET_SHA256 = "e0aab1bbdac876403626aa2a35fb41c1569fab326e63f051c00474263ac09301"
SOURCE_ARTIFACTS = {
    "GeneratedRequest.json": "fb9e098382aa68bc8232bc7adebb3a02183fd9244de082086d1b5dd143e94362",
    "GeneratedConstruction.json": "570a9c637b721e2fd61f1654bd0edfd244439c02afc88e987e21a9592f3f1be1",
    "PropertySectionConstruction.json": "37aaab3056f77e9687c750b828051a04e9fe9f49ce2a1e33c7beb212cebd86ca",
}
BASELINE_SHA256 = "ab2b76a87f11344b9172a23ce88985ec8fa4aa98518d1d21597d6dfb1e2c6eeb"
GENERATED_SHA256 = "7400cf1fa4a71994807ce8e49283e2721e09a5ceaf723e36f6ae807906c94a26"


def read_packet(packet, packet_sha, runner_sha):
    require = blank.curves.require
    require(packet_sha == PACKET_SHA256, "property-section observer requires the frozen matched packet")
    require(blank.curves.digest(Path(__file__)) == runner_sha, "property-section observer bytes changed")
    job = blank.read_packet(packet, packet_sha)
    source = {}
    for name, expected in SOURCE_ARTIFACTS.items():
        artifact = packet.parent / name
        require(blank.curves.digest(artifact) == expected, f"property-section source proof changed: {name}")
        source[name] = json.loads(artifact.read_bytes())
    construction = source["GeneratedConstruction.json"]
    comparison = source["PropertySectionConstruction.json"]
    generated = next(row for row in job["cases"] if row["kind"] == "generated")
    require(job["generator_input_sha256"] == SOURCE_ARTIFACTS["GeneratedRequest.json"]
            and construction["native_sha256"] == generated["sha256"] == GENERATED_SHA256
            and construction["native_bytes"] == generated["bytes"]
            and construction["input_runtime_file_access_attempts"] == 0
            and construction["native_acceptance"] is False,
            "property-section neutral construction proof differs")
    require(comparison["before_sha256"] == BASELINE_SHA256
            and comparison["after_sha256"] == GENERATED_SHA256
            and comparison["changed_streams"] == ["docProps/ISolidWorksInformation.xml"]
            and comparison["generated_twice_identically"]
            and comparison["input_runtime_file_access_attempts"] == 0
            and comparison["native_acceptance"] is False
            and comparison["property_count"] == comparison["dictionary_count"]
            and comparison["generated_ids"] == list(range(3, 3 + comparison["property_count"])),
            "property-section comparison proof differs")
    return job


def run(packet, packet_sha, runner_sha):
    read_packet(packet, packet_sha, runner_sha)
    report = blank.run(packet, packet_sha)
    read_packet(packet, packet_sha, runner_sha)
    accepted = bool(report["interpretable"] and report["reduced_native_passed"]
                    and report["generated_discovery_passed"] and report["inputs_immutable"]
                    and report["control_results"] == [True, True])
    result = {
        **report,
        "schema": "kit.sw2026.blank-drawing-property-section-native-result.v1",
        "property_section_profile_passed": accepted,
        "property_section_observer_sha256": runner_sha,
        "source_proof_sha256": SOURCE_ARTIFACTS,
        "baseline_generated_sha256": BASELINE_SHA256,
        "corrected_generated_sha256": GENERATED_SHA256,
    }
    blank.curves.write_json(packet.parent / "Results" / "DrawingBlankPropertySectionsResults.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description="Verify the generated native property-section blank through edited save and fresh reopen")
    parser.add_argument("packet", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--runner-sha256", required=True)
    parser.add_argument("--verify-only", action="store_true")
    arguments = parser.parse_args()
    packet = arguments.packet.resolve()
    if arguments.verify_only:
        read_packet(packet, arguments.packet_sha256, arguments.runner_sha256)
        print(json.dumps({"custody_verified": True, "packet_sha256": arguments.packet_sha256}))
        return 0
    result = run(packet, arguments.packet_sha256, arguments.runner_sha256)
    keys = ("property_section_profile_passed", "interpretable", "reduced_native_passed",
            "generated_discovery_passed", "distinct_processes", "inputs_immutable")
    print(json.dumps({key: result[key] for key in keys}))
    return 0 if result["property_section_profile_passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
