from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PureWindowsPath
import subprocess
import sys

AUTHOR_SDK = "66b81576ae9424372bb89f70369b90f28727e3cd6fa39e8070f5270bb5ff4a33"
SDK = "c038ac2e2d374d96930ea206b0bfc4eeec3b4013ad2e0e2e00862eb168b7864e"
OBSERVER = "bf6a9a76acc9040bee8bfdb5ea150d3a9d1ad7adfd1214d0af842cf4d1e91167"
IDS = ("D01", "D02", "D03", "D04")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked(base, row):
    path = (base / row["path"]).resolve(strict=True)
    if (
        not path.is_relative_to(base.resolve())
        or path.is_symlink()
        or digest(path) != row["sha256"]
        or path.stat().st_size != row["bytes"]
    ):
        raise ValueError("disclosed source export custody differs")
    return path


def path_config_binding(observed, native):
    configurations = observed["child_configuration_metadata"]["configurations"]
    reference = observed["view_reference_fields"]
    return (
        observed["declared_reference_file"].get("available") is True
        and PureWindowsPath(observed["declared_reference_file"]["native_file_path"])
        == PureWindowsPath(native["resolved_child_path"])
        and observed["child_sha256"] == native["resolved_child_sha256"]
        and len(configurations) == 1
        and configurations[0]["name"] == native["configuration"]
        and configurations[0]["selected_by_f360"] is True
        and configurations[0]["selected_by_f368"] is True
        and reference["f3c0"]
        == {
            "f08": native["configuration"],
            "f10": configurations[0]["native_object_id"],
        }
    )


def component_binding(observed, display):
    rows = display["component_reference_closure"]
    nodes = {row["identity"]["object_index"]: row for row in rows}

    def fields(identity, class_name):
        if (
            not isinstance(identity, dict)
            or identity.get("class") != class_name
            or identity.get("schema") != 1
            or identity.get("concrete_runtime_class") is not True
        ):
            raise ValueError("display component path has an unsupported typed owner")
        node = nodes[identity["object_index"]]
        if node["identity"] != identity:
            raise ValueError("display component path aliases a different owner")
        return node["fields"]

    if len(nodes) != len(rows):
        return False
    try:
        wrapper = display["wrapper_fields"]
        chain = fields(wrapper["f58"], "moChainComponent_c")
        reference_chain = fields(chain["f20"], "moReferenceChain_c")
        entries = fields(reference_chain["f08"], "moExtFeatureList_c")
        if reference_chain["f24"] != 0 or entries["n"] != 1 or len(entries["f08"]) != 1:
            return False
        external = fields(entries["f08"][0]["o"], "moExtFeature_c")
        return (
            external["f50"] == observed["actual_view_internal_reference"]
            and display["display_fields"]["f40"] == observed["actual_view"]
            and display["display_fields"]["f48"] == display["component_profile"]
        )
    except (KeyError, TypeError, ValueError):
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Join locked disclosed origin displays to actual native child feature ids"
    )
    parser.add_argument("candidate", type=Path)
    parser.add_argument("packet", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    args = parser.parse_args()
    packet = args.packet.resolve(strict=True)
    if digest(packet) != args.packet_sha256 or args.output.exists():
        raise ValueError("use the exact frozen source packet and an unused output")
    job = json.loads(packet.read_bytes())
    tools = packet.parent / "HostTools"
    if job["sdk_manifest_sha256"] != AUTHOR_SDK:
        raise ValueError("use the exact independently frozen SDK reader profile")
    for name, expected in job["host_tools_sha256"].items():
        if digest(tools / name) != expected:
            raise ValueError("host origin source observer changed")
    observer = tools / "InspectDrawingProfileChild.py"
    if digest(observer) != OBSERVER:
        raise ValueError("the actual child graph observer changed")
    record = json.loads(
        (
            packet.parent / "Progress/disclosed/C00/export-disclosed/Record.json"
        ).read_bytes()
    )
    exported = packet.parent / "DisclosedExports"
    index = exported / "Index.json"
    if (
        record["packet_sha256"] != args.packet_sha256
        or record["passed"] is not True
        or digest(index) != record["disclosed_export_sha256"]
    ):
        raise ValueError("disclosed source export is not locked")
    inputs = json.loads(index.read_bytes())
    if (
        inputs["packet_sha256"] != args.packet_sha256
        or inputs["cohort"] != "disclosed"
        or tuple(row["case"] for row in inputs["cases"]) != IDS
        or inputs["heldout_details_exported"] is not False
    ):
        raise ValueError("only the exact four disclosed native sources are admitted")
    args.output.mkdir(parents=True)
    report = {
        "schema": "kit.sw2026.native-origin-source-profile-join.v1",
        "packet_sha256": args.packet_sha256,
        "export_sha256": digest(index),
        "sdk_manifest_sha256": SDK,
        "author_sdk_manifest_sha256": AUTHOR_SDK,
        "reader_refresh_only": True,
        "prior_failed_join_sha256": "0d3d1cc4b2142fd9be3f5304c995bab778c28c23dd44a4a48fc01761178c756e",
        "observer_source_sha256": digest(Path(__file__)),
        "states": [],
        "native_acceptance": False,
        "heldout_acceptance": False,
        "new_writer_inputs_exposed": False,
        "hidden_inputs_read": 0,
    }
    signatures = {}
    for state in ("source", "moved"):
        pairs = []
        for row in inputs["cases"]:
            obs = row["observations"][state]
            child, drawing = checked(exported, row["child"]), checked(
                exported, row["drawings"][state]
            )
            pairs.append(
                {
                    "case": row["case"],
                    "role": state,
                    "drawing": {
                        "path": str(drawing),
                        "bytes": drawing.stat().st_size,
                        "sha256": digest(drawing),
                    },
                    "child": {
                        "path": str(child),
                        "bytes": child.stat().st_size,
                        "sha256": digest(child),
                    },
                    "orientation": obs["orientation"],
                    "declared_expected_native_resolved_path": obs[
                        "resolved_child_path"
                    ],
                }
            )
        pair_path = args.output / (state + "Pairs.json")
        pair_path.write_text(
            json.dumps(
                {
                    "schema": "kit.sw2026.disclosed-profile-child-pairs.v1",
                    "pairs": pairs,
                },
                indent=2,
            )
            + "\n"
        )
        raw_path = args.output / (state + "Profiles.json")
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                str(observer),
                str(args.candidate),
                str(pair_path),
                str(raw_path),
                "--manifest-sha256",
                SDK,
                "--pairs-sha256",
                digest(pair_path),
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        (args.output / (state + ".stdout")).write_text(result.stdout)
        (args.output / (state + ".stderr")).write_text(result.stderr)
        if result.returncode != 0:
            report["states"].append(
                {
                    "state": state,
                    "reader_completed": False,
                    "return_code": result.returncode,
                    "raw_report_sha256": (
                        digest(raw_path) if raw_path.exists() else None
                    ),
                }
            )
            continue
        actual = json.loads(raw_path.read_bytes())
        if actual["data_collected"] is not True:
            raise ValueError("the actual child source observation is incomplete")
        for observed, original in zip(actual["cases"], inputs["cases"], strict=True):
            native = original["observations"][state]
            owners = native["feature_owners"]
            origin_id = owners["origin"]["feature_id"]
            sketch_id = owners["ordinary_profile"]["feature_id"]
            seen = []
            path_config_match = path_config_binding(observed, native)
            valid = path_config_match
            for display in observed["profile_displays"]:
                target = display["actual_child_profile"]
                role = (
                    "origin"
                    if target and target["class"] == "moOriginProfileFeature_c"
                    else (
                        "ordinary-profile"
                        if target and target["class"] == "moProfileFeature_c"
                        else "unsupported"
                    )
                )
                expected = (
                    origin_id
                    if role == "origin"
                    else sketch_id if role == "ordinary-profile" else None
                )
                match = (
                    target is not None
                    and target["native_f08"] == expected
                    and display["native_feature_id"] == expected
                    and display.get("creation_log_epoch_equal") is True
                    and component_binding(observed, display)
                )
                valid = valid and match
                seen.append(
                    {
                        "role": role,
                        "actual_child_class": target["class"] if target else None,
                        "native_api_feature_id": expected,
                        "native_reference_feature_id": display["native_feature_id"],
                        "creation_epoch": display["native_creation_stamp"],
                        "actual_native_child_match": match,
                        "actual_view_component_path_match": component_binding(
                            observed, display
                        ),
                    }
                )
            origin_count = sum(
                value["role"] == "origin" and value["actual_native_child_match"]
                for value in seen
            )
            signature = [
                (
                    value["role"],
                    value["native_reference_feature_id"],
                    value["creation_epoch"],
                )
                for value in seen
            ]
            preserved = state == "source" or signature == signatures.get(
                original["case"]
            )
            if state == "source":
                signatures[original["case"]] = signature
            report["states"].append(
                {
                    "case": original["case"],
                    "state": state,
                    "reader_completed": True,
                    "actual_child_path_and_configuration_match": path_config_match,
                    "displays": seen,
                    "origin_count": origin_count,
                    "exact_origin_only_family": valid
                    and origin_count == len(seen) == 1,
                    "native_source_target_id_distinct_from_ordinary_sketch": origin_id
                    != sketch_id,
                    "view_move_preserved_profile_signature": preserved,
                    "raw_report_sha256": digest(raw_path),
                }
            )
    report["origin_source_family_measured"] = len(report["states"]) == 8 and all(
        row.get("reader_completed")
        and row.get("exact_origin_only_family")
        and row.get("view_move_preserved_profile_signature")
        for row in report["states"]
    )
    report["native_source_without_origin_or_with_other_profiles_is_retained"] = True
    (args.output / "Result.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    print(
        json.dumps(
            {
                "origin_source_family_measured": report[
                    "origin_source_family_measured"
                ],
                "result_sha256": digest(args.output / "Result.json"),
                "native_acceptance": False,
                "heldout_acceptance": False,
            }
        )
    )
    return 0 if report["origin_source_family_measured"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
