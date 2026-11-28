from __future__ import annotations

from base64 import b64encode
import codecs
from copy import deepcopy
import importlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
TOOLS = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(TOOLS), str(TOOLS / "serial")]

from DrawingFrontBundleProcess import AUDIT, digest, require
from DrawingGraphBridge import generated_document
from Classes import registry
from builders.DrawingDocument import construct_blank_drawing
from DrawingPublicScope import refuse_research_drawing
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Container.Container import build_sldprt
from convert.adapters.solidworks.Container.Format import KDrawingFormatId
from convert.adapters.solidworks.Drawing.Construction.Sheet.MakeBlankSheet import MakeBlankSheet
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetBuild import SheetBuild
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetInput import SheetInput
from convert.adapters.solidworks.Drawing.Construction.Sheet.SheetNames import SheetNames
from convert.adapters.solidworks.Drawing.Definition.Emission.BlankGraph import BlankGraph
from convert.adapters.solidworks.Drawing.Definition.Emission.ReadBlankDef import ReadBlankDef
from convert.adapters.solidworks.Drawing.Definition.Emission.ReadBlankKids import ReadBlankKids
from convert.adapters.solidworks.Drawing.Definition.Emission.WriteBlankDef import WriteBlankDef
from convert.api import open_document


def build_input(request, probe):
    spec = dict(request["sheet"])
    names = request["sheet_names"]
    target = request["target"]
    creation = request["provenance"]["created_at"]
    first_id = 1 + len(("annotations", "binder", "comments"))
    values = {
        "FirstIdValue": first_id, "CreatedAtValue": creation,
        "DateCodeValue": target["date_code"], "KernelVersion": target["parasolid_version"],
        "ArchiveVersion": 19000, "ServicePack": 5, "SubservicePack": 2,
    }
    if probe == "scale_zero":
        spec["scale_numerator"] = 0
    elif probe == "scale_boolean":
        spec["scale_denominator"] = True
    elif probe == "paper_format":
        spec["paper_size"] = "other-paper"
    elif probe == "length_unit":
        spec["length_unit"] = "unqualified-unit"
    elif probe == "sheet_delimiter":
        spec["name"] = "ambiguous@sheet"
    elif probe == "sheet_xml":
        spec["custom_property_view"] = "bad\x01property"
    elif probe == "support_name":
        names = {**names, "profile_name": ""}
    elif probe == "archive_version":
        values["ArchiveVersion"] = 18000
    elif probe == "service_pack":
        values["ServicePack"] = 4
    elif probe == "id_domain":
        values["FirstIdValue"] = 0
    elif probe == "creation_time":
        values["CreatedAtValue"] = -1
    elif probe == "kernel_provenance":
        values["KernelVersion"] = 0
    elif probe is not None and probe not in ("foreign_owner", "external_component"):
        raise ValueError("unknown sheet construction qualification probe")
    return SheetBuild(
        SheetInput(spec["name"], spec["paper_size"], spec["scale_numerator"], spec["scale_denominator"],
                   spec["length_unit"], spec["custom_property_view"]),
        SheetNames(names["plane_name"], names["profile_name"], names["detail_name"]), **values,
    )


def main():
    job = json.load(sys.stdin)
    require(job["schema"] == "kit.sw2026.sdk-sheet-construction-process.v1", "sheet construction job differs")
    for name in ("DocumentAssemblyValidate", "DocumentFeatureValidate", "DocumentReferenceValidate"):
        importlib.import_module("interchange.document.Validation." + name)
    tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
    canonical_rules, independent_rules = registry(), registry()
    AUDIT.BeginBuild()
    request = job["request"]
    canonical = construct_blank_drawing(registry=canonical_rules, request=deepcopy(request))
    independent = construct_blank_drawing(registry=independent_rules, request=deepcopy(request))
    document = generated_document(construction=independent, request=request)
    model = document.FieldsValue["model"]
    component = model.FieldsValue["f990"]
    if job.get("qualification_probe") == "foreign_owner":
        model.ClassValue = RuntimeClass("moPart_c", 1)
    elif job.get("qualification_probe") == "external_component":
        component.FieldsValue["has_ext"] = 1
    build = build_input(request, job.get("qualification_probe"))
    generated = MakeBlankSheet(build, model, component)
    require(generated.ProfileValue.FieldsValue["pd_f80"].FieldsValue["f138"] is generated.ProfileValue,
            "SDK sheet constructor lost its runtime sketch owner backlink")
    original_children = ReadBlankKids(model)
    require(sum(node.ClassValue.NameValue == "moDrSheet" for node in original_children) == 1,
            "the independent parent contains a different sheet count")
    new_children = tuple(generated.SheetValue if node.ClassValue.NameValue == "moDrSheet" else node
                         for node in original_children)
    model.FieldsValue["f60"] = {"list": {"n": len(new_children), "items": tuple({"o": node} for node in new_children)}, "tail": 0}
    model.FieldsValue["f1430"] = generated.SheetValue
    document.FieldsValue["fac0"] = generated.UiSketch
    late_roles = ("ink_markups",)
    require(generated.NextIdValue + len(late_roles) == model.FieldsValue["fa8"].FieldsValue["f08"],
            "new sheet allocator progress differs from the parent construction plan")
    output = WriteBlankDef(BlankGraph(document, 19000))
    require(output.OutputValue == canonical.streams["Contents/Definition"]
            and output.MapValue.CounterValue == canonical.definition_map_count,
            "SDK sheet construction changed independent complete Definition bytes or map")
    sdk = ReadBlankDef(output.OutputValue, 19000)
    again = WriteBlankDef(sdk.GraphValue)
    require(again.OutputValue == output.OutputValue, "SDK constructed graph lost a field on readback")
    read_model = sdk.GraphValue.DocumentValue.FieldsValue["model"]
    read_sheet = read_model.FieldsValue["f1430"]
    plane, profile, details = ReadBlankKids(read_sheet)
    reference = profile.FieldsValue["pd_f78"]
    require(reference.FieldsValue["ff8"] is plane and reference.FieldsValue["ff0"] == {"f00": -1, "f08": 2592000},
            "SDK sheet lost its preallocation plane handle")
    require(reference.FieldsValue["f58"] is not read_model.FieldsValue["f990"]
            and reference.FieldsValue["f58"].FieldsValue["owner"] is read_model,
            "SDK sheet reference lost its exclusively owned component copy")
    require(read_sheet.FieldsValue["f408"] is profile and read_sheet.FieldsValue["f390"] is details,
            "SDK sheet lost its real profile or detail aliases")
    ratio = request["sheet"]["scale_numerator"] / request["sheet"]["scale_denominator"]
    require(profile.FieldsValue["pd_ff0"]["f70"] == 1.0 / ratio
            and plane.FieldsValue["f6f8"].FieldsValue["f20"]["f70"] == 1.0 / ratio
            and sdk.GraphValue.DocumentValue.FieldsValue["fac0"].FieldsValue["f80"]["f70"] == ratio,
            "SDK sheet scale frames differ from the native operation order")
    streams = dict(independent.streams)
    streams["Contents/Definition"] = output.OutputValue
    require(streams == canonical.streams, "SDK sheet construction changed another logical stream")
    payload = build_sldprt(streams)
    public = open_document(payload, source_format=KDrawingFormatId, strict=False)
    require(public.drawing is not None and len(public.drawing.Sheets) == 1
            and public.drawing.Sheets[0].EntityName == request["sheet"]["name"],
            "public SDK readback differs from the independent authored sheet")
    public_refusals = refuse_research_drawing(public, linked=False)
    require(not AUDIT.DeniedReads, "SDK sheet construction attempted runtime input access")
    result = {
        "schema": "kit.sw2026.sdk-sheet-construction-result.v1", "passed": True,
        "definition_bytes": len(output.OutputValue), "definition_sha256": digest(output.OutputValue),
        "definition_map_next_index": output.MapValue.CounterValue, "all_logical_streams_identical": True,
        "sdk_complete_read_write_identical": True, "public_reader_passed": True,
        "real_aliases_preserved": True, "preallocation_plane_handle_preserved": True,
        "component_copy_preserved": True, "scale_operation_order_preserved": True,
        "constructor_sketch_backlink_preserved": True,
        "feature_ids": [node.FieldsValue["f08"] for node in (read_sheet, plane, profile, details)],
        "next_sheet_id": generated.NextIdValue,
        "artifact_bytes": len(payload), "artifact_sha256": digest(payload),
        "artifact_base64": b64encode(payload).decode("ascii"),
        "sdk_sheet_constructor": True, "research_parent_factory_retained": True,
        "complete_sdk_only_drawing_factory": False, "native_acceptance": False,
        "public_write_refusals": public_refusals, "heldout_inputs_read": 0,
        "runtime_input_file_access_attempts": len(AUDIT.DeniedReads), "vendor_runtime_executed": False,
    }
    print(json.dumps(result, indent=None, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
