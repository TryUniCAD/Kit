from __future__ import annotations

from base64 import b64encode
import codecs
from copy import deepcopy
import importlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[3]
TOOLS = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(TOOLS), str(TOOLS / "serial")]

from DrawingFrontBundleProcess import AUDIT, check_bundle, digest, require
from DrawingGraphBridge import generated_document, project_generated_graph
from DrawingModelBridge import compatible_model
from DrawingModelInput import drawing_build
from Classes import registry
from Core import Store
from builders.DrawingDocument import _metadata, construct_blank_drawing
from builders.DrawingFrontBundle import FrontDrawingBundle, construct_front_bundle
from builders.DrawingFrontView import add_front_view
from builders.DrawingMetadata import DrawingViewIndex, drawing_sheet_indexes
from builders.DrawingSheet import drawing_sheet
from builders.Part import construct_part
from convert.adapters.solidworks.Archive.Construction.Model.RequireModel import RequireModel
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Container.Container import build_sldprt
from convert.adapters.solidworks.Container.Format import KDrawingFormatId
from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
from convert.adapters.solidworks.Drawing.Construction.Model.MakeDrawRoot import MakeDrawRoot
from convert.adapters.solidworks.Drawing.Definition.Emission.BlankGraph import BlankGraph
from convert.adapters.solidworks.Drawing.Definition.Emission.ReadBlankDef import ReadBlankDef
from convert.adapters.solidworks.Drawing.Definition.Emission.ReadBlankKids import ReadBlankKids
from convert.adapters.solidworks.Drawing.Definition.Emission.WriteBlankDef import WriteBlankDef
from convert.adapters.solidworks.Drawing.Definition.Linked.FrontGraph import FrontGraph
from convert.adapters.solidworks.Drawing.Definition.Linked.ReadFrontDef import ReadFrontDef
from convert.adapters.solidworks.Drawing.Definition.Linked.WriteFrontDef import WriteFrontDef
from convert.api import open_document


def check_constructed(graph, spec):
    model = graph.ModelValue
    fields = model.FieldsValue
    children = ReadBlankKids(model)
    require(type(model) is ArchiveNode and fields["f08"] == 0 and graph.Allocator.NextValue == 9,
            "drawing root constructor lost its concrete owner or persistent boundary")
    require(fields["f990"].FieldsValue["owner"] is model and fields["f9d0"].FieldsValue["owner"] is model,
            "drawing root constructor lost actual self or relation ownership")
    require([node.ClassValue.NameValue for node in children] == ["moCommentsFolder_c", "moBlockFolder_c",
            "moDocsFolder_c", "moDetailCabinet_c", "moInkMarkupFolder_c", "moMarkupCommentFolder_c", "moDrSheet"],
            "drawing root constructor changed native child order")
    require([node.FieldsValue["f08"] for node in children] == [3, -1, 2, 1, 8, -1, 4],
            "drawing root constructor changed registration lifetimes")
    require(all(node.FieldsValue["owner"] is model for node in children)
            and fields["f1430"] is children[-1] is graph.SheetValue.SheetValue,
            "drawing root constructor lost containing or active sheet ownership")
    require(len({id(fields[name]) for name in ("f9d8", "fa48", "fa50")}) == 3
            and fields["f78"] is fields["f9c0"] is None and len(fields["f9f8"]) == 10,
            "drawing root constructor lost shared model allocation state")
    layers, blocks, properties = (fields[key] for key in ("fed0", "fe80", "f16a8"))
    require(layers.FieldsValue["f30"] is model and properties.FieldsValue["f18"] is model
            and blocks.FieldsValue["blocks"]["f30"] is blocks,
            "drawing root constructor lost manager ownership")
    require(fields["f1444"] == 256 | int(spec["presentation"]["auto_dim_text_link"]),
            "drawing root constructor lost authored dimension text behavior")
    for descriptor in (RuntimeClass("moDrawing_c", 2), ExternalClass("moDrawing_c", 1), RuntimeClass("moModel_c", 1)):
        try:
            RequireModel(ArchiveNode(descriptor, {}))
        except (TypeError, ValueError):
            pass
        else:
            raise ValueError("drawing root constructor widened unresolved shared ownership admission")
    return {"plain_sdk_model": True, "self_component_owner": True, "relation_runtime_owner": True,
            "active_sheet_identity": True, "manager_backlinks": True, "auxiliary_lists": 3,
            "canonical_view_count": 10, "root_id": fields["f08"], "root_next_id": graph.Allocator.NextValue,
            "ordered_child_ids": [node.FieldsValue["f08"] for node in children], "shared_owner_guard_rejections": 3}


def generated_bundle(graph, spec, request, mode, rules):
    model = compatible_model(graph.ModelValue)
    provenance, presentation = spec["provenance"], spec["presentation"]
    streams = _metadata(registry=rules, model=model, next_id=graph.Allocator.NextValue,
                        provenance=provenance, presentation=presentation, output=spec["output"])
    settings = drawing_sheet(spec["sheet"])
    part = view = None
    if mode == "front":
        part = construct_part(registry=rules, **request["part"])
        view = add_front_view(drawing=model, child=part, sheet_settings=settings, requested=request["view"],
                              created_at=provenance["created_at"], target=spec["target"])
    document = generated_document(construction=SimpleNamespace(model=model), request=spec)
    document.FieldsValue["fac0"] = project_generated_graph(graph.SheetValue.UiSketch)
    if mode == "front":
        output = WriteFrontDef(FrontGraph(document, 19000))
        read = ReadFrontDef(output.OutputValue, 19000)
        again = WriteFrontDef(read.GraphValue)
    else:
        output = WriteBlankDef(BlankGraph(document, 19000))
        read = ReadBlankDef(output.OutputValue, 19000)
        again = WriteBlankDef(read.GraphValue)
    require(again.OutputValue == output.OutputValue and again.MapValue.CounterValue == output.MapValue.CounterValue,
            "drawing root constructor lost complete SDK read and reemission parity")
    streams["Contents/Definition"] = output.OutputValue
    if mode == "front":
        from Streams import StreamDoc, store_rooted
        streams["Header2"] = store_rooted(StreamDoc("rooted", {"base": 1}, [model["fa8"]]), rules, 19000)
    stamps = Store(1, rules, 19000)
    header = model["fa8"]
    rules.run_store("ModelStamps.load", stamps, {"creation": header["f70"], "update_stamp": header["f40"], "body_stamp": header["f44"]}, model)
    streams["ModelStamps"] = bytes(stamps.out)
    layout = {"document_name": spec["name"], "created_at": provenance["created_at"], "sheet": settings,
              "sheet_id": model["f1430"]["f08"]}
    if mode == "front":
        layout["model_view"] = DrawingViewIndex.from_view(view)
    streams.update(drawing_sheet_indexes(**layout))
    read_model = read.GraphValue.DocumentValue.FieldsValue["model"]
    require(read_model.FieldsValue["f990"].FieldsValue["owner"] is read_model
            and read_model.FieldsValue["f1430"] is ReadBlankKids(read_model)[-1],
            "drawing root constructor lost persisted model or active sheet aliases")
    return output, streams, part, view, read_model


def main():
    job = json.load(sys.stdin)
    require(job["schema"] == "kit.sw2026.sdk-drawing-model-process.v1", "drawing root process job differs")
    for name in ("DocumentAssemblyValidate", "DocumentFeatureValidate", "DocumentReferenceValidate"):
        importlib.import_module("interchange.document.Validation." + name)
    tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
    require(not callable(getattr(SldprtAdapter(), "write", None)), "drawing root constructor enabled public writing")
    mode = job.get("mode", "blank")
    require(mode in ("blank", "front"), "drawing root process mode differs")
    request = job["request"]
    spec = request["drawing"] if mode == "front" else request
    rules, independent_rules = registry(), registry()
    AUDIT.BeginBuild()
    canonical = (construct_front_bundle(registry=rules, request=deepcopy(request)) if mode == "front"
                 else construct_blank_drawing(registry=rules, request=deepcopy(spec)))
    graph = MakeDrawRoot(drawing_build(spec, job.get("qualification_probe")))
    construction = check_constructed(graph, spec)
    output, streams, part, view, read_model = generated_bundle(graph, spec, request, mode, independent_rules)
    require(output.OutputValue == canonical.streams["Contents/Definition"]
            and output.MapValue.CounterValue == canonical.definition_map_count,
            "drawing root constructor changed complete independent Definition bytes or map")
    require(streams == canonical.streams, "drawing root constructor changed another generated logical stream")
    payload = build_sldprt(streams)
    if mode == "front":
        bundle = FrontDrawingBundle(streams, view, part, output.MapValue.CounterValue)
        inspection = check_bundle(drawing_data=payload, part_data=build_sldprt(part.streams),
                                  bundle=bundle, request=request, rules=rules)
        require(read_model.FieldsValue["f1430"].FieldsValue["f08"] == graph.SheetValue.SheetValue.FieldsValue["f08"],
                "drawing root constructor lost linked sheet identity")
    else:
        document = open_document(payload, source_format=KDrawingFormatId, strict=False)
        require(document.drawing is not None and document.drawing.Sheets[0].EntityName == spec["sheet"]["name"],
                "drawing root constructor changed public sheet readback")
        inspection = {"sheet": document.drawing.Sheets[0].EntityName}
    require(not AUDIT.DeniedReads, "drawing root constructor attempted runtime input access")
    result = {"schema": "kit.sw2026.sdk-drawing-model-result.v1", "passed": True, "mode": mode,
              **construction, "inspection": inspection, "sdk_model_factory": True,
              "research_parent_factory_retained": False, "research_ui_metadata_retained": True,
              "complete_sdk_only_drawing_factory": False,
              "all_logical_streams_identical": True, "complete_sdk_read_write_identical": True,
              "definition_bytes": len(output.OutputValue), "definition_sha256": digest(output.OutputValue),
              "definition_map_next_index": output.MapValue.CounterValue,
              "artifact_bytes": len(payload), "artifact_sha256": digest(payload),
              "artifact_base64": b64encode(payload).decode("ascii"),
              "runtime_input_file_access_attempts": len(AUDIT.DeniedReads), "heldout_inputs_read": 0,
              "vendor_runtime_executed": False, "native_acceptance": False, "public_writer_enabled": False}
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError) as error:
        raise ValueError("drawing root constructor rejected: " + str(error)) from error
