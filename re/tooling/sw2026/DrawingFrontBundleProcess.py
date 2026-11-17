from __future__ import annotations

import codecs
import json
import sys
from base64 import b64encode
from importlib import import_module

from DrawingFrontRecordProcess import AUDIT, check_header, digest, nodes, reencode, require, verify_graph

from Classes import registry
from Streams import load_rooted
from builders.DrawingFrontBundle import construct_front_bundle
from builders.DrawingMetadata import INFORMATION_STREAM
from builders.Metadata import FILE_VERSION
from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt
from convert.adapters.solidworks.Container.Format import KDrawingFormatId, KeywordsStream
from convert.adapters.solidworks.Core.Native import ParseXml
from convert.adapters.solidworks.Drawing.Metadata.ReadDrawProps import ReadDrawProps
from convert.api import open_document


def checked_indexes(archive, view, sheet):
    root = ParseXml(archive.require(KeywordsStream))
    catalog = root.findall("View")
    detail = root.findall("Sheet/View")
    reference = view["f5d8"]
    config = reference["f3c0"]
    name = view["f18"]["f08"]
    file = reference["f3b0"]["shared"]
    require(len(catalog) == len(detail) == 1, "each drawing keyword owner needs one view")
    for node in (*catalog, *detail):
        require(node.attrib == {"id": str(config["f10"]), "Name": name, "Description": config["f08"]}
                and node.text == file["h10"]["f08"] + ".sldprt", "drawing keywords differ from their native view owners")
    key = "SW-Config-Model-View-Sheet-List"
    properties = ReadDrawProps(archive.require(INFORMATION_STREAM), frozenset((key,)))
    require(properties[key].split("@") == ["1:", "", config["f08"], str(config["f10"]),
                                             file["h18"]["f08"], name, sheet["f18"]["f08"]],
            "drawing model-view index differs from its native owners")
    return config


def check_bundle(*, drawing_data, part_data, bundle, request, rules):
    archive = SldprtArchive.from_bytes(drawing_data)
    part = SldprtArchive.from_bytes(part_data)
    require(archive.streams == bundle.streams and part.streams == bundle.part.streams,
            "generated containers changed their logical streams")
    definition = archive.require("Contents/Definition")
    model, count = reencode(definition, rules, archive)
    header, header_map = check_header(archive.require("Header2"), rules)
    sheet = model["f1430"]
    view, = [node for node in nodes(sheet) if node.cls == "moAbsoluteView"]
    require(count == bundle.definition_map_count, "generated drawing altered its Definition map")
    verify_graph(original=bundle.view, model=model, header=header, view=view)
    linked = checked_indexes(archive, view, sheet)
    manager, _ = load_rooted(part.require("Contents/CMgr"), rules, 1, FILE_VERSION)
    active = manager.roots[0]["f360"]
    require(linked == {"f08": active["f18"]["f08"], "f10": active["f08"]}, "drawing reference lost the generated part configuration")
    projected = open_document(drawing_data, source_format=KDrawingFormatId, strict=False).drawing
    layout, = projected.Sheets
    shown, = layout.Views
    linked_model, = projected.ModelRefs
    position = (shown.PositionValue.XCoord, shown.PositionValue.YCoord)
    require(shown.EntityName == request["view"]["name"] and position == tuple(request["view"]["position"])
            and shown.OrientationName == "*Front" and shown.ScaleRatio == (1.0, 1.0) and shown.ConfigurationName == linked["f08"],
            "drawing SDK layout differs from the authored view")
    require(linked_model.SourcePath == request["part"]["output"]["path_name"], "drawing SDK omitted the generated part path")
    return {"definition_map_next_index": count, "header_map_next_index": header_map, "view_persistent_id": view["f08"],
            "next_persistent_id": header["f08"], "child_configuration_id": linked["f10"], "sheet": layout.EntityName,
            "view": shown.EntityName, "position_m": position, "scale_ratio": shown.ScaleRatio,
            "outline_m": shown.OutlineValues, "model_to_sheet": shown.ModelToSheet.Values,
            "readback_exact": True, "detailing_bucket_count": model["n1578"]}


def artifact(payload, streams):
    return {"sha256": digest(payload), "bytes": len(payload), "artifact_base64": b64encode(payload).decode("ascii"),
            "streams": {name: {"sha256": digest(data), "bytes": len(data)} for name, data in sorted(streams.items())}}


def main():
    request = json.load(sys.stdin)
    tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
    for module in ("DocumentAssemblyValidate", "DocumentFeatureValidate", "DocumentReferenceValidate"):
        import_module("interchange.document.Validation." + module)
    rules = registry()
    AUDIT.BeginBuild()
    bundle = construct_front_bundle(registry=rules, request=request)
    drawing, part = (build_sldprt(streams) for streams in (bundle.streams, bundle.part.streams))
    inspection = check_bundle(drawing_data=drawing, part_data=part, bundle=bundle, request=request, rules=rules)
    result = {"schema": "kit.sw2026.generated-front-drawing-bundle.v1", "native_acceptance": False,
              "input_runtime_file_access_attempts": len(AUDIT.DeniedReads), "inspection": inspection,
              "drawing": artifact(drawing, bundle.streams), "part": artifact(part, bundle.part.streams)}
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
