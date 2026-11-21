from __future__ import annotations

import argparse
import json
from pathlib import Path

import InspectBlankDrawing as blank


PACKET_SHA256 = "04e1364393be6301e0c8f10bdacc5761e43ed7654c32d8a31265dabd249f5fa4"
SOURCE_ARTIFACTS = {
    "GeneratedRequest.json": "fb9e098382aa68bc8232bc7adebb3a02183fd9244de082086d1b5dd143e94362",
    "GeneratedConstruction.json": "9742daa30a1086a8ebc0f7d3a6badf106f64bf65fa56dc7bdaeb2c5698323923",
    "PropertyPrefixConstruction.json": "db3f4ab127ebaf1c10de2f2cbaceea8ea276b07af07e2a071c4dff0c5d4d67a3",
    "GeneratorSourceSnapshot.json": "3b88e43229e2c00a2c0658faad6db22160df91e9ff145af34b7dcb5f05a7deb1",
}
BASELINE_SHA256 = "7400cf1fa4a71994807ce8e49283e2721e09a5ceaf723e36f6ae807906c94a26"
GENERATED_SHA256 = "2ac13e616a8853add228bd11e21c400cb461b535bb9fc19252bb848bb410d1b4"
VALUE_NAMESPACE = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"


def read_packet(packet, packet_sha, runner_sha):
    require = blank.curves.require
    require(packet_sha == PACKET_SHA256, "property-prefix observer requires the frozen matched packet")
    require(blank.curves.digest(Path(__file__)) == runner_sha, "property-prefix observer bytes changed")
    job = blank.read_packet(packet, packet_sha)
    source = {}
    for name, expected in SOURCE_ARTIFACTS.items():
        artifact = packet.parent / name
        require(blank.curves.digest(artifact) == expected, f"property-prefix source proof changed: {name}")
        source[name] = json.loads(artifact.read_bytes())
    construction = source["GeneratedConstruction.json"]
    comparison = source["PropertyPrefixConstruction.json"]
    generated = next(row for row in job["cases"] if row["kind"] == "generated")
    require(job["generator_input_sha256"] == SOURCE_ARTIFACTS["GeneratedRequest.json"]
            and construction["native_sha256"] == generated["sha256"] == GENERATED_SHA256
            and construction["native_bytes"] == generated["bytes"]
            and construction["input_runtime_file_access_attempts"] == 0
            and construction["native_acceptance"] is False,
            "property-prefix neutral construction proof differs")
    require(comparison["before_sha256"] == BASELINE_SHA256
            and comparison["after_sha256"] == GENERATED_SHA256
            and comparison["changed_streams"] == ["docProps/ISolidWorksInformation.xml"]
            and comparison["generated_twice_identically"] and comparison["expanded_xml_tree_identical"]
            and comparison["input_runtime_file_access_attempts"] == 0
            and comparison["native_acceptance"] is False and comparison["heldout_inputs_tested"] == 0
            and comparison["property_count"] == comparison["dictionary_count"]
            and comparison["generated_ids"] == list(range(3, 3 + comparison["property_count"]))
            and comparison["vt_prefix_binding"] == VALUE_NAMESPACE and comparison["typed_value_prefix"] == "vt"
            and comparison["global_namespace_registration_changed"] is False,
            "property-prefix comparison proof differs")
    return job


def run(packet, packet_sha, runner_sha):
    read_packet(packet, packet_sha, runner_sha)
    report = blank.run(packet, packet_sha)
    read_packet(packet, packet_sha, runner_sha)
    accepted = bool(report["interpretable"] and report["reduced_native_passed"]
                    and report["generated_discovery_passed"] and report["inputs_immutable"]
                    and report["control_results"] == [True, True] and report["distinct_processes"] == 10)
    result = {
        **report,
        "schema": "kit.sw2026.blank-drawing-property-prefix-native-result.v1",
        "property_prefix_profile_passed": accepted,
        "property_prefix_observer_sha256": runner_sha,
        "source_proof_sha256": SOURCE_ARTIFACTS,
        "baseline_generated_sha256": BASELINE_SHA256,
        "corrected_generated_sha256": GENERATED_SHA256,
    }
    blank.curves.write_json(packet.parent / "Results" / "DrawingBlankPropertyPrefixResults.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description="Verify the generated property-prefix blank through edited save and fresh reopen")
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
    keys = ("property_prefix_profile_passed", "interpretable", "reduced_native_passed",
            "generated_discovery_passed", "distinct_processes", "inputs_immutable")
    print(json.dumps({key: result[key] for key in keys}))
    return 0 if result["property_prefix_profile_passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
