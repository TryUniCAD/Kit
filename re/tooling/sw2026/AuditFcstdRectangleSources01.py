from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

CASES = ("C059-P01", "C130-P01")
SOURCE_HASHES = (
    "73cd885cd4755b274fe1106db3022923352ea45a7a4d9964d48202790a47de61",
    "d1f9225bfdf31d9708fc8fc8f94261edc9479d01d6a09c720ae70c16a5aa2362",
)
CODE = "24b090548c73c8745636c5be3888d9268f2ca6ec5473ada762213e1e1df248be"
MODES = {
    "C059-P01": (
        "positive",
        "repeat",
        "stale_width",
        "missing_origin",
        "unknown_reference",
        "ambiguous_alias",
    ),
    "C130-P01": (
        "positive",
        "repeat",
        "stale_width",
        "foreign_owner",
        "reordered_profile",
    ),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def publish(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )


def mutate(document, mode):
    from interchange import CadDocument, Expression
    from FcstdRectangleOwners01 import require

    if mode in ("positive", "repeat"):
        return document
    parameters = list(document.parameters)
    sketch = document.sketches[0]
    if mode == "stale_width":
        index = next(
            index
            for index, value in enumerate(parameters)
            if value.id == sketch.parameter_ids[0]
        )
        parameters[index] = replace(
            parameters[index],
            value=replace(
                parameters[index].value, value=parameters[index].value.value + 1
            ),
        )
        return replace(document, parameters=tuple(parameters))
    if mode == "foreign_owner":
        index = next(
            index
            for index, value in enumerate(parameters)
            if value.attributes.get("freecad_path") == "Length"
        )
        parameters[index] = replace(parameters[index], owner_id=sketch.id)
        return replace(document, parameters=tuple(parameters))
    if mode == "reordered_profile":
        return replace(
            document,
            sketches=(
                replace(
                    sketch,
                    closed_profile_entity_ids=(
                        sketch.closed_profile_entity_ids[0][::-1],
                    ),
                ),
            ),
        )
    data = json.loads(document.to_json())
    if mode == "missing_origin":
        rule = data["sketches"]["$tuple"][0]["constraints"]["$tuple"][8]
        rule["attributes"]["freecad_reference_slots"][1][
            "freecad_geometry_index"
        ] = -2000
        return CadDocument.from_json(json.dumps(data))
    if mode == "ambiguous_alias":
        sheet = next(
            value
            for value in data["metadata"]["freecad"]["objects"]
            if value["type_id"] == "Spreadsheet::Sheet"
        )
        rows = sheet["properties"]["cells"]["children"][0]["children"]
        duplicate = json.loads(
            json.dumps(
                next(
                    value for value in rows if value.get("attributes", {}).get("alias")
                )
            )
        )
        duplicate["attributes"]["address"] = "C1"
        rows.append(duplicate)
        return CadDocument.from_json(json.dumps(data))
    require(mode == "unknown_reference", "unsupported source-refusal mutation")
    index = next(
        index for index, value in enumerate(parameters) if value.expression is not None
    )
    parameters[index] = replace(
        parameters[index],
        expression=Expression("Dimensions.unknown", language="freecad"),
    )
    return replace(document, parameters=tuple(parameters))


def property_roles(document):
    from FcstdRectangleOwners01 import plain

    roles = {
        "AllowMultiFace": "authored operation setting; current one-profile shape does not qualify lossless target preservation",
        "AlongSketchNormal": "active direction mode flag",
        "Label": "authored feature label",
        "Label2": "secondary presentation label",
        "Length": "active depth driver or dependency target",
        "Length2": "inactive second-direction value retained despite absent second end condition",
        "Midplane": "active termination mode flag",
        "Offset": "stored offset value retained",
        "Refine": "authored topology refinement option",
        "Reversed": "active direction flag",
        "TaperAngle": "stored forward draft driver",
        "TaperAngle2": "inactive second-direction draft value",
        "Type": "active termination enumeration",
        "UseCustomVector": "active direction-selection mode flag",
        "Visibility": "presentation visibility",
    }
    result = []
    for value in document.parameters:
        path = value.attributes.get("freecad_path", "")
        role = (
            "actual sketch dimensional constraint"
            if path.startswith("Constraints[")
            else roles.get(path)
        )
        if role is None:
            raise ValueError("unclassified actual source parameter path")
        result.append(
            {
                "id": value.id,
                "name": value.name,
                "actual_owner_id": value.owner_id,
                "source_path": path,
                "declared_portable_role": str(value.role),
                "classified_source_role": role,
                "value": plain(value.value),
                "expression": plain(value.expression),
                "attributes": plain(value.attributes),
                "target_preservation_qualified": False,
            }
        )
    return result


def worker(request_path, expected, output):
    if digest(request_path) != expected:
        raise ValueError("the source audit request changed")
    request = json.loads(request_path.read_bytes())
    if (
        request["case_id"] not in CASES
        or request["source_sha256"] != SOURCE_HASHES[CASES.index(request["case_id"])]
    ):
        raise ValueError(
            "the source audit is restricted to the two disclosed exact identities"
        )
    sys.path.insert(0, str(Path(request["code_root"]) / "src"))
    from convert import open_document
    from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
    from convert.Geometry.Opencascade import DecodeAsciiBrep
    from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
        PrincipalFrame,
    )
    from FcstdRectangleOwners01 import (
        canonical,
        constraint_owners,
        dependency_plan,
        factory_drivers,
        plain,
        point,
        rectangular_source_measure,
        require,
        source_profile,
        topology_compare,
        value_quantity,
    )

    source = Path(request["source_path"])
    allowed = {
        os.path.normcase(os.path.abspath(source)),
        os.path.normcase(os.path.realpath(source)),
    }
    activity = {
        "stage": "source_read",
        "cad_file_reads": 0,
        "constructor_cad_reads": 0,
        "foreign_cad_reads": 0,
        "cad_imports": 0,
        "nested_processes": 0,
    }

    def audit(event, args):
        if (
            event == "import"
            and args
            and str(args[0]).split(".")[0]
            in ("FreeCAD", "Part", "pythoncom", "win32com")
        ):
            activity["cad_imports"] += 1
            raise RuntimeError(
                "CAD runtime imports are outside this pure SDK source audit"
            )
        if event == "subprocess.Popen":
            activity["nested_processes"] += 1
            raise RuntimeError(
                "nested external execution is outside this source worker"
            )
        if (
            event != "open"
            or not args
            or not isinstance(args[0], (str, bytes, os.PathLike))
        ):
            return
        raw = os.fsdecode(args[0])
        if Path(raw).suffix.casefold() not in (
            ".fcstd",
            ".sldprt",
            ".sldasm",
            ".slddrw",
            ".f3d",
            ".f3z",
        ):
            return
        mode = args[1] if len(args) > 1 else None
        flags = args[2] if len(args) > 2 and type(args[2]) is int else 0
        reading = (
            isinstance(mode, str)
            and ("r" in mode or "+" in mode)
            or mode is None
            and flags & os.O_ACCMODE == os.O_RDONLY
        )
        if not reading:
            raise RuntimeError("source CAD writes are outside this audit")
        activity["cad_file_reads"] += 1
        if activity["stage"] == "construct":
            activity["constructor_cad_reads"] += 1
            raise RuntimeError("analytic construction must not read native files")
        if os.path.normcase(os.path.abspath(raw)) not in allowed:
            activity["foreign_cad_reads"] += 1
            raise RuntimeError("an undeclared CAD file was requested")

    sys.addaudithook(audit)
    require(
        digest(source) == request["source_sha256"],
        "the actual disclosed source bytes changed",
    )
    document = open_document(
        source, strict=True, include_brep=True, include_tessellation=True
    )
    require(
        not document.validate(), "the whole original strict source document is invalid"
    )
    original_json = document.to_json(indent=2) + "\n"
    require(
        hashlib.sha256(original_json.encode()).hexdigest() == request["neutral_sha256"],
        "the whole source-neutral read differs from the frozen pre-fix census",
    )
    document = mutate(document, request["mode"])
    before = document.to_json()
    result = {
        "schema": "kit.sw2026.fcstd-rectangle-source-owner-audit.v1",
        "case_id": request["case_id"],
        "mode": request["mode"],
        "source_sha256": request["source_sha256"],
        "original_neutral_sha256": request["neutral_sha256"],
        "writer_output_count": 0,
        "native_acceptance": False,
        "whole_fcstd_conversion_qualified": False,
        "explicit_negative_input_mutation": request["mode"]
        not in ("positive", "repeat"),
    }
    output.mkdir(parents=True, exist_ok=False)
    try:
        require(
            document.units == "mm",
            "this measured source member needs its actual millimetre geometry domain",
        )
        sketch, feature, body, plane = source_profile(document)
        dependencies = dependency_plan(document)
        rules = constraint_owners(sketch)
        drivers = factory_drivers(document)
        depth, dimension = value_quantity(feature.definition.length)
        require(dimension == (1, 0), "active Pad depth is not a length")
        activity["stage"] = "construct"
        generated, volume, area, bounds = BuildPrism(
            body.id,
            plane.transform,
            tuple(value.geometry for value in sketch.entities),
            0.0,
            depth,
        )
        activity["stage"] = "source_geometry_validation"
        refs = body.attributes.get("brep_payload_ids")
        require(
            isinstance(refs, (list, tuple)) and len(refs) == 1,
            "the actual body has an ambiguous source B-rep owner",
        )
        (payload,) = [value for value in document.brep_payloads if value.id == refs[0]]
        native = DecodeAsciiBrep(
            payload.data, IdPrefix="source-check", DesignBodyId=body.id
        )
        topology = topology_compare(native, generated, body.id)
        actual = rectangular_source_measure(native)
        require(
            abs(volume - actual["volume_mm3"]) <= 1e-9
            and abs(area - actual["area_mm2"]) <= 1e-9,
            "model-generated analytic prism disagrees with the complete source boundary",
        )
        require(
            all(
                abs(value - want) <= 1e-9
                for value, want in zip(
                    (
                        (low + high) / 2
                        for low, high in zip(
                            point(bounds.minimum), point(bounds.maximum), strict=True
                        )
                    ),
                    actual["center_mm"],
                    strict=True,
                )
            ),
            "independently generated centroid differs from the source boundary",
        )
        planes = []
        for datum in document.support_planes:
            frame = datum.transform
            candidates = []
            for axis, role in (("z", "Front"), ("y", "Top"), ("x", "Right")):
                native_frame = PrincipalFrame(axis)
                if tuple(
                    (
                        point(frame.origin),
                        point(frame.x_axis),
                        point(frame.y_axis),
                        point(frame.z_axis),
                    )
                ) == (
                    native_frame.OriginValue,
                    native_frame.AxisU,
                    native_frame.AxisV,
                    native_frame.NormalValue,
                ):
                    candidates.append(role)
            require(
                len(candidates) == 1,
                "actual source datum has no unique shared native principal-frame role",
            )
            planes.append(
                {
                    "id": datum.id,
                    "source_name": datum.name,
                    "actual_transform": plain(frame),
                    "native_system_role": candidates[0],
                    "authored_name_must_survive": True,
                    "native_output_emitted": False,
                }
            )
        envelope = {
            "schema": "kit.sw2026.fcstd-source-owner-envelope.v1",
            "original_full_document_sha256": request["neutral_sha256"],
            "evidence_only_not_a_converted_document": True,
            "document_with_payload_fingerprints_only": plain(document),
            "dependencies": plain(dependencies),
            "constraint_owners": plain(rules),
            "parameter_roles": property_roles(document),
            "support_datums": planes,
            "factory_driver_owners": plain(drivers),
        }
        publish(output / "SourceEnvelope.Private.json", envelope)
        publish(
            output / "GeneratedAnalyticBrep.json",
            {
                "schema": "kit.sw2026.analytic-brep-evidence.v1",
                "model": plain(generated),
                "native_output": False,
                "source_saved_payload_used_in_construction": False,
            },
        )
        result.update(
            source_owner_projection_passed=True,
            dependency_count=len(dependencies.expressions),
            dependency_bindings_complete_in_original=dependencies.typed_dependency_bindings_complete,
            source_body_payload_sha256=hashlib.sha256(payload.data).hexdigest(),
            source_body_payload_bytes=len(payload.data),
            topology=topology,
            source_measure=actual,
            generated_measure={"volume_mm3": volume, "area_mm2": area},
            owner_counts={
                "parameters": len(document.parameters),
                "features": len(document.feature_timeline),
                "sketches": len(document.sketches),
                "constraints": len(sketch.constraints),
                "entities": len(sketch.entities),
                "support_planes": len(document.support_planes),
                "bodies": len(document.bodies),
                "payloads_retained_by_fingerprint": len(document.brep_payloads),
                "source_objects": len(document.metadata["freecad"]["objects"]),
            },
            actual_names={
                "body": body.name,
                "sketch": sketch.name,
                "feature": feature.name,
                "drivers": [
                    value.name
                    for value in document.parameters
                    if value.id in sketch.parameter_ids
                    or value.attributes.get("freecad_path") == "Length"
                ],
            },
            dependencies=plain(dependencies.expressions),
            factory_driver_owners=plain(drivers),
            source_envelope_sha256=digest(output / "SourceEnvelope.Private.json"),
            generated_analytic_brep_sha256=digest(
                output / "GeneratedAnalyticBrep.json"
            ),
            native_generation_refusals=[
                "populated native equation ownership unqualified",
                "original portable dependency IDs empty",
                "all seventeen source parameter properties and inactive values need actual target owners",
                "eleven explicit source constraints are not the seven-row qualified shared-point rectangle",
                "source metadata, three axis objects, chronology and presentation are retained but not natively lowered",
                "whole source envelope must not be stripped",
            ]
            + (
                [
                    "source spreadsheet cells, alias, text and sheet state are not natively lowered"
                ]
                if any(
                    value["type_id"] == "Spreadsheet::Sheet"
                    for value in document.metadata["freecad"]["objects"]
                )
                else []
            )
            + (
                [
                    "historical reader maps hidden source sketch to suppressed; root correction is a separate revision"
                ]
                if sketch.suppressed
                else []
            ),
        )
    except Exception as error:
        result.update(
            source_owner_projection_passed=False,
            refusal={
                "type": type(error).__name__,
                "message": str(error).replace(str(source), "<source>"),
            },
        )
    activity["stage"] = "final_source_identity"
    result["source_bytes_unchanged"] = digest(source) == request["source_sha256"]
    result["neutral_unchanged_by_projection"] = document.to_json() == before
    result["activity"] = activity
    result["expected_outcome_met"] = (
        result["source_owner_projection_passed"]
        == (request["mode"] in ("positive", "repeat"))
        and result["source_bytes_unchanged"]
        and result["neutral_unchanged_by_projection"]
        and activity["constructor_cad_reads"]
        == activity["foreign_cad_reads"]
        == activity["cad_imports"]
        == activity["nested_processes"]
        == 0
    )
    publish(output / "Result.json", result)
    print(
        json.dumps(
            {
                "case_id": request["case_id"],
                "mode": request["mode"],
                "expected_outcome_met": result["expected_outcome_met"],
                "projection_passed": result["source_owner_projection_passed"],
                "result_sha256": digest(output / "Result.json"),
                "writer_output_count": 0,
            },
            sort_keys=True,
        )
    )
    return 0 if result["expected_outcome_met"] else 2


def run(args):
    require_unused = not args.output.exists()
    if not require_unused or digest(args.census / "CodeManifest01.json") != CODE:
        raise ValueError("use the exact frozen census and an unused source audit root")
    manifest = json.loads((args.census / "CodeManifest01.json").read_bytes())
    for relative, record in manifest["files"].items():
        current = args.census / "CodeRoot" / relative
        if (
            digest(current) != record["sha256"]
            or current.stat().st_size != record["bytes"]
        ):
            raise ValueError("the frozen SDK source closure changed")
    roster = json.loads((args.census / "VerifiedInputs01.json").read_bytes())
    args.output.mkdir(parents=True)
    (args.output / "Tools").mkdir()
    for name in ("AuditFcstdRectangleSources01.py", "FcstdRectangleOwners01.py"):
        shutil.copyfile(
            Path(__file__).resolve().parent / name, args.output / "Tools" / name
        )
    tools = {
        path.name: digest(path) for path in sorted((args.output / "Tools").glob("*.py"))
    }
    method = {
        "schema": "kit.sw2026.fcstd-rectangle-source-method.v1",
        "sdk_manifest_sha256": CODE,
        "source_inventory_sha256": roster["inventory_sha256"],
        "source_case_ids": list(CASES),
        "tools_sha256": tools,
        "modes": MODES,
        "source_path_policy": "actual original path from the verified disclosed inventory",
        "writer_output_count": 0,
        "native_calls": 0,
    }
    publish(args.output / "Method01.json", method)
    results = []
    for case, source_sha in zip(CASES, SOURCE_HASHES, strict=True):
        (row,) = [value for value in roster["files"] if value["case_id"] == case]
        if row["sha256"] != source_sha:
            raise ValueError("the two disclosed source fingerprints differ")
        neutral = args.census / "Cases" / case / "Neutral.json"
        for mode in MODES[case]:
            request = {
                "case_id": case,
                "source_path": row["source_path"],
                "source_sha256": source_sha,
                "neutral_sha256": digest(neutral),
                "mode": mode,
                "code_root": str(args.census / "CodeRoot"),
            }
            request_file = (
                args.output / "Requests.Private" / (case + "-" + mode + ".json")
            )
            publish(request_file, request)
            target = args.output / "Results" / (case + "-" + mode)
            command = [
                sys.executable,
                "-B",
                str(args.output / "Tools/AuditFcstdRectangleSources01.py"),
                "worker",
                "--request",
                str(request_file),
                "--sha256",
                digest(request_file),
                "--output",
                str(target),
            ]
            completed = subprocess.run(
                command, capture_output=True, text=True, timeout=120
            )
            publish(
                args.output / "Transport" / (case + "-" + mode + ".json"),
                {
                    "exit_code": completed.returncode,
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                },
            )
            if completed.returncode != 0:
                raise RuntimeError(
                    "source audit process failed for " + case + "-" + mode
                )
            results.append(json.loads((target / "Result.json").read_bytes()))
    positive = [row for row in results if row["mode"] == "positive"]
    for case in CASES:
        (first,) = [
            row
            for row in results
            if row["case_id"] == case and row["mode"] == "positive"
        ]
        (second,) = [
            row for row in results if row["case_id"] == case and row["mode"] == "repeat"
        ]
        if (
            first["source_envelope_sha256"] != second["source_envelope_sha256"]
            or first["generated_analytic_brep_sha256"]
            != second["generated_analytic_brep_sha256"]
        ):
            raise ValueError("independent source owner replays diverged")
    summary = {
        "schema": "kit.sw2026.fcstd-rectangle-source-summary.v1",
        "passed": all(row["expected_outcome_met"] for row in results),
        "sdk_manifest_sha256": CODE,
        "method_sha256": digest(args.output / "Method01.json"),
        "sdk_processes": len(results),
        "positive_processes": 4,
        "refusal_processes": len(results) - 4,
        "source_case_ids": list(CASES),
        "positive_observations": positive,
        "refusals": [
            {
                "case_id": row["case_id"],
                "mode": row["mode"],
                "refusal": row.get("refusal"),
            }
            for row in results
            if row["explicit_negative_input_mutation"]
        ],
        "writer_output_count": 0,
        "native_acceptance": False,
        "whole_fcstd_conversion_qualified": False,
        "native_calls": 0,
    }
    publish(args.output / "Summary01.json", summary)
    print(
        json.dumps(
            {
                "passed": summary["passed"],
                "sdk_processes": len(results),
                "summary_sha256": digest(args.output / "Summary01.json"),
                "writer_output_count": 0,
            },
            sort_keys=True,
        )
    )


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    audit = commands.add_parser("run")
    audit.add_argument("--census", type=Path, required=True)
    audit.add_argument("--output", type=Path, required=True)
    child = commands.add_parser("worker")
    child.add_argument("--request", type=Path, required=True)
    child.add_argument("--sha256", required=True)
    child.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "run":
        run(args)
        return 0
    return worker(args.request, args.sha256, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
