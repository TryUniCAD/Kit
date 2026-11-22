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
from DrawingGraphBridge import generated_document
from Classes import registry
from defs.Definition import load_definition
from builders.DrawingFrontBundle import construct_front_bundle
from DrawingPublicScope import refuse_research_drawing
from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Container.Container import build_sldprt
from convert.adapters.solidworks.Container.Format import KDrawingFormatId
from convert.api import open_document
from convert.adapters.solidworks.Drawing.Definition.Emission.BlankGraph import BlankGraph
from convert.adapters.solidworks.Drawing.Definition.Emission.ReadBlankDef import ReadBlankDef
from convert.adapters.solidworks.Drawing.Definition.Emission.WriteBlankDef import WriteBlankDef
from convert.adapters.solidworks.Drawing.Definition.Emission.WalkDrawNodes import WalkDrawNodes
from convert.adapters.solidworks.Drawing.Definition.Linked.FrontGraph import FrontGraph
from convert.adapters.solidworks.Drawing.Definition.Linked.ReadFrontDef import ReadFrontDef
from convert.adapters.solidworks.Drawing.Definition.Linked.WriteFrontDef import WriteFrontDef


def inject_probe(document, name):
    model = document.FieldsValue["model"]
    sheet = model.FieldsValue["f1430"]
    view, = [row["o"] for row in sheet.FieldsValue["f60"]["list"]["items"]
             if row["o"].ClassValue.NameValue == "moAbsoluteView"]
    reference = view.FieldsValue["f5d8"]
    external = reference.FieldsValue["f4f8"]
    property_model = model.FieldsValue["f16a8"].FieldsValue["f08"][0]["model"]
    if name == "orientation":
        view.FieldsValue["f1018"] = "*Top"
    elif name == "view_scale":
        view.FieldsValue["f780"] = 2.0
    elif name == "view_rotation":
        view.FieldsValue["f5e0"]["has_matrix"] = 1
    elif name == "view_owner":
        view.FieldsValue["owner"] = model
    elif name == "active_sheet":
        model.FieldsValue["f1430"] = view
    elif name == "directory_alias":
        entry = reference.FieldsValue["f3b0"]
        reference.FieldsValue["f3b0"] = ArchiveNode(entry.ClassValue, dict(entry.FieldsValue))
    elif name == "property_alias":
        entry = reference.FieldsValue["f3b0"]
        property_model.FieldsValue["f3b0"] = ArchiveNode(entry.ClassValue, dict(entry.FieldsValue))
    elif name == "property_config":
        property_model.FieldsValue["f3c0"] = {"f08": "foreign configuration", "f10": 1234}
    elif name == "external_backlink":
        external.FieldsValue["f50"] = None
    elif name == "external_name":
        external.FieldsValue["f38"] = "unqualified direct CString"
    elif name == "external_owner":
        external.FieldsValue["f10"]["f20"] = 3
    elif name == "support_alias":
        view.FieldsValue["f7c8"] = view.FieldsValue["fde0"]
    elif name == "support_owner":
        view.FieldsValue["f7c8"].FieldsValue["pd_f78"].FieldsValue["f58"].FieldsValue["owner"] = sheet
    elif name == "annotation":
        view.FieldsValue["fa20"]["items"] = ({"o": sheet},)
    elif name == "view_cache":
        view.FieldsValue.update(has_fb50=1, fb50={"n": 0})
    elif name == "root_preview":
        model.FieldsValue["n1740"] = 1
    elif name == "ui_profile":
        document.FieldsValue["fac0"].FieldsValue["profile_feature_id"] = -1
    elif name == "view_schema":
        view.ClassValue = RuntimeClass("moAbsoluteView", 2)
    elif name == "second_view":
        listing = sheet.FieldsValue["f60"]["list"]
        listing["items"] = (*listing["items"], {"o": view})
    elif name not in (None, "archive_version", "read_tail", "read_version"):
        raise ValueError("unknown front drawing Definition qualification probe")


def main():
    job = json.load(sys.stdin)
    require(job["schema"] == "kit.sw2026.sdk-front-definition-process.v1", "front drawing Definition job differs")
    for name in ("DocumentAssemblyValidate", "DocumentFeatureValidate", "DocumentReferenceValidate"):
        importlib.import_module("interchange.document.Validation." + name)
    tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
    rules = registry()
    independent_rules = registry()
    AUDIT.BeginBuild()
    request = job["request"]
    canonical = construct_front_bundle(registry=rules, request=deepcopy(request))
    independent = construct_front_bundle(registry=independent_rules, request=deepcopy(request))
    model = independent.view["owner"]["owner"]
    require(model.cls == "moDrawing_c", "front drawing Definition source model ownership differs")
    document = generated_document(construction=SimpleNamespace(model=model), request=request["drawing"])
    inject_probe(document, job.get("qualification_probe"))
    version = 18000 if job.get("qualification_probe") == "archive_version" else 19000
    output = WriteFrontDef(FrontGraph(document, version))
    require(output.OutputValue == canonical.streams["Contents/Definition"], "SDK front drawing Definition changed generated bytes")
    require(output.MapValue.CounterValue == canonical.definition_map_count, "SDK front drawing Definition map differs")
    sdk_read = ReadFrontDef(output.OutputValue, 19000)
    sdk_again = WriteFrontDef(sdk_read.GraphValue)
    require(sdk_again.OutputValue == output.OutputValue
            and sdk_read.MapValue.CounterValue == output.MapValue.CounterValue
            and sdk_again.MapValue.CounterValue == output.MapValue.CounterValue,
            "SDK front drawing Definition complete read and reemission differs")
    if job.get("qualification_probe") == "read_tail":
        ReadFrontDef(output.OutputValue + b"\0", 19000)
        raise ValueError("front drawing Definition accepted an unconsumed tail")
    if job.get("qualification_probe") == "read_version":
        ReadFrontDef(output.OutputValue, 18000)
        raise ValueError("front drawing Definition accepted an unsupported reader version")
    for action, argument in ((WriteBlankDef, BlankGraph(document, 19000)), (ReadBlankDef, output.OutputValue)):
        try:
            action(argument, 19000) if action is ReadBlankDef else action(argument)
        except (BodyUnsupported, ValueError):
            pass
        else:
            raise ValueError("front drawing Definition silently widened blank admission")
    streams = dict(independent.streams)
    streams["Contents/Definition"] = output.OutputValue
    require(streams == canonical.streams, "SDK front drawing Definition changed another logical stream")
    parsed, archive = load_definition(output.OutputValue, rules, 19000)
    require(archive.left() == 0 and not parsed.tail and archive.count == output.MapValue.CounterValue,
            "SDK front drawing Definition has incomplete independent readback")
    payload = build_sldprt(streams)
    part_data = build_sldprt(independent.part.streams)
    inspection = check_bundle(drawing_data=payload, part_data=part_data, bundle=independent, request=request, rules=rules)
    public = open_document(payload, source_format=KDrawingFormatId, strict=False)
    public_refusals = refuse_research_drawing(public, linked=True)
    require(not AUDIT.DeniedReads, "front drawing Definition attempted runtime input access")
    usage = GetBodyReport(output.UsageValue)
    require(usage["completed"] and not usage["missing_schemas"], "front drawing Definition grammar did not finish")
    classes = sorted({node.ClassValue.NameValue for node in WalkDrawNodes(document)})
    result = {"schema": "kit.sw2026.sdk-front-definition-result.v1", "passed": True,
              "definition_bytes": len(output.OutputValue), "definition_sha256": digest(output.OutputValue),
              "definition_map_next_index": output.MapValue.CounterValue,
              "all_logical_streams_identical": True, "artifact_bytes": len(payload), "artifact_sha256": digest(payload),
              "artifact_base64": b64encode(payload).decode("ascii"), "child_artifact_sha256": digest(part_data),
              "usage": usage, "classes": classes, "inspection": inspection,
              "complete_sdk_readback": True, "sdk_read_write_identical": True,
              "complete_research_readback": True, "public_reader_passed": True,
              "blank_profile_unchanged": True, "runtime_input_file_access_attempts": len(AUDIT.DeniedReads),
              "heldout_inputs_read": 0, "vendor_runtime_executed": False, "native_acceptance": False,
              "public_write_refusals": public_refusals, "research_semantic_factory_retained": True}
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError) as error:
        raise ValueError("front drawing Definition rejected: " + str(error)) from error
