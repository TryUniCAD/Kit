from __future__ import annotations

import argparse
from base64 import b64decode
from hashlib import sha256
import json
from pathlib import Path
from shutil import copyfile
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(value):
    return sha256(value).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def read_checked(root, row):
    relative = Path(row["path"])
    path = root / relative
    require(not relative.is_absolute() and ".." not in relative.parts and not path.is_symlink()
            and path.resolve(strict=True).is_relative_to(root.resolve()), "deck source escaped its declared root")
    value = path.read_bytes()
    require(len(value) == row["bytes"] and digest(value) == row["sha256"], "deck source bytes changed: " + str(relative))
    return value


def copy_new(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(value)
    return {"path": name, "bytes": len(value), "sha256": digest(value)}


def drawing_tree(job, document):
    options, support = job["native"]["options"], job["support_names"]
    folders, names = options["folder_names"], options["sheet_names"]
    sheet = document.Sheets[0]
    view = sheet.Views[0]
    return [[folders["comments"], "CommentsFolder", None], [folders["blocks"], "BlockFolder", None],
            [folders["binder"], "DocsFolder", None], [folders["annotations"], "DetailCabinet", None],
            [folders["ink_markups"], "InkMarkupFolder", None], [folders["review_markups"], "MarkupCommentFolder", None],
            [sheet.EntityName, "DrSheet", None], [names["plane_name"], "RefPlane", sheet.EntityName],
            [names["profile_name"], "ProfileFeature", sheet.EntityName], [names["detail_name"], "DetailFolder", sheet.EntityName],
            [view.EntityName, "AbsoluteView", sheet.EntityName], [support["detail"], "DetailFolder", view.EntityName],
            [support["sheet_plane"], "RefPlane", view.EntityName], [support["sheet_profile"], "ProfileFeature", view.EntityName],
            [support["model_plane"], "RefPlane", view.EntityName], [support["model_profile"], "ProfileFeature", view.EntityName]]


def main():
    parser = argparse.ArgumentParser(description="Prepare an unused native epoch packet only after frozen guarded composition and independent readback pass")
    parser.add_argument("candidate", type=Path)
    parser.add_argument("process_root", type=Path)
    parser.add_argument("oracle_base", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-manifest-sha256", required=True)
    parser.add_argument("--process-result-sha256", required=True)
    parser.add_argument("--host-tools-manifest-sha256", required=True)
    args = parser.parse_args()
    tool_root = Path(__file__).resolve().parent
    tool_raw = (tool_root / "HostToolsManifest.json").read_bytes()
    require(digest(tool_raw) == args.host_tools_manifest_sha256, "epoch host tools manifest differs")
    tool_manifest = json.loads(tool_raw)
    require(args.source_manifest_sha256 == tool_manifest["required_source_manifest_sha256"]
            and args.process_result_sha256 == tool_manifest["required_process_result_sha256"],
            "this host deck is frozen to a different independently checked source or process result")
    for row in tool_manifest["files"]:
        read_checked(tool_root, row)
    manifest_raw = (args.candidate / "SourceManifest.json").read_bytes()
    require(digest(manifest_raw) == args.source_manifest_sha256, "epoch writer source manifest differs")
    manifest = json.loads(manifest_raw)
    code = (args.candidate / "CodeRoot").resolve(strict=True)
    for row in manifest["files"]:
        read_checked(code, row)
    require(len(manifest["files"]) == manifest["file_count"] and manifest["all_base_source_files_unchanged"] is True,
            "epoch writer base source custody differs")
    require({row["path"] for row in manifest["files"]}
            == {str(path.relative_to(code)) for path in code.rglob("*") if path.is_file()},
            "epoch writer source has undeclared files")
    result_raw = (args.process_root / "Result.json").read_bytes()
    require(digest(result_raw) == args.process_result_sha256, "epoch process result differs")
    result = json.loads(result_raw)
    require(result["schema"] == "kit.sw2026.sdk-epoch-flow.v1" and result["passed"] is True
            and result["native_deck_ready_for_review"] is True and result["process_count"] == 26
            and result["source_manifest_sha256"] == args.source_manifest_sha256
            and len(result["cases"]) == 4 and all(value["passed"] for value in result["cases"])
            and len(result["negative_cases"]) == 8 and all(value["rejected"] for value in result["negative_cases"])
            and len(result["published_refusals"]) == 2 and all(value["passed"] for value in result["published_refusals"]),
            "epoch factory and independent readback have not completed")
    oracle_raw = (args.oracle_base / "Packet.json").read_bytes()
    require(digest(oracle_raw) == "862adb0519afd892aa690ce7b4e283a33de95cdf3bcdc71be465498244118842",
            "use the exact prior controlled ordinary lifecycle packet")
    oracle = json.loads(oracle_raw)
    old_case = oracle["cases"][0]
    old_request_row = next(row for row in oracle["custody"] if row["path"] == "Provenance/" + old_case["name"] + ".Request.json")
    old_request = json.loads(read_checked(args.oracle_base, old_request_row))
    require(not args.output.exists(), "epoch native packet output must be unused")
    args.output.mkdir(parents=True)
    custody = [copy_new(args.output, "Provenance/SourceManifest.json", manifest_raw),
               copy_new(args.output, "Provenance/ProcessResult.json", result_raw),
               copy_new(args.output, "Provenance/ProbePlan.json", (args.candidate / "ProbePlan.json").read_bytes()),
               copy_new(args.output, "Provenance/HostToolsManifest.json", tool_raw)]
    spec_raw = (code / "re/tooling/sw2026/EpochExperimentSpec01.json").read_bytes()
    spec = json.loads(spec_raw)
    require(digest(spec_raw) == result["spec_sha256"] == manifest["spec_sha256"], "epoch modeled input spec differs")
    custody.append(copy_new(args.output, "Provenance/EpochExperimentSpec01.json", spec_raw))
    tools = {name: copy_new(args.output, "Tools/" + name, read_checked(args.oracle_base, row))
             for name, row in oracle["tools"].items()}
    host_tools = {"InspectEpochClocks.py": copy_new(args.output, "HostTools/InspectEpochClocks.py",
                                                    (tool_root / "InspectEpochClocks.py").read_bytes())}
    control = copy_new(args.output, "Control.SLDPRT", read_checked(args.oracle_base, oracle["control"]))
    sys.path[:0] = [str(code / "src"), str(code)]
    from interchange.serialization.Deserialize import FromData
    cases = []
    for case in result["cases"]:
        prefix = case["builds"][0]["artifact_prefix"]
        request_raw = (args.process_root / (prefix + ".Request.json")).read_bytes()
        build_raw = (args.process_root / (prefix + ".stdout.json")).read_bytes()
        require(digest(request_raw) == case["builds"][0]["request_sha256"]
                and digest(build_raw) == case["builds"][0]["stdout_sha256"], "epoch case capture differs")
        request, build = json.loads(request_raw), json.loads(build_raw)
        job = request["origin_request"]
        require(request["case"] == case["name"] == build["case"] and build["passed"] is True,
                "epoch native case source identities differ")
        current_system = job["part"]["settings"]["system"]
        old_system = old_request["part"]["settings"]["system"]
        require(all(current_system[key] == old_system[key] for key in
                    ("folders", "planes", "cabinet_name", "origin_name", "origin_axis", "construction_flag")),
                "prior native default tree prediction does not describe these unchanged system inputs")
        neutral = build["child_neutral"]
        remap = {old_case["sketch_name"]: neutral["sketch_name"], old_case["boss_name"]: neutral["feature_name"]}
        tree = [[remap.get(name, name), kind, remap.get(parent, parent)] for name, kind, parent in old_case["part_tree"]]
        document = FromData(job["drawing_document"])
        sheet, view = document.Sheets[0], document.Sheets[0].Views[0]
        files = {}
        for kind, basename in (("child", "EpochPart.SLDPRT"), ("drawing", "EpochDrawing.SLDDRW")):
            value = b64decode(build[kind + "_base64"], validate=True)
            require(len(value) == build[kind + "_bytes"] and digest(value) == build[kind + "_sha256"]
                    and value == read_checked(args.process_root, case["files"][kind]), "epoch generated artifact differs")
            files[kind] = copy_new(args.output, "Generated/" + case["name"] + "/" + basename, value)
        for record in (*case["builds"], case["default_constructor"], case["preparation"]):
            for suffix, field in ((".Request.json", "request_sha256"), (".stdout.json", "stdout_sha256"), (".stderr.txt", "stderr_sha256")):
                name = record["artifact_prefix"] + suffix
                raw = (args.process_root / name).read_bytes()
                require(digest(raw) == record[field], "epoch prospective worker custody differs")
                custody.append(copy_new(args.output, "Provenance/" + name, raw))
        settings = job["part"]["settings"]
        width_name, height_name = neutral["driver_names"]
        cases.append({"name": case["name"], "kind": "corner", "files": files,
                      "paths": {"child": build["native_child_path"], "drawing": build["native_drawing_path"]},
                      "part": {key: spec["neutral_geometry"][key] for key in ("width_m", "height_m", "depth_m")},
                      "view": {"name": view.EntityName, "orientation": build["orientation"],
                               "position_m": build["view_position_m"], "scale": spec["drawing"]["scale"]},
                      "sheet": {"name": sheet.EntityName, "width_m": sheet.SheetWidth,
                                "height_m": sheet.SheetHeight, "scale_ratio": list(sheet.ScaleRatio)},
                      "configuration": neutral["configuration_name"], "sketch_name": neutral["sketch_name"],
                      "boss_name": neutral["feature_name"], "origin_name": current_system["origin_name"],
                      "part_tree": tree, "drawing_tree": drawing_tree(job, document),
                      "density_kg_m3": settings["density_kg_m3"], "generated_profile": build["profile"],
                      "parameter_names": [width_name + "@" + neutral["sketch_name"], height_name + "@" + neutral["sketch_name"],
                                          neutral["depth_name"] + "@" + neutral["feature_name"]],
                      "edit": {"field": "depth_m", "parameter": neutral["depth_name"] + "@" + neutral["feature_name"],
                               "value_m": spec["neutral_geometry"]["depth_m"] + spec["native_phases"]["driving_depth_delta_m"],
                               "view_move_m": spec["native_phases"]["view_move_delta_m"]},
                      "constructor_source": {"request_sha256": digest(request_raw), "build_sha256": digest(build_raw)},
                      "clock_plan": request["clock_plan"], "drawing_clock_plan": request["drawing_clock_plan"],
                      "changed_clock_axis": request["changed_axis"]})
    for record in (*result["published_refusals"], *result["negative_cases"]):
        for suffix, field in ((".Request.json", "request_sha256"), (".stdout.json", "stdout_sha256"), (".stderr.txt", "stderr_sha256")):
            name = record["artifact_prefix"] + suffix
            raw = (args.process_root / name).read_bytes()
            require(digest(raw) == record[field], "epoch negative process custody differs")
            custody.append(copy_new(args.output, "Provenance/" + name, raw))
    packet = {"schema": oracle["schema"], "revision": 1, "oracle_sha256": oracle["oracle_sha256"],
              "tools": tools, "host_tools": host_tools, "control": control, "custody": custody, "cases": cases,
              "source_manifest_sha256": args.source_manifest_sha256, "root_process_result_sha256": args.process_result_sha256,
              "controls_bracket_all_candidates": True, "process_count": 18, "immutable_packet_inputs": True,
              "hidden_inputs_read": 0, "hidden_source_cohort_unsealing_authorized": False,
              "native_acceptance": False, "heldout_acceptance": False, "public_drawing_writer_enabled": False,
              "typed_origin_join_required_after_native": True, "typed_clock_observation_required_after_native": True,
              "clock_expectations": spec["expected_observations"], "clock_attribution_limits": spec["attribution_limits"],
              "prior_native_packet_sha256": digest(oracle_raw),
              "default_tree_basis": "the prior independent ordinary-family oracle prediction, with unchanged system inputs checked; actual neutral sketch and boss names substituted only in observer expectations",
              "projection_policy": oracle["projection_policy"], "clock_expansion_qualified": False}
    packet_row = copy_new(args.output, "Packet.json", encode(packet))
    print(json.dumps({"prepared": True, "packet": packet_row, "source_manifest_sha256": args.source_manifest_sha256,
                      "native_execution_performed": False, "native_acceptance": False}))


if __name__ == "__main__":
    raise SystemExit(main())
