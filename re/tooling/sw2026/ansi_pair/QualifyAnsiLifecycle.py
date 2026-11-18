from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def checked(root, row):
    relative = Path(row["path"])
    require(
        not relative.is_absolute() and ".." not in relative.parts,
        "ANSI host input escapes its packet",
    )
    path = root / relative
    require(
        not path.is_symlink()
        and path.resolve(strict=True).is_relative_to(root.resolve())
        and path.stat().st_size == row["bytes"]
        and digest(path) == row["sha256"],
        "ANSI host artifact changed",
    )
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("packet", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--native-result-sha256", required=True)
    parser.add_argument("--qualifier-sha256", required=True)
    args = parser.parse_args()
    require(
        digest(Path(__file__)) == args.qualifier_sha256, "ANSI host qualifier differs"
    )
    manifest_path = args.candidate / "SourceManifest.json"
    require(
        digest(manifest_path) == args.manifest_sha256, "ANSI source manifest differs"
    )
    manifest = json.loads(manifest_path.read_bytes())
    code = (args.candidate / "CodeRoot").resolve(strict=True)
    for row in manifest["files"]:
        checked(code, row)
    require(digest(args.packet) == args.packet_sha256, "ANSI native packet differs")
    packet = json.loads(args.packet.read_bytes())
    require(
        packet["schema"] == "kit.sw2026.ansi-pair-native-lifecycle-packet.v1"
        and packet["source_manifest_sha256"] == args.manifest_sha256,
        "ANSI native/source packet identities differ",
    )
    root = args.packet.parent.resolve(strict=True)
    for row in [
        *packet["tools"].values(),
        *packet["host_tools"].values(),
        *packet["custody"],
        packet["control"],
    ]:
        checked(root, row)
    native_path = root / "Inspection/Result.json"
    require(
        digest(native_path) == args.native_result_sha256, "ANSI native result differs"
    )
    native = json.loads(native_path.read_bytes())
    require(
        native["packet_sha256"] == args.packet_sha256
        and native["passed"] is True
        and native["controls_healthy"] is True
        and native["distinct_native_processes"] == 18,
        "ANSI native phases or controls are incomplete",
    )
    sys.path[:0] = [str(code / "src"), str(code)]
    import dataclasses
    import dis
    import inspect

    sys.path.append(str(code / "re/tooling/sw2026"))
    from ansi_pair.Readback import fields
    from ansi_style.JsonDifference import difference
    from spatial_text.QualifySpatialTextLifecycle import typed_join

    args.output.mkdir(exist_ok=False, parents=True)
    result = {
        "schema": "kit.sw2026.ansi-native-typed-qualification.v1",
        "source_manifest_sha256": args.manifest_sha256,
        "packet_sha256": args.packet_sha256,
        "native_result_sha256": args.native_result_sha256,
        "qualifier_sha256": args.qualifier_sha256,
        "cases": [],
        "passed": False,
        "native_acceptance": False,
        "heldout_acceptance": False,
        "source_original_admission": False,
    }
    for case in packet["cases"]:
        initial = [
            (
                "constructed",
                checked(root, case["files"]["drawing"]),
                checked(root, case["files"]["child"]),
                None,
            )
        ]
        for phase in ("open-save", "reopen", "edit-move-save", "reopen-edited"):
            state = native["phases"][case["name"] + "/" + phase]
            require(state["passed"] is True, "ANSI native phase did not pass")
            require(
                digest(root / "Inspection" / case["name"] / phase / "Record.json")
                == state["record_sha256"],
                "ANSI native phase record changed",
            )
            draw = {
                **state["drawing_file"],
                "path": state["drawing_file"]["relative_path"],
            }
            child = {
                **state["child_file"],
                "path": state["child_file"]["relative_path"],
            }
            initial.append(
                (phase, checked(root, draw), checked(root, child), state["saved"])
            )
        expected = json.loads(checked(root, case["expected_presentation"]).read_bytes())
        for phase, drawing, child, observation in initial:
            row = typed_join(root, drawing, child, case, phase, observation)
            try:
                _, _, actual = fields(
                    child.read_bytes(),
                    drawing.read_bytes(),
                    case["view"]["orientation"],
                    case["style_mode"],
                )
                changes = difference(expected, actual)
                row.update(
                    style_mode=case["style_mode"],
                    actual_matching_ui_owners=True,
                    actual_detail_selectors=True,
                    complete_presentation=actual,
                    presentation_changes=changes,
                    complete_style_state_preserved=not changes,
                )
                row["passed"] = bool(row["passed"] and not changes)
            except Exception as error:
                row.update(
                    passed=False,
                    style_exception=type(error).__name__,
                    style_diagnostic=str(error),
                )
            result["cases"].append(row)
    result["passed"] = len(result["cases"]) == 20 and all(
        row["passed"] for row in result["cases"]
    )
    result["native_geometry_lifecycle_passed"] = True
    result["complete_style_retention_passed"] = all(
        row.get("complete_style_state_preserved") for row in result["cases"]
    )
    with (args.output / "Result.json").open("x", encoding="utf-8") as stream:
        json.dump(
            result,
            stream,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        stream.write("\n")
    print(
        json.dumps(
            {
                "passed": result["passed"],
                "typed_joins": len(result["cases"]),
                "complete_style_retention_passed": result[
                    "complete_style_retention_passed"
                ],
            }
        )
    )
    return 0 if result["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
