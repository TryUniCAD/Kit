from __future__ import annotations

import codecs
import json
import sys
from pathlib import PureWindowsPath

from DrawingFrontGraphProcess import AUDIT, verify_links, verify_supports

from CheckDrawingDefinitions import check_header, digest, nodes, reencode, require
from Classes import registry
from Streams import StreamDoc, store_rooted
from builders.DrawingDocument import _definitions, construct_blank_drawing
from builders.DrawingFrontView import add_front_view
from builders.DrawingSheet import drawing_sheet
from builders.Metadata import FILE_VERSION, fields
from builders.Part import construct_part
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeader
from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Drawing.Definition.Projection.JoinConcept import JoinConcept
from convert.adapters.solidworks.Drawing.Definition.ReadConcept import ReadConcept
from convert.adapters.solidworks.Drawing.Layout.ReadViewLayout import ReadViewLayout
from convert.adapters.solidworks.Drawing.Metadata.SavedSheet import SavedSheet
from interchange.document.Models.Drawing.DrawingData import DrawingData
from interchange.document.Models.Drawing.DrawingModelRef import DrawingModelRef
from interchange.document.Models.Drawing.DrawingSheet import DrawingSheet


def project_view(*, archive, header_bytes, sheet, settings, child, requested):
    header = ReadHeader(header_bytes, FILE_VERSION)
    native, = header.ModelFiles
    path = child.model_header["f38"]["shared"]["h18"]["f08"]
    configuration = child.configuration["f18"]["f08"]
    require(native.PathValue == path and native.KindValue == 2 and not native.ConfigValue,
            "Header2 lost its generated child identity")
    model = DrawingModelRef("slddrw:model:1", path, KPartFormatId)
    ratio = (float(settings.scale_numerator), float(settings.scale_denominator))
    saved = SavedSheet(sheet["f08"], settings.name, ratio, requested["name"], PureWindowsPath(path).name, configuration)
    view_layout = ReadViewLayout(header, saved, model.EntityId)
    layout = DrawingSheet(f"slddrw:sheet:{sheet['f08']}", settings.name, *settings.dimensions, ratio, (view_layout,))
    projected = JoinConcept(ReadConcept(archive, FILE_VERSION), DrawingData(layout.EntityId, (layout,), (model,)))
    view = projected.Sheets[0].Views[0]
    position = (view.PositionValue.XCoord, view.PositionValue.YCoord)
    require(position == tuple(requested["position"]) and view.OrientationName == requested["orientation"]
            and view.ScaleRatio == (1.0, 1.0) and view.ConfigurationName == configuration and view.ModelRefId == model.EntityId,
            "ordinary drawing reader lost authored placement or orientation")
    return {"name": view.EntityName, "position_m": position, "orientation": view.OrientationName, "scale": view.ScaleRatio,
            "model_to_sheet": view.ModelToSheet.Values, "outline_m": view.OutlineValues, "configuration": view.ConfigurationName}


def verify_graph(*, original, model, header, view):
    sheet = model["f1430"]
    sheet_children = nodes(sheet)
    require(sheet_children[-1] is view and [node.cls for node in sheet_children] == [
        "moRefPlane_c", "moProfileFeature_c", "moDetailFolder_c", "moAbsoluteView",
    ], "the view must be the ordered child of its actual drawing sheet")
    children = nodes(view)
    require(view["f630"] is children[0] and view["f7c8"] is children[2] and view["fde0"] is children[4],
            "drawing view lost its detail folder or sketch aliases")
    verify_links(model=model, header=model["fa8"], internal=view["f5d8"], manager=model["f16a8"])
    require(view["f5d8"]["f370"] == view["f600"] and view["f630"]["f08"] + 1 == view["f08"],
            "view lost its local model bounds or persistent allocation order")
    verify_supports(decoded=children, original=nodes(original), model=model)
    require("has_f3d0" in sheet_children[0].f and all("has_f3d0" not in children[index].f for index in (1, 3)),
            "view archive condition 0x40 did not remain scoped to its children")
    require(header["f08"] == model["fa8"]["f08"] == children[-1]["f08"] + 1 and header["bbox"] == model["fa8"]["bbox"],
            "view insertion broke the drawing header identity or view bounds")
    require(not model["n1578"] and not model["n1740"] and not any(view[key] for key in ("has_fb50", "nf68", "na10", "na18")),
            "the complete authored view must remain free of detailing and render cache records")
    for key in ("fe30_name", "fe30_flags", "f610", "f614", "f618", "f61c", "f7a0", "fe94", "f608", "ffa8", "ffac"):
        require(view[key] == original[key], f"generated view field {key} changed on readback")


def inspect_record(*, drawing, view, child, spec, settings, requested, rules):
    definition, count = _definitions(registry=rules, model=drawing, settings=settings, presentation=spec["presentation"]["definition"])
    header = store_rooted(StreamDoc("rooted", {"base": 1}, [drawing["fa8"]]), rules, FILE_VERSION)
    archive = SldprtArchive.from_bytes(build_sldprt({"Contents/Definition": definition, "Header2": header}))
    decoded, read_count = reencode(definition, rules, archive)
    read_header, header_count = check_header(header, rules)
    read_view, = [item for item in nodes(decoded["f1430"]) if item.cls == "moAbsoluteView"]
    require(count == read_count and read_view.pos < read_view.end, "complete view Definition did not consume its exact extent")
    verify_graph(original=view, model=decoded, header=read_header, view=read_view)
    projection = project_view(archive=archive, header_bytes=header, sheet=decoded["f1430"], settings=settings, child=child, requested=requested)
    view_data = definition[read_view.pos:read_view.end]
    return {
        "definition_bytes": len(definition), "definition_sha256": digest(definition), "definition_next_map_index": count,
        "header_bytes": len(header), "header_sha256": digest(header), "header_next_map_index": header_count,
        "view_record_bytes": len(view_data), "view_record_sha256": digest(view_data), "view_field_count": len(read_view.f),
        "view_persistent_id": read_view["f08"], "next_persistent_id": read_header["f08"], "sdk_view_projection": projection,
        "file_version": FILE_VERSION, "container_version": archive.format_version,
        "view_state": {key: read_view[key] for key in ("f2b8", "f300", "f301", "f610", "f614", "f618", "f61c", "f7a0",
                                                        "fe94", "ffa8", "ffac", "fe30_flags", "has_fb50", "nf68")},
        "named_display_state": bool(read_view["fe30_name"]), "detailing_bucket_count": decoded["n1578"],
    }


def main():
    request = fields(json.load(sys.stdin), "front view record", ("drawing", "part", "view"))
    tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
    rules = registry()
    AUDIT.BeginBuild()
    child = construct_part(registry=rules, **request["part"])
    spec = request["drawing"]
    drawing = construct_blank_drawing(registry=rules, request=spec).model
    settings = drawing_sheet(spec["sheet"])
    view = add_front_view(drawing=drawing, child=child, sheet_settings=settings, requested=request["view"],
                          created_at=spec["provenance"]["created_at"], target=spec["target"])
    report = inspect_record(drawing=drawing, view=view, child=child, spec=spec, settings=settings, requested=request["view"], rules=rules)
    report.update(schema="kit.sw2026.front-view-record.v1", native_acceptance=False, native_drawing_emitted=False,
                  input_runtime_file_access_attempts=len(AUDIT.DeniedReads))
    print(json.dumps(report, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
