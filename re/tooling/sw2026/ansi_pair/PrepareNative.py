from __future__ import annotations

import argparse
from base64 import b64decode
from hashlib import sha256
import json
from pathlib import Path


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("proof", type=Path)
    parser.add_argument("publication", type=Path)
    parser.add_argument("control", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-manifest-sha256", required=True)
    parser.add_argument("--process-result-sha256", required=True)
    args = parser.parse_args()
    manifest_raw = (args.candidate / "SourceManifest.json").read_bytes()
    result_raw = (args.proof / "Result.json").read_bytes()
    require(
        digest(manifest_raw) == args.source_manifest_sha256
        and digest(result_raw) == args.process_result_sha256,
        "ANSI source or process proof differs",
    )
    manifest, result = json.loads(manifest_raw), json.loads(result_raw)
    require(
        result["passed"] is True
        and result["source_manifest_sha256"] == args.source_manifest_sha256
        and len(result["cases"]) == 8
        and len(result["rejections"]) == 6,
        "ANSI guarded cohort is incomplete",
    )
    code = args.candidate / "CodeRoot"
    for row in manifest["files"]:
        data = (code / row["path"]).read_bytes()
        require(
            len(data) == row["bytes"] and digest(data) == row["sha256"],
            "ANSI frozen source changed",
        )
    control_raw = args.control.read_bytes()
    require(
        digest(control_raw)
        == "c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57",
        "ANSI native control differs",
    )
    args.output.mkdir(parents=True, exist_ok=False)
    custody = [
        item(args.output, "Provenance/SourceManifest.json", manifest_raw),
        item(args.output, "Provenance/ProcessResult.json", result_raw),
    ]
    control = item(args.output, "Control.SLDPRT", control_raw)
    tools = {}
    names = (
        "InspectAnsiDrawingLifecycle.py",
        "SpatialTextNativeObserve.py",
        "OriginNativeObserve.py",
        "OriginNativePredict.py",
        "AuthorCurves.py",
        "AuthorDrawingSources.py",
        "AuthorRectangleAnchors.py",
        "InspectFresh.py",
        "OracleIdentity.py",
        "Swapp.py",
    )
    for name in names:
        source = (
            args.publication / "re/tooling/sw2026" / name
            if name == names[0]
            else code / "re/tooling/sw2026" / name
        )
        tools[name] = item(args.output, "Tools/" + name, source.read_bytes())
    qualifier = args.publication / "re/tooling/sw2026/ansi_pair/QualifyAnsiLifecycle.py"
    host_tools = {
        "QualifyAnsiLifecycle.py": item(
            args.output, "HostTools/QualifyAnsiLifecycle.py", qualifier.read_bytes()
        )
    }
    custody.append(
        item(args.output, "Provenance/PrepareNative.py", Path(__file__).read_bytes())
    )
    cases = []
    for entry in result["cases"]:
        if entry["scope"] != "Native":
            continue
        request_raw = (args.proof / entry["request_file"]).read_bytes()
        build_raw = (args.proof / entry["result_file"]).read_bytes()
        require(
            digest(request_raw) == entry["builds"][0]["request_sha256"]
            and digest(build_raw) == entry["builds"][0]["stdout_sha256"],
            "ANSI case inputs or output differ",
        )
        request, build = json.loads(request_raw), json.loads(build_raw)
        job, design = request["origin_request"], entry["design"]
        sheet = one(job["drawing_document"]["sheets"])
        view = one(sheet["views"])
        sketch = one(job["part"]["document"]["sketches"])
        boss = one(job["part"]["document"]["feature_timeline"])
        parameters = job["part"]["document"]["parameters"]["$tuple"]
        require(
            [row["id"] for row in parameters]
            == ["parameter/width", "parameter/height", "parameter/depth"],
            "ANSI driver ownership is outside the declared family",
        )
        files = {}
        for kind, suffix in (("child", ".SLDPRT"), ("drawing", ".SLDDRW")):
            data = b64decode(build[kind + "_base64"], validate=True)
            require(
                len(data) == build[kind + "_bytes"]
                and digest(data) == entry[kind + "_sha256"],
                "ANSI generated bytes differ",
            )
            files[kind] = item(
                args.output,
                "Generated/" + entry["name"] + "/" + kind.title() + suffix,
                data,
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
        is_corner = job["child_policy"]["kind"] == "corner-anchored"
        index = 0 if is_corner else 1
        edit_value = design[1 + index] + (0.005423 if is_corner else 0.004317)
        parameter_names = [
            parameters[i]["name"] + "@" + (sketch["name"] if i < 2 else boss["name"])
            for i in range(3)
        ]
        cases.append(
            {
                "name": entry["name"],
                "style_mode": entry["mode"],
                "kind": "corner" if is_corner else "center",
                "paths": entry["paths"],
                "files": files,
                "constructor_source": args.source_manifest_sha256,
                "part": {
                    "width_m": design[1],
                    "height_m": design[2],
                    "depth_m": design[3],
                },
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
                "edit": {
                    "field": "width_m" if is_corner else "height_m",
                    "parameter": parameter_names[index],
                    "value_m": edit_value,
                    "view_move_m": [0.002371, -0.001129],
                },
            }
        )
    require(
        len(cases) == 4
        and [c["style_mode"] for c in cases] == ["iso", "ansi", "iso", "ansi"],
        "ANSI native control order differs",
    )
    packet = {
        "schema": "kit.sw2026.ansi-pair-native-lifecycle-packet.v1",
        "source_manifest_sha256": args.source_manifest_sha256,
        "process_result_sha256": args.process_result_sha256,
        "base_commit": manifest["base_commit"],
        "oracle_sha256": "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe",
        "control": control,
        "tools": tools,
        "host_tools": host_tools,
        "custody": custody,
        "cases": cases,
        "expected_text_depths_m": [0.0, 0.0, 0.0, 0.0],
        "expected_native_processes": 18,
        "hidden_inputs_read": 0,
        "native_acceptance": False,
        "heldout_acceptance": False,
        "source_original_admission": False,
        "public_drawing_writer_changed": False,
        "complete_style_retention_required": True,
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
                "files": sum(1 for p in args.output.rglob("*") if p.is_file()),
                "native_processes": 18,
            }
        )
    )


if __name__ == "__main__":
    main()
