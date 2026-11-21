from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(value):
    return sha256(value).hexdigest()


def checked(root, row):
    relative = Path(row.get("relative_path", row.get("path", "")))
    path = root / relative
    require(not relative.is_absolute() and ".." not in relative.parts and not path.is_symlink()
            and path.resolve(strict=True).is_relative_to(root.resolve()), "epoch observation file escaped its packet")
    raw = path.read_bytes()
    require(len(raw) == row["bytes"] and digest(raw) == row["sha256"], "epoch observation custody differs")
    return raw


def main():
    parser = argparse.ArgumentParser(description="Read actual archived clock owners after a completed ordinary native lifecycle; no CAD calls")
    parser.add_argument("packet", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--source-manifest-sha256", required=True)
    parser.add_argument("--native-result-sha256", required=True)
    args = parser.parse_args()
    root = args.packet.parent.resolve(strict=True)
    packet_raw = args.packet.read_bytes()
    require(digest(packet_raw) == args.packet_sha256, "epoch native packet differs")
    packet = json.loads(packet_raw)
    own = packet["host_tools"]["InspectEpochClocks.py"]
    require(Path(__file__).resolve() == root / own["path"] and checked(root, own) == Path(__file__).read_bytes(),
            "use the exact packet-bound clock observation tool")
    manifest_raw = (args.candidate / "SourceManifest.json").read_bytes()
    require(digest(manifest_raw) == args.source_manifest_sha256 == packet["source_manifest_sha256"],
            "clock observation must use the exact qualified SDK source")
    code = (args.candidate / "CodeRoot").resolve(strict=True)
    manifest = json.loads(manifest_raw)
    for row in manifest["files"]:
        checked(code, row)
    require({row["path"] for row in manifest["files"]}
            == {str(path.relative_to(code)) for path in code.rglob("*") if path.is_file()},
            "epoch observation source has undeclared files")
    native_raw = (root / "Inspection/Result.json").read_bytes()
    require(digest(native_raw) == args.native_result_sha256, "native result changed before clock observation")
    native = json.loads(native_raw)
    require(native["packet_sha256"] == args.packet_sha256 and native["controls_healthy"] is True
            and native["native_lifecycle_passed"] is True and native["distinct_native_processes"] == 18,
            "clock observation has no completed controlled native batch")
    require(not args.output.exists(), "clock observation output must be unused")
    sys.path[:0] = [str(code / "src"), str(code)]
    sys.path.append(str(code / "re/tooling/sw2026"))
    from EpochReadback import concrete, observe_header, observe_history
    from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
    from convert.adapters.solidworks.Archive.History.ReadHistMut import ReadHistMut
    from convert.adapters.solidworks.Archive.History.WriteHistMut import WriteHistMut
    from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHeader import ReadMgrHeader
    from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHeader import WriteMgrHeader
    from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Drawing.Definition.Named.ReadNamedDef import ReadNamedDef
    from convert.adapters.solidworks.Drawing.Definition.Named.WriteNamedDef import WriteNamedDef
    from convert.adapters.solidworks.Drawing.Definition.Profiles.ReadAllProfiles import ReadAllProfiles

    def history(archive):
        raw = archive.require("_MO_VERSION_19000/History")
        graph = ReadHistMut(raw, 19000)
        require(WriteHistMut(graph.RootValue, 19000)[0] == raw, "native clock history replay differs")
        result = observe_history(graph.RootValue)
        fields = graph.RootValue.FieldsValue
        result["provenance_fields"] = {name: fields[name] for name in ("f28", "f2c", "f30", "f38", "f3c", "f40")}
        codes = []
        for row in fields["states"]:
            owner = concrete(row["st"]["f38"], "moDateCodeHistory_c")
            values = owner.FieldsValue["states"]
            require(0 < len(values) <= 128 and owner.FieldsValue["n"] == len(values), "native date-code membership differs")
            codes.append([value["st"]["f08"] for value in values])
        result.update(date_code_states=codes, raw_sha256=digest(raw), byte_identity=True,
                      provenance_semantics_unprojected=True)
        return result

    def observe_pair(child_raw, drawing_raw, case):
        child_archive = SldprtArchive.from_bytes(child_raw)
        drawing_archive = SldprtArchive.from_bytes(drawing_raw)
        child = ReadNativeLink(child_archive, 0)
        model = concrete(child.ConfigValue.RootValue, "moPart_c")
        header = child.ConfigValue.HeaderValue
        top = ReadHeaderGraph(child_archive.require("Header2"), 19000)
        manager = ReadMgrHeader(child_archive.require("Contents/CMgrHdr2"), 19000)
        require(WriteHeadGraph(header, 19000) == child_archive.require("Contents/Config-0-ModelHeader")
                and WriteHeadGraph(top, 19000) == child_archive.require("Header2")
                and WriteMgrHeader(manager.RootValue, 19000)[0] == child_archive.require("Contents/CMgrHdr2"),
                "native clock header replay differs")
        drawing = ReadNamedDef(drawing_archive.require("Contents/Definition"), 19000, case["view"]["orientation"])
        require(WriteNamedDef(drawing.GraphValue).OutputValue == drawing_archive.require("Contents/Definition"),
                "native drawing Definition replay differs")
        drawing_model = concrete(drawing.GraphValue.DocumentValue.FieldsValue["model"], "moDrawing_c")
        drawing_header = concrete(drawing_model.FieldsValue["fa8"], "moHeader_c")
        drawing_top = ReadHeaderGraph(drawing_archive.require("Header2"), 19000)
        require(WriteHeadGraph(drawing_top, 19000) == drawing_archive.require("Header2"), "native drawing Header2 replay differs")
        origins = tuple(value for value in child.ResolvedValue.RootsValue if value is not None
                        and value.ClassValue == RuntimeClass("moOriginProfileFeature_c", 1))
        require(len(origins) == 1, "native epoch source has no unique actual origin")
        origin_id = origins[0].FieldsValue["f08"]
        origin_time = DatumTime(header, origin_id)
        displays = tuple(item for group in ReadAllProfiles(drawing.GraphValue.DocumentValue, 19000) for item in group.ItemsValue)
        require(len(displays) == 1, "native epoch drawing has no unique retained origin display")
        item = displays[0]
        wrapper = concrete(item.ReferenceValue, "moCompProfile_c")
        require(wrapper.FieldsValue["ff0"] == {"f00": origin_id, "f08": origin_time}
                and item.DisplayValue.FieldsValue["f30"] is item.FolderValue
                and item.DisplayValue.FieldsValue["f40"] is item.ViewValue
                and item.DisplayValue.FieldsValue["f48"] is wrapper,
                "native clock lifecycle changed the actual origin event or drawing owner aliases")
        return {"child": {"model_header": observe_header(header, model), "top_header": observe_header(top, model),
                          "history": history(child_archive), "manager_saved_f60": manager.RootValue.FieldsValue["f60"]},
                "drawing": {"model_header": observe_header(drawing_header, drawing_model),
                            "top_header": observe_header(drawing_top, drawing_model), "history": history(drawing_archive),
                            "has_independent_manager_header": "Contents/CMgrHdr2" in drawing_archive.streams,
                            "unprojected": list(drawing.Unprojected)},
                "actual_origin_id": origin_id, "actual_origin_creation_time": origin_time,
                "actual_origin_event_and_owner_aliases": True,
                "child_sha256": digest(child_raw), "drawing_sha256": digest(drawing_raw),
                "raw_typed_metadata_byte_identity": True}

    report = {"schema": "kit.sw2026.native-epoch-observations.v1", "packet_sha256": args.packet_sha256,
              "source_manifest_sha256": args.source_manifest_sha256, "native_result_sha256": args.native_result_sha256,
              "cases": [], "data_collected": False, "native_acceptance": False, "heldout_acceptance": False,
              "clock_constructor_expansion_qualified": False, "vm_calls": False, "hidden_inputs_read": False}
    def checkpoint():
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n")
    with args.output.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n")
    for case in packet["cases"]:
        row = {"case": case["name"], "clock_plan": case["clock_plan"], "phases": {}, "data_collected": False}
        report["cases"].append(row)
        try:
            initial = observe_pair(checked(root, case["files"]["child"]), checked(root, case["files"]["drawing"]), case)
            row["constructed"] = initial
            for phase in ("open-save", "reopen", "edit-move-save", "reopen-edited"):
                result = native["phases"][case["name"] + "/" + phase]
                record_raw = (root / "Inspection" / case["name"] / phase / "Record.json").read_bytes()
                require(digest(record_raw) == result["record_sha256"], "native operation clock window record differs")
                record = json.loads(record_raw)
                current = observe_pair(checked(root, result["child_file"]), checked(root, result["drawing_file"]), case)
                current["native_phase_wall_seconds"] = {name: record[name] for name in ("started_at", "finished_at")}
                changes = {}
                for kind in ("child", "drawing"):
                    fields = ("CreatedAt", "ModifiedAt", "UpdatedAt", "RootFirstEventAt", "SelfCreatedAt", "SelfSavedAt")
                    changes[kind] = {name: {"constructed": initial[kind]["model_header"][name], "native_saved": current[kind]["model_header"][name]}
                                     for name in fields if initial[kind]["model_header"][name] != current[kind]["model_header"][name]}
                current["changed_model_header_clocks"] = changes
                current["attribution"] = "phase-wide archived result; no live setter or helper-mode observation"
                row["phases"][phase] = current
                checkpoint()
            row["data_collected"] = True
        except Exception as error:
            row["diagnostic"] = {"exception": type(error).__name__, "message": str(error)}
        checkpoint()
    report["data_collected"] = len(report["cases"]) == 4 and all(value["data_collected"] for value in report["cases"])
    checkpoint()
    print(json.dumps({"data_collected": report["data_collected"], "result_sha256": digest(args.output.read_bytes()),
                      "native_acceptance": False}))
    return 0 if report["data_collected"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
