from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path, PureWindowsPath
import shutil
import sys

METADATA = "60db6487419215724e9f48f7f17ae1f5aa373e6cb39a868dda02c31658f7f78c"
CONTROL = "92b83376b42ca55aa3b32a350635585c788ea0f968cc6e54f1730fdeb3c99caa"
PREDICTION = "e3526797ad49d04073a46e9a93a178377195f776697abe141d7d6ed54d112ca5"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
HELPERS = (
    "AuthorCurves.py",
    "AuthorRectangleAnchors.py",
    "Swapp.py",
    "OracleIdentity.py",
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )


def freeze(args):
    base = args.research_root.resolve(strict=True)
    source = args.source_root.resolve(strict=True) / "re/tooling/sw2026"
    tools = Path(__file__).resolve().parent
    metadata = tools.parent / "ApiMetadata01.json"
    control = (
        base
        / "ConcentricMateSourcePacket02/Disclosed/D01/Native/Source/ConcentricD01Child.SLDPRT"
    )
    prediction = (
        base
        / "GeneratedConcentricObserver01/RootPacket10/Evidence/FeaturePrediction.json"
    )
    if (
        digest(metadata) != METADATA
        or digest(control) != CONTROL
        or digest(prediction) != PREDICTION
    ):
        raise ValueError(
            "the exact disclosed metadata, pristine control or independent control prediction changed"
        )
    if args.output.exists():
        raise FileExistsError("source packet destination must be unused")
    prefix = PureWindowsPath(args.guest_packet)
    if not prefix.is_absolute() or not str(prefix).startswith(
        "\\\\Mac\\Home\\Documents\\UniCAD\\Oracle121Takeover\\"
    ):
        raise ValueError("use the declared mounted research packet path")
    private = PureWindowsPath(args.guest_private_root)
    if (
        private.drive.casefold() != "c:"
        or not private.is_absolute()
        or len(private.parts) != 2
    ):
        raise ValueError(
            "sealed designs require a separate explicit guest-local top-level directory"
        )
    args.output.mkdir(parents=True)
    (args.output / "Tools").mkdir()
    files = {}
    for name in (
        *HELPERS,
        "AuthorEquationSources01.py",
        "CaptureEquationApi01.py",
        "FreezeEquationSources01.py",
    ):
        current = source / name if name in HELPERS else tools / name
        ast.parse(current.read_text())
        target = args.output / "Tools" / name
        shutil.copyfile(current, target)
        files["Tools/" + name] = digest(target)
    shutil.copyfile(metadata, args.output / "ApiMetadata01.json")
    shutil.copyfile(control, args.output / "Control.SLDPRT")
    files["ApiMetadata01.json"] = METADATA
    files["Control.SLDPRT"] = CONTROL
    saved = json.loads(prediction.read_bytes())["control"]
    disclosed = [
        {
            "id": "D01",
            "family": "global_width",
            "width_mm": 31.7,
            "height_mm": 14.3,
            "depth_mm": 9.1,
            "edit_width_mm": 46.9,
            "global_name": "source_width",
            "divisor": 2,
        },
        {
            "id": "D02",
            "family": "width_depth",
            "width_mm": 43.7,
            "height_mm": 18.1,
            "depth_mm": 21.85,
            "edit_width_mm": 58.3,
            "global_name": "unused_source_width",
            "divisor": 2,
        },
    ]
    job = {
        "schema": "kit.sw2026.equation-source-protocol.v1",
        "writer_output_count": 0,
        "native_acceptance": False,
        "oracle_sha256": ORACLE,
        "api_metadata_sha256": METADATA,
        "guest_runtime": {
            "executable": "C:\\Users\\odin\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
            "version": [3, 12, 7],
            "pointer_bits": 64,
        },
        "guest_private_root": str(private),
        "files_sha256": files,
        "slots": {
            "D01": "disclosed_global_width",
            "D02": "disclosed_width_depth",
            "Slot01": "sealed_global_width",
            "Slot02": "sealed_width_depth",
        },
        "disclosed_cases": disclosed,
        "control_prediction": saved["initial"]["child"],
        "control_dimensions_m": {
            saved["radial_parameter"]: saved["radial_value_m"],
            saved["depth_parameter"]: saved["depth_m"],
        },
        "control_tree": saved["child_tree"],
        "control_prediction_source_sha256": PREDICTION,
        "sealed_intent_policy": {
            "sampler": "guest SystemRandom; values never materialized on host",
            "width_mm_integer_um": [22001, 61000],
            "height_mm_integer_um": [10001, 29000],
            "independent_depth_mm_integer_um": [7001, 19000],
            "minimum_width_edit_mm": 4,
            "pad_depth_relation": "actual upstream width / 2",
            "global_assignment": "explicit millimetres",
            "native_owners": ["AnchorSketch", "AnchorBoss"],
            "opaque_progress_only": True,
        },
    }
    write_new(args.output / "Protocol.json", job)
    wanted = digest(args.output / "Protocol.json")
    command = [
        job["guest_runtime"]["executable"],
        "-B",
        str(prefix / "Tools/AuthorEquationSources01.py"),
        "--job",
        str(prefix / "Protocol.json"),
        "--sha256",
        wanted,
    ]
    stages = []
    for slot in job["slots"]:
        stages.append(
            {
                "slot": slot,
                "seal_argv": command + ["seal", "--slot", slot],
                "phases": [
                    {
                        "phase": phase,
                        "argv": command + ["phase", "--slot", slot, "--phase", phase],
                        "new_process_required": True,
                        "recommended_transport_timeout_seconds": 360,
                    }
                    for phase in (
                        "ControlBefore",
                        "Author",
                        "ReopenOriginal",
                        "ReopenEdited",
                        "ControlAfter",
                    )
                ],
                "lock_argv": command + ["lock", "--slot", slot],
                "run_trailing_control_even_if_earlier_phase_fails": True,
            }
        )
    recipe = {
        "schema": "kit.sw2026.equation-source-recipe.v1",
        "protocol_sha256": wanted,
        "verify_argv": command + ["verify"],
        "stages": stages,
        "recovery_argv_prefix": command + ["recover"],
        "recovery_arguments": [
            "--journal",
            "EXACT_OWNED_AUTHOR_PREFERENCE_JOURNAL",
            "--output",
            "UNUSED_GUEST_RECOVERY_RECEIPT",
        ],
        "root_exclusive_native_execution": True,
        "source_only": True,
        "writer_output_count": 0,
        "native_phases_executed_during_freeze": 0,
    }
    write_new(args.output / "Recipe01.json", recipe)
    write_new(
        args.output / "PacketManifest01.json",
        {
            "schema": "kit.sw2026.equation-source-packet-manifest.v1",
            "files_sha256": {
                str(path.relative_to(args.output)).replace("\\", "/"): digest(path)
                for path in sorted(args.output.rglob("*"))
                if path.is_file()
            },
            "native_processes_started": 0,
            "sealed_intents_generated": 0,
        },
    )
    return {
        "passed": True,
        "protocol_sha256": wanted,
        "recipe_sha256": digest(args.output / "Recipe01.json"),
        "packet_manifest_sha256": digest(args.output / "PacketManifest01.json"),
        "native_processes_started": 0,
        "sealed_inputs_read": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--research-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--guest-packet", required=True)
    parser.add_argument("--guest-private-root", required=True)
    print(json.dumps(freeze(parser.parse_args()), sort_keys=True))


if __name__ == "__main__":
    main()
