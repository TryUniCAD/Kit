from __future__ import annotations

import argparse
from base64 import b64decode
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath


def digest(data):
    return sha256(data).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def item(root, path, data):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as stream:
        stream.write(data)
    return {"path": path, "bytes": len(data), "sha256": digest(data)}


def one(value):
    require(
        type(value) is dict
        and set(value) == {"$tuple"}
        and type(value["$tuple"]) is list
        and len(value["$tuple"]) == 1,
        "native prediction needs exactly one declared neutral row",
    )
    return value["$tuple"][0]


def part_tree(job, sketch, boss):
    system = job["part"]["settings"]["system"]
    labels = dict(system["folders"])
    result = [
        [labels[name], kind, None]
        for name, kind in (
            ("moCommentsFolder_c", "CommentsFolder"),
            ("moFavoriteFolder_c", "FavoriteFolder"),
            ("moHistoryFolder_c", "HistoryFolder"),
            ("moSelectionSetFolder_c", "SelectionSetFolder"),
            ("moSensorFolder_c", "SensorFolder"),
            ("moDocsFolder_c", "DocsFolder"),
        )
    ]
    cabinet, environment = system["cabinet_name"], labels["moEnvFolder_c"]
    result.extend(
        [
            [cabinet, "DetailCabinet", None],
            ["Notes", "NotesAreaFtrFolder", cabinet],
            ["Notes1___EndTag___", "NotesAreaFtrFolder", cabinet],
            [labels["moSurfaceBodyFolder_c"], "SurfaceBodyFolder", None],
            [labels["moSolidBodyFolder_c"], "SolidBodyFolder", None],
            [environment, "EnvFolder", None],
            ["Ambient", "AmbientLight", environment],
            *[
                ["Directional" + str(i), "DirectionLight", environment]
                for i in range(1, 4)
            ],
            [labels["moInkMarkupFolder_c"], "InkMarkupFolder", None],
            [labels["moEqnFolder_c"], "EqnFolder", None],
            [labels["moMaterialFolder_c"], "MaterialFolder", None],
        ]
    )
    result.extend(
        [[system["planes"][key], "RefPlane", None] for key in ("z", "y", "x")]
    )
    result.extend(
        [
            [system["origin_name"], "OriginProfileFeature", None],
            [sketch, "ProfileFeature", None],
            [boss, "Extrusion", None],
        ]
    )
    return result


def drawing_tree(job, sheet, view):
    options, support = job["native"]["options"], job["support_names"]
    folders, names = options["folder_names"], options["sheet_names"]
    return [
        [folders[key], kind, None]
        for key, kind in (
            ("comments", "CommentsFolder"),
            ("blocks", "BlockFolder"),
            ("binder", "DocsFolder"),
            ("annotations", "DetailCabinet"),
            ("ink_markups", "InkMarkupFolder"),
            ("review_markups", "MarkupCommentFolder"),
        )
    ] + [
        [sheet["name"], "DrSheet", None],
        [names["plane_name"], "RefPlane", sheet["name"]],
        [names["profile_name"], "ProfileFeature", sheet["name"]],
        [names["detail_name"], "DetailFolder", sheet["name"]],
        [view["name"], "AbsoluteView", sheet["name"]],
        [support["detail"], "DetailFolder", view["name"]],
        [support["sheet_plane"], "RefPlane", view["name"]],
        [support["sheet_profile"], "ProfileFeature", view["name"]],
        [support["model_plane"], "RefPlane", view["name"]],
        [support["model_profile"], "ProfileFeature", view["name"]],
    ]


def checked(root, row):
    relative = Path(row["path"])
    require(
        not relative.is_absolute() and ".." not in relative.parts,
        "packet input escapes its source",
    )
    path = root / relative
    require(
        not path.is_symlink()
        and path.resolve(strict=True).is_relative_to(root.resolve())
        and path.stat().st_size == row["bytes"]
        and digest(path.read_bytes()) == row["sha256"],
        "frozen input changed: " + row["path"],
    )
    return path


def model_lengths(parameters):
    require(
        [row["id"] for row in parameters]
        == ["parameter/width", "parameter/height", "parameter/depth"],
        "packet needs the three independently authored rectangle drivers",
    )
    values = []
    for row in parameters:
        value = row["value"]
        require(
            value["$type"] == "ParameterValue"
            and value["unit"] == "mm"
            and value["kind"] == {"$enum": "ValueKind", "value": "length"}
            and type(value["value"]) in (int, float)
            and value["value"] > 0,
            "native prediction needs an actual positive authored millimetre length",
        )
        values.append(value["value"] / 1000.0)
    return values


def main():
    parser = argparse.ArgumentParser(
        description="Prepare a data-only, strict native initialization experiment packet"
    )
    parser.add_argument("candidate", type=Path)
    parser.add_argument("proof", type=Path)
    parser.add_argument("observer_packet", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-manifest-sha256", required=True)
    parser.add_argument("--process-result-sha256", required=True)
    parser.add_argument("--observer-packet-sha256", required=True)
    args = parser.parse_args()
    manifest_raw = (args.candidate / "SourceManifest.json").read_bytes()
    result_raw = (args.proof / "Result.json").read_bytes()
    observer_raw = (args.observer_packet / "Packet.json").read_bytes()
    require(
        digest(manifest_raw) == args.source_manifest_sha256
        and digest(result_raw) == args.process_result_sha256
        and digest(observer_raw) == args.observer_packet_sha256,
        "source, host result or previously measured observer packet differs",
    )
    manifest, result, observer = (
        json.loads(value) for value in (manifest_raw, result_raw, observer_raw)
    )
    require(
        manifest["base_commit"] == "f393c3bdc84a630f82f0b4c52ba67b05967ccaea"
        and result["passed"] is True
        and result["source_manifest_sha256"] == args.source_manifest_sha256
        and len(result["cases"]) == 8
        and len(result["comparisons"]) == 4
        and len(result["rejections"]) == 8
        and observer["schema"] == "kit.sw2026.ansi-pair-native-lifecycle-packet.v1"
        and observer["complete_style_retention_required"] is True,
        "initialization source/host/observer scope differs",
    )
    code = args.candidate / "CodeRoot"
    for row in manifest["files"]:
        checked(code, row)
    args.output.mkdir(parents=True, exist_ok=False)
    custody = [
        item(args.output, "Provenance/SourceManifest.json", manifest_raw),
        item(args.output, "Provenance/ProcessResult.json", result_raw),
        item(args.output, "Provenance/PreviousObserverPacket.json", observer_raw),
        item(args.output, "Provenance/PrepareNative.py", Path(__file__).read_bytes()),
    ]
    control_raw = checked(args.observer_packet, observer["control"]).read_bytes()
    require(
        digest(control_raw)
        == "c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57",
        "wrong control",
    )
    control = item(args.output, "Control.SLDPRT", control_raw)
    tools = {
        name: item(
            args.output,
            "Tools/" + name,
            checked(args.observer_packet, row).read_bytes(),
        )
        for name, row in observer["tools"].items()
    }
    host_tools = {
        name: item(
            args.output,
            "HostTools/" + name,
            checked(args.observer_packet, row).read_bytes(),
        )
        for name, row in observer["host_tools"].items()
    }
    cases, targets = [], set()
    for entry in result["cases"]:
        if entry["initialization"] != "document-units":
            continue
        request_raw = (
            args.proof / (entry["name"] + "Build0.Request.json")
        ).read_bytes()
        build_raw = (args.proof / (entry["name"] + "Build0.stdout.json")).read_bytes()
        require(
            digest(request_raw) == entry["builds"][0]["request_sha256"]
            and digest(build_raw) == entry["builds"][0]["stdout_sha256"],
            "case source custody differs",
        )
        request, build = json.loads(request_raw), json.loads(build_raw)
        require(
            request["initialization"] == build["initialization"] == "document-units"
            and build["passed"] is True
            and build["runtime_input_file_access_attempts"] == 0
            and build["sdk_research_imports"] == [],
            "case is not a complete guarded generated pair",
        )
        job = request["origin_request"]
        sheet = one(job["drawing_document"]["sheets"])
        view = one(sheet["views"])
        sketch = one(job["part"]["document"]["sketches"])
        boss = one(job["part"]["document"]["feature_timeline"])
        parameters = job["part"]["document"]["parameters"]["$tuple"]
        width, height, depth = model_lengths(parameters)
        files = {}
        paths = {
            kind: build["native_" + kind + "_path"] for kind in ("child", "drawing")
        }
        for kind, suffix in (("child", ".SLDPRT"), ("drawing", ".SLDDRW")):
            raw = b64decode(build[kind + "_base64"], validate=True)
            require(
                len(raw) == build[kind + "_bytes"]
                and digest(raw) == entry[kind + "_sha256"],
                "generated bytes differ from the exact host result",
            )
            target = PureWindowsPath(paths[kind])
            require(
                target.is_absolute()
                and target.drive.upper() == "C:"
                and target.suffix.upper() == suffix
                and ".." not in target.parts
                and target.parts[1] == "KitAnsiNormalized01"
                and str(target).casefold() not in targets,
                "native targets must be distinct exact authored experiment paths",
            )
            targets.add(str(target).casefold())
            files[kind] = item(
                args.output,
                "Generated/" + entry["name"] + "/" + kind.title() + suffix,
                raw,
            )
        for suffix, raw in (("Request.json", request_raw), ("Build.json", build_raw)):
            custody.append(
                item(args.output, "Provenance/" + entry["name"] + suffix, raw)
            )
        expected = json.dumps(
            build["presentation"],
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        ).encode()
        expected_row = item(
            args.output, "Expected/" + entry["name"] + "Presentation.json", expected
        )
        custody.append(expected_row)
        corner = job["child_policy"]["kind"] == "corner-anchored"
        parameter_names = [
            row["name"] + "@" + (sketch["name"] if index < 2 else boss["name"])
            for index, row in enumerate(parameters)
        ]
        edit_index = 0 if corner else 1
        cases.append(
            {
                "name": entry["name"],
                "style_mode": entry["mode"],
                "kind": "corner" if corner else "center",
                "paths": paths,
                "files": files,
                "constructor_source": args.source_manifest_sha256,
                "part": {"width_m": width, "height_m": height, "depth_m": depth},
                "sheet": {
                    "name": sheet["name"],
                    "width_m": sheet["width"],
                    "height_m": sheet["height"],
                    "scale_ratio": sheet["scale_ratio"]["$tuple"],
                },
                "view": {
                    "name": view["name"],
                    "orientation": view["orientation_name"],
                    "scale": view["scale_ratio"]["$tuple"][0]
                    / view["scale_ratio"]["$tuple"][1],
                    "position_m": [view["position"]["x"], view["position"]["y"]],
                },
                "configuration": view["configuration_name"],
                "density_kg_m3": job["part"]["settings"]["density_kg_m3"],
                "sketch_name": sketch["name"],
                "boss_name": boss["name"],
                "origin_name": job["part"]["settings"]["system"]["origin_name"],
                "parameter_names": parameter_names,
                "part_tree": part_tree(job, sketch["name"], boss["name"]),
                "drawing_tree": drawing_tree(job, sheet, view),
                "text_after": build["text_after"],
                "generated_profile": build["profile"],
                "expected_presentation": expected_row,
                "document_precision": entry["precision"],
                "analysis_precision": job["part"]["settings"]["analysis_units"][
                    "decimal_places"
                ],
                "exclusion_names": job["part"]["settings"]["styles"]["exclusion_names"],
                "edit": {
                    "field": "width_m" if corner else "height_m",
                    "parameter": parameter_names[edit_index],
                    "value_m": (width if corner else height)
                    + (0.005423 if corner else 0.004317),
                    "view_move_m": [0.002371, -0.001129],
                },
            }
        )
    require(
        len(cases) == 4
        and len(targets) == 8
        and [case["style_mode"] for case in cases] == ["iso", "ansi", "iso", "ansi"],
        "native cases, targets or bracketing sequence differ",
    )
    packet = {
        "schema": "kit.sw2026.ansi-pair-native-lifecycle-packet.v1",
        "experiment": "document-style-initialization",
        "base_commit": manifest["base_commit"],
        "source_manifest_sha256": args.source_manifest_sha256,
        "process_result_sha256": args.process_result_sha256,
        "previous_observer_packet_sha256": args.observer_packet_sha256,
        "oracle_sha256": observer["oracle_sha256"],
        "control": control,
        "tools": tools,
        "host_tools": host_tools,
        "custody": custody,
        "cases": cases,
        "expected_native_processes": 18,
        "expected_text_depths_m": [0.0, 0.0, 0.0, 0.0],
        "complete_style_retention_required": True,
        "ansi_drawing_f20_exemption": False,
        "hidden_inputs_read": 0,
        "native_acceptance": False,
        "heldout_acceptance": False,
        "source_original_admission": False,
        "public_drawing_writer_changed": False,
        "guest_target_existence_checked": False,
    }
    raw = (
        json.dumps(
            packet, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False
        )
        + "\n"
    ).encode()
    row = item(args.output, "Packet.json", raw)
    print(
        json.dumps(
            {
                "packet": str(args.output / "Packet.json"),
                "sha256": row["sha256"],
                "files": sum(1 for path in args.output.rglob("*") if path.is_file()),
                "native_processes": 18,
                "vendor_processes_started": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
