from __future__ import annotations

from base64 import b64encode
import codecs
from hashlib import sha256
import importlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
TOOLS = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
sys.path.append(str(TOOLS))

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit
from DrawingSdkLinkedInput import linked_input, part_settings
from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindPart
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartStreams import EmitPartStreams
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KDrawingFormatId
from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
from convert.adapters.solidworks.Drawing.Construction.Linked.MakeLinkedFile import MakeLinkedFile
from convert.adapters.solidworks.Drawing.Definition.Named.ReadNamedDef import ReadNamedDef
from convert.adapters.solidworks.Drawing.Definition.Named.WriteNamedDef import WriteNamedDef
from convert.api import open_document
from interchange.document.Models.DocumentModel import CadDocument
from interchange.serialization.Deserialize import FromData


AUDIT = BuildAudit(TOOLS / "serial/defs")
sys.addaudithook(AUDIT.InspectEvent)


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def main():
    job = json.load(sys.stdin)
    require(job["schema"] == "kit.sw2026.sdk-linked-drawing-process.v1", "SDK linked drawing job differs")
    for name in ("DocumentAssemblyValidate", "DocumentFeatureValidate", "DocumentReferenceValidate"):
        importlib.import_module("interchange.document.Validation." + name)
    for name in ("JoinConcept", "ReadConcept"):
        suffix = "Projection." if name == "JoinConcept" else ""
        importlib.import_module("convert.adapters.solidworks.Drawing.Definition." + suffix + name)
    tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
    require(not callable(getattr(SldprtAdapter(), "write", None)), "SDK linked drawing enabled public writing")
    AUDIT.BeginBuild()
    neutral = FromData(job["part"]["document"])
    require(type(neutral) is CadDocument, "SDK linked child requires an actual neutral CAD document")
    child_inputs = part_settings(job)
    child = MakeBlindPart(neutral, child_inputs)
    inputs = linked_input(job)
    candidate = MakeLinkedFile(inputs, child)
    reemitted_child, _, _ = EmitPartStreams(child.SystemValue, child.ResolvedValue.RootsValue,
        (child.HeaderValue, child.TopHeader, child.ManagerHeader), child.DefinitionValue, child_inputs, child.PlanValue)
    require(reemitted_child == child.StreamsValue, "SDK linked drawing mutated its actual generated child graph")
    require(candidate.ChildValue is child and candidate.ViewValue.FieldsValue["owner"] is candidate.ModelGraph.SheetValue.SheetValue,
            "SDK linked drawing lost actual generated child or view ownership")
    require(not any(name == "builders" or name.startswith("builders.") or name in ("Classes", "Core", "Streams") for name in sys.modules),
            "SDK linked drawing loaded a research construction or serialization module")
    require(SldprtArchive.from_bytes(candidate.BytesValue).streams == candidate.StreamsValue,
            "SDK linked drawing container changed its generated logical streams")
    orientation = inputs.DrawingValue.Sheets[0].Views[0].OrientationName
    definition = ReadNamedDef(candidate.StreamsValue["Contents/Definition"], 19000, orientation)
    require(WriteNamedDef(definition.GraphValue).OutputValue == candidate.StreamsValue["Contents/Definition"],
            "SDK linked drawing lost complete Definition read and reemission")
    header = ReadHeaderGraph(candidate.StreamsValue["Header2"], 19000)
    require(WriteHeadGraph(header, 19000) == candidate.StreamsValue["Header2"], "SDK linked drawing header readback differs")
    public = open_document(candidate.BytesValue, source_format=KDrawingFormatId, strict=False)
    expected = inputs.DrawingValue.Sheets[0]
    require(public.drawing is not None and len(public.drawing.Sheets) == len(public.drawing.ModelRefs) == 1
            and public.drawing.Sheets[0].EntityName == expected.EntityName
            and public.drawing.Sheets[0].ScaleRatio == expected.ScaleRatio
            and len(public.drawing.Sheets[0].Views) == 1,
            "SDK linked drawing lost portable sheet semantics")
    actual_view, expected_view = public.drawing.Sheets[0].Views[0], expected.Views[0]
    require(actual_view.EntityName == expected_view.EntityName and actual_view.OrientationName == expected_view.OrientationName
            and actual_view.ConfigurationName == expected_view.ConfigurationName and actual_view.PositionValue == expected_view.PositionValue
            and actual_view.ScaleRatio == expected_view.ScaleRatio and public.drawing.ModelRefs[0].SourcePath == inputs.DrawingValue.ModelRefs[0].SourcePath,
            "SDK linked drawing lost portable model and view semantics")
    require(not AUDIT.DeniedReads, "SDK linked drawing attempted runtime input access")
    plan = child.PlanValue
    result = {"schema": "kit.sw2026.sdk-linked-drawing-result.v1", "passed": True,
              "complete_sdk_only_linked_factory": True, "research_builder_modules_loaded": False,
              "complete_sdk_read_write_identical": True, "neutral_drawing_semantics": True,
              "actual_generated_child_identity": True, "source_sheet_id": candidate.SourceSheetId,
              "child_graph_reemission_unchanged": True,
              "source_view_id": candidate.SourceViewId, "source_model_ref_id": candidate.SourceRefId,
              "native_sheet_id": candidate.ModelGraph.SheetValue.SheetValue.FieldsValue["f08"],
              "native_view_id": candidate.ViewValue.FieldsValue["f08"], "model_next_id": candidate.ModelGraph.Allocator.NextValue,
              "definition_map_next_index": definition.MapValue.CounterValue,
              "orientation": orientation, "scale_ratio": actual_view.ScaleRatio,
              "outline_m": actual_view.OutlineValues, "model_to_sheet": actual_view.ModelToSheet.Values,
              "child_vertices_m": plan.VerticesValue, "child_depth_m": plan.DepthValue,
              "artifact_bytes": len(candidate.BytesValue), "artifact_sha256": digest(candidate.BytesValue),
              "artifact_base64": b64encode(candidate.BytesValue).decode("ascii"),
              "child_artifact_sha256": digest(child.BytesValue), "child_artifact_base64": b64encode(child.BytesValue).decode("ascii"),
              "streams": {name: {"bytes": len(data), "sha256": digest(data)} for name, data in sorted(candidate.StreamsValue.items())},
              "runtime_input_file_access_attempts": len(AUDIT.DeniedReads), "heldout_inputs_read": 0,
              "vendor_runtime_executed": False, "native_acceptance": False, "public_writer_enabled": False}
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, IndexError) as error:
        raise ValueError("linked drawing constructor rejected: " + str(error)) from error
