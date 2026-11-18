from __future__ import annotations

import sys
from pathlib import Path

sys.path[:] = [
    value
    for value in sys.path
    if Path(value or ".").resolve() != Path(__file__).resolve().parent
]

import argparse
from dataclasses import replace
import hashlib
import json


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify_code(candidate, expected):
    path = candidate / "SourceManifest.json"
    if digest(path.read_bytes()) != expected:
        raise ValueError("frozen source manifest differs")
    manifest = json.loads(path.read_bytes())
    for row in manifest["files"]:
        data = (candidate / "CodeRoot" / row["path"]).read_bytes()
        if digest(data) != row["sha256"] or len(data) != row["bytes"]:
            raise ValueError("frozen source changed: " + row["path"])
    return manifest


def signed_word(value):
    value &= 0xFFFFFFFF
    return value if value < (1 << 31) else value - (1 << 32)


def manager(counter, count=0, rows=()):
    return {
        "f08": signed_word(counter),
        "f0c": signed_word(counter >> 32),
        "list": {"n": count, "items": list(rows)},
    }


def main():
    parser = argparse.ArgumentParser(
        description="Exercise empty appearance admission through actual generated drawing Definition read and write components"
    )
    parser.add_argument("candidate", type=Path)
    parser.add_argument("generated_drawing", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--generated-sha256", required=True)
    parser.add_argument("--orientation", required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("result output must be unused")
    manifest = verify_code(args.candidate, args.manifest_sha256)
    sys.path[:0] = [
        str(args.candidate / "CodeRoot/src"),
        str(args.candidate / "CodeRoot"),
    ]
    from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import (
        BodyUnsupported,
    )
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Drawing.Definition.Appearance.ReadAppearState import (
        ReadAppearState,
    )
    from convert.adapters.solidworks.Drawing.Definition.Named.ReadNamedDef import (
        ReadNamedDef,
    )
    from convert.adapters.solidworks.Drawing.Definition.Named.WriteNamedDef import (
        WriteNamedDef,
    )

    input_data = args.generated_drawing.read_bytes()
    if digest(input_data) != args.generated_sha256:
        raise ValueError("pinned generated drawing changed")
    data = SldprtArchive.from_bytes(input_data).require("Contents/Definition")
    baseline = ReadNamedDef(data, 19000, args.orientation)
    if WriteNamedDef(baseline.GraphValue).OutputValue != data:
        raise ValueError("qualified generated baseline does not round trip")
    result = {
        "schema": "kit.sw2026.empty-drawing-appearance-process.v1",
        "source_manifest_sha256": args.manifest_sha256,
        "source_files": manifest["file_count"],
        "runner_sha256": digest(Path(__file__).read_bytes()),
        "generated_input_sha256": args.generated_sha256,
        "generated_definition_sha256": digest(data),
        "orientation": args.orientation,
        "input_provenance": "caller pinned SDK generated neutral drawing; no native vendor fixture added",
        "baseline_byte_identical": True,
        "positive_cases": [],
        "negative_cases": [],
        "native_execution": False,
        "vm_access": False,
        "native_acceptance": False,
        "heldout_acceptance": False,
        "public_writer_enabled": False,
    }
    for counter in (1, 0x100000002, 0x8000000100000003, 0xFFFFFFFFFFFFFFFF):
        read = ReadNamedDef(data, 19000, args.orientation)
        document = read.GraphValue.DocumentValue
        document.FieldsValue["has_pwmaterial"] = 1
        document.FieldsValue["f1110"] = manager(counter)
        written = WriteNamedDef(read.GraphValue)
        reread = ReadNamedDef(written.OutputValue, 19000, args.orientation)
        state = ReadAppearState(reread.GraphValue.DocumentValue, 19000)
        second = WriteNamedDef(reread.GraphValue)
        retained = reread.GraphValue.DocumentValue.FieldsValue["f1110"]
        passed = (
            state.ManagerOnWire is True
            and state.NextAppearanceId == counter
            and second.OutputValue == written.OutputValue
            and retained["f08"] == signed_word(counter)
            and retained["f0c"] == signed_word(counter >> 32)
        )
        result["positive_cases"].append(
            {
                "next_appearance_id": counter,
                "low_word": signed_word(counter),
                "high_word": signed_word(counter >> 32),
                "output_bytes": len(written.OutputValue),
                "output_sha256": digest(written.OutputValue),
                "counter_and_raw_fields_retained": passed,
                "passed": passed,
            }
        )

    scenarios = [
        ("negative count", {"n": -1, "items": []}),
        ("minimum signed count", {"n": -(1 << 31), "items": []}),
        ("positive count without rows", {"n": 1, "items": []}),
        ("populated null row", {"n": 1, "items": [{"o": None}]}),
        ("zero count with a row", {"n": 0, "items": [{"o": None}]}),
        ("untyped row container", {"n": 0, "items": {}}),
        ("floating count", {"n": 0.0, "items": []}),
        ("boolean count", {"n": False, "items": []}),
    ]
    for name, refs in scenarios:
        read = ReadNamedDef(data, 19000, args.orientation)
        document = read.GraphValue.DocumentValue
        document.FieldsValue["has_pwmaterial"] = 1
        value = manager(1)
        value["list"] = refs
        document.FieldsValue["f1110"] = value
        try:
            WriteNamedDef(read.GraphValue)
        except (BodyUnsupported, ValueError, TypeError, KeyError) as error:
            result["negative_cases"].append(
                {
                    "case": name,
                    "rejected": True,
                    "exception": type(error).__name__,
                    "message": str(error),
                    "result_returned": False,
                }
            )
        else:
            result["negative_cases"].append(
                {"case": name, "rejected": False, "result_returned": True}
            )

    for name, field, value in [
        ("low word overflow", "f08", 1 << 31),
        ("high word underflow", "f0c", -(1 << 31) - 1),
        ("untyped low word", "f08", "1"),
        ("untyped high word", "f0c", None),
    ]:
        read = ReadNamedDef(data, 19000, args.orientation)
        document = read.GraphValue.DocumentValue
        document.FieldsValue["has_pwmaterial"] = 1
        state = manager(1)
        state[field] = value
        document.FieldsValue["f1110"] = state
        try:
            WriteNamedDef(read.GraphValue)
        except (BodyUnsupported, ValueError, TypeError, KeyError) as error:
            result["negative_cases"].append(
                {
                    "case": name,
                    "rejected": True,
                    "exception": type(error).__name__,
                    "message": str(error),
                    "result_returned": False,
                }
            )
        else:
            result["negative_cases"].append(
                {"case": name, "rejected": False, "result_returned": True}
            )

    for name in ("other presence", "footer remains closed", "legacy remains closed"):
        read = ReadNamedDef(data, 19000, args.orientation)
        graph = read.GraphValue
        if name == "other presence":
            graph.DocumentValue.FieldsValue["has_pwmaterial"] = 2
            graph.DocumentValue.FieldsValue["f1110"] = manager(1)
        elif name == "footer remains closed":
            graph.DocumentValue.FieldsValue["drawing_end_marker"] = 3504
        else:
            graph = replace(graph, VersionValue=18999)
        try:
            WriteNamedDef(graph)
        except (BodyUnsupported, ValueError, TypeError, KeyError) as error:
            result["negative_cases"].append(
                {
                    "case": name,
                    "rejected": True,
                    "exception": type(error).__name__,
                    "message": str(error),
                    "result_returned": False,
                }
            )
        else:
            result["negative_cases"].append(
                {"case": name, "rejected": False, "result_returned": True}
            )
    _ = verify_code(args.candidate, args.manifest_sha256)
    result["source_immutable"] = True
    result["input_unchanged"] = (
        digest(args.generated_drawing.read_bytes()) == args.generated_sha256
    )
    result["passed"] = (
        result["input_unchanged"]
        and all(row["passed"] for row in result["positive_cases"])
        and all(
            row["rejected"] and not row["result_returned"]
            for row in result["negative_cases"]
        )
    )
    payload = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(payload)
    print(
        json.dumps(
            {
                "passed": result["passed"],
                "positive_cases": len(result["positive_cases"]),
                "negative_cases": len(result["negative_cases"]),
                "report_sha256": digest(args.output.read_bytes()),
                "native_acceptance": False,
                "heldout_acceptance": False,
            }
        )
    )
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
