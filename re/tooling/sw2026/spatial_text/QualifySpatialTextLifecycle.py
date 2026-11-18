from __future__ import annotations

import argparse
from hashlib import sha256
import json
from math import isfinite
from ntpath import normcase, normpath
from pathlib import Path
import sys


def require(condition, diagnostic):
    if not condition:
        raise ValueError(diagnostic)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def same_number(actual, expected):
    return abs(actual) <= 1e-12 if expected == 0.0 else format(actual, ".6g") == format(expected, ".6g")


def checked(root, row):
    relative = Path(row["path"])
    require(not relative.is_absolute() and ".." not in relative.parts, "spatial text host path must be packet-contained")
    path = root / relative
    require(not path.is_symlink() and path.resolve(strict=True).is_relative_to(root.resolve())
            and path.stat().st_size == row["bytes"] and digest(path) == row["sha256"],
            "spatial text host artifact custody differs")
    return path


def verify_source(candidate, expected):
    manifest = candidate / "SourceManifest.json"
    require(not manifest.is_symlink() and digest(manifest) == expected, "spatial text host source manifest differs")
    value = json.loads(manifest.read_bytes())
    require(value["schema"] == "kit.sw2026.spatial-text-source-closure.v1", "spatial text host source family differs")
    root = (candidate / "CodeRoot").resolve(strict=True)
    names = set()
    for row in value["files"]:
        relative = Path(row["path"])
        require(not relative.is_absolute() and ".." not in relative.parts and row["path"] not in names,
                "spatial text source membership differs")
        checked(root, row)
        names.add(row["path"])
    require(len(names) == value["file_count"], "spatial text source count differs")
    return root, value


def typed_join(root, drawing_path, child_path, case, phase, native):
    from SpatialTextMut import concrete, text_rows
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
    from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, FieldText
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Drawing.Definition.Named.ReadNamedDef import ReadNamedDef
    from convert.adapters.solidworks.Drawing.Definition.Named.WriteNamedDef import WriteNamedDef
    from convert.adapters.solidworks.Drawing.Definition.Profiles.ReadAllProfiles import ReadAllProfiles

    row = {"case": case["name"], "phase": phase, "passed": False,
           "drawing_sha256": digest(drawing_path), "child_sha256": digest(child_path)}
    try:
        drawing_archive = SldprtArchive.from_bytes(drawing_path.read_bytes())
        child_archive = SldprtArchive.from_bytes(child_path.read_bytes())
        drawing = ReadNamedDef(drawing_archive.require("Contents/Definition"), 19000, case["view"]["orientation"])
        child = ReadNativeLink(child_archive, 0)
        manager = ReadCmgrMut(child_archive.require("Contents/CMgr"), 19000)
        require(WriteNamedDef(drawing.GraphValue).OutputValue == drawing_archive.require("Contents/Definition"),
                "spatial text native full Definition replay differs")
        cfg_bytes, cfg = WriteConfigMut(child.ConfigValue.RootValue, 19000, child.ConfigValue.HeaderValue)
        resolved_bytes, _ = WriteResolMut(child.ResolvedValue.RootsValue, child.ResolvedValue.ExtraFields,
                                           19000, cfg.MapValue, child.ResolvedValue.ContextValue)
        require(cfg_bytes == child_archive.require("Contents/Config-0")
                and resolved_bytes == child_archive.require("Contents/Config-0-ResolvedFeatures")
                and WriteCmgrMut(manager.RootValue, 19000) == child_archive.require("Contents/CMgr"),
                "spatial text native complete child graph replay differs")
        roots = [node for node in child.ResolvedValue.RootsValue if node is not None]
        profiles = [node for node in roots if node.ClassValue.NameValue == "moProfileFeature_c"]
        origins = [node for node in roots if node.ClassValue.NameValue == "moOriginProfileFeature_c"]
        require(len(profiles) == len(origins) == 1, "spatial text native child profile identity is ambiguous")
        profile = concrete(profiles[0], "moProfileFeature_c")
        origin = concrete(origins[0], "moOriginProfileFeature_c")
        actual = text_rows(profile)
        row["stored_text_points"] = actual
        row["expected_authored_text_points"] = case["text_after"]
        row["edited_planar_text_coordinates_are_observed_only"] = phase in ("edit-move-save", "reopen-edited")
        for observed, expected in zip(actual, case["text_after"], strict=True):
            require(observed["value_id"] == expected["value_id"] and observed["annotation_id"] == expected["annotation_id"],
                    "spatial text native dimension/display persistent identity changed")
            require(all(type(value) is float and isfinite(value) for value in observed["xyz_m"]),
                    "spatial text native stored coordinate is not finite")
            require(same_number(observed["xyz_m"][2], expected["xyz_m"][2]),
                    "spatial text native saved normal coordinate differs from explicit authored input")
            if phase not in ("edit-move-save", "reopen-edited"):
                require(all(same_number(a, b) for a, b in zip(observed["xyz_m"], expected["xyz_m"], strict=True)),
                        "spatial text native unedited stored point differs from explicit authored input")
        items = tuple(item for group in ReadAllProfiles(drawing.GraphValue.DocumentValue, 19000) for item in group.ItemsValue)
        require(len(items) == 1, "spatial text native drawing has another displayed profile")
        item = items[0]
        wrapper = concrete(item.ReferenceValue, "moCompProfile_c")
        drawing_model = concrete(drawing.GraphValue.DocumentValue.FieldsValue["model"], "moDrawing_c")
        reference = concrete(item.ViewValue.FieldsValue["f5d8"], "moReferenceInternal_c")
        origin_id = FieldInt(origin.FieldsValue, "f08")
        origin_time = DatumTime(child.ConfigValue.HeaderValue, origin_id)
        require(wrapper.FieldsValue["ff0"] == {"f00": origin_id, "f08": origin_time}
                and FieldInt(profile.FieldsValue, "f08") != origin_id,
                "spatial text native drawing selected another actual child profile or creation event")
        chain = concrete(wrapper.FieldsValue["f58"], "moChainComponent_c")
        refs = concrete(chain.FieldsValue["f20"], "moReferenceChain_c")
        entries = concrete(refs.FieldsValue["f08"], "moExtFeatureList_c")
        require(entries.FieldsValue["n"] == len(entries.FieldsValue["f08"]) == 1,
                "spatial text native drawing has another actual external component path")
        external = concrete(entries.FieldsValue["f08"][0]["o"], "moExtFeature_c")
        require(chain.FieldsValue["owner"] is drawing_model and external is reference.FieldsValue["f4f8"]
                and external.FieldsValue["f50"] is reference,
                "spatial text native actual external reference aliases differ")
        require(item.DisplayValue.FieldsValue["f40"] is item.ViewValue
                and item.DisplayValue.FieldsValue["f30"] is item.FolderValue
                and item.DisplayValue.FieldsValue["f48"] is wrapper,
                "spatial text native display folder/view/reference aliases differ")
        own = concrete(child.ConfigValue.HeaderValue.FieldsValue["f38"], "moExtObject_c")
        declared = concrete(reference.FieldsValue["f3b0"], "moExtObject_c")
        own_key, declared_key = ReadFileKey(own), ReadFileKey(declared)
        require(own_key == declared_key and own_key[2] == 2
                and normcase(normpath(own_key[1])) == normcase(normpath(case["paths"]["child"])),
                "spatial text native drawing resolves a different actual child file identity")
        config = concrete(manager.RootValue.FieldsValue["f360"], "moPartConfiguration_c")
        require(config is manager.RootValue.FieldsValue["f368"], "spatial text native manager selection aliases differ")
        config_name = FieldText(concrete(config.FieldsValue["f18"], "moNodeName_c").FieldsValue, "f08")
        config_id = FieldInt(config.FieldsValue, "f08")
        for selector in (reference.FieldsValue["f3c0"], own.FieldsValue["refcfg"]):
            require(FieldText(selector, "f08") == config_name == case["configuration"]
                    and FieldInt(selector, "f10") == config_id,
                    "spatial text native selected child configuration differs")
        if native is not None:
            require(native["child"]["profile_ids"] == {"origin": origin_id, "ordinary_profile": FieldInt(profile.FieldsValue, "f08")},
                    "spatial text native API profile IDs differ from actual typed child owners")
            row["annotation_api_coordinates"] = native["child"]["annotation_coordinates"]
        row.update(passed=True, complete_definition_byte_identity=True, complete_child_byte_identity=True,
                   actual_child_file_alias=True, actual_configuration_selection=True,
                   actual_origin_profile_link={"id": origin_id, "creation_time": origin_time},
                   actual_display_folder_view_aliases=True, stored_normal_coordinate_preserved=True,
                   annotation_api_position_is_stored_text_point=False,
                   independent_manager_reader_base=1,
                   independent_manager_first_entry=min(value.IndexValue for value in manager.MapValue.EntriesValue))
    except Exception as error:
        row.update(exception=type(error).__name__, diagnostic=str(error))
    return row


def main():
    parser = argparse.ArgumentParser(description="Join signed text-depth lifecycle snapshots through the exact shared SDK and actual origin/component/configuration owners")
    parser.add_argument("candidate", type=Path)
    parser.add_argument("packet", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--native-result-sha256", required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "spatial text host proof directory must be unused")
    source_root, source_manifest = verify_source(args.candidate, args.manifest_sha256)
    require(digest(args.packet) == args.packet_sha256, "spatial text native packet differs")
    packet = json.loads(args.packet.read_bytes())
    root = args.packet.parent.resolve(strict=True)
    require(packet["schema"] == "kit.sw2026.spatial-text-native-lifecycle-packet.v1"
            and packet["source_manifest_sha256"] == args.manifest_sha256
            and Path(__file__).resolve().parent == root / "HostTools", "spatial text host method scope differs")
    for row in [*packet["tools"].values(), *packet["host_tools"].values(), *packet["custody"], packet["control"]]:
        checked(root, row)
    native_path = root / "Inspection/Result.json"
    require(digest(native_path) == args.native_result_sha256, "spatial text native result custody differs")
    native = json.loads(native_path.read_bytes())
    require(native["packet_sha256"] == args.packet_sha256 and native["passed"] is True
            and native["controls_healthy"] is True and native["distinct_native_processes"] == 10,
            "spatial text native lifecycle or controls are incomplete")
    sys.path[:0] = [str(source_root / "src"), str(source_root)]
    import dataclasses
    import dis
    import inspect
    sys.path.append(str(source_root / "re/tooling/sw2026"))
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"schema": "kit.sw2026.spatial-text-native-typed-join.v1", "source_manifest_sha256": args.manifest_sha256,
              "source_file_count": source_manifest["file_count"], "packet_sha256": args.packet_sha256,
              "native_result_sha256": args.native_result_sha256, "cases": [], "passed": False,
              "native_acceptance": False, "heldout_acceptance": False, "source_original_admission": False,
              "hidden_inputs_read": 0, "public_drawing_writer_changed": False}
    for case in packet["cases"]:
        draw = checked(root, case["files"]["drawing"])
        child = checked(root, case["files"]["child"])
        report["cases"].append(typed_join(root, draw, child, case, "constructed", None))
        for phase in ("open-save", "reopen", "edit-move-save", "reopen-edited"):
            state = native["phases"][case["name"] + "/" + phase]
            require(state["passed"] is True, "spatial text native phase did not pass")
            record = root / "Inspection" / case["name"] / phase / "Record.json"
            require(digest(record) == state["record_sha256"], "spatial text native phase record changed")
            draw_row = {**state["drawing_file"], "path": state["drawing_file"]["relative_path"]}
            child_row = {**state["child_file"], "path": state["child_file"]["relative_path"]}
            report["cases"].append(typed_join(root, checked(root, draw_row), checked(root, child_row), case, phase, state["saved"]))
    report["passed"] = len(report["cases"]) == 10 and all(row["passed"] for row in report["cases"])
    with (args.output / "Result.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"passed": report["passed"], "typed_joins": len(report["cases"]), "native_acceptance": False}))
    return 0 if report["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
