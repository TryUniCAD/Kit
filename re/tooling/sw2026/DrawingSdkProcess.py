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
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(TOOLS)]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit
from DrawingSdkInput import blank_input
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.History.ReadHistMut import ReadHistMut
from convert.adapters.solidworks.Archive.History.WriteHistMut import WriteHistMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KDrawingFormatId
from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
from convert.adapters.solidworks.Drawing.Construction.Portable.MakeBlankFile import MakeBlankFile
from convert.adapters.solidworks.Drawing.Definition.Emission.ReadBlankDef import ReadBlankDef
from convert.adapters.solidworks.Drawing.Definition.Emission.WriteBlankDef import WriteBlankDef
from convert.api import open_document


AUDIT = BuildAudit(TOOLS / "serial/defs")
sys.addaudithook(AUDIT.InspectEvent)


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def main():
    job = json.load(sys.stdin)
    require(job["schema"] == "kit.sw2026.sdk-blank-drawing-process.v1", "SDK blank drawing job differs")
    for name in ("DocumentAssemblyValidate", "DocumentFeatureValidate", "DocumentReferenceValidate"):
        importlib.import_module("interchange.document.Validation." + name)
    for name in ("JoinConcept", "ReadConcept"):
        suffix = "Projection." if name == "JoinConcept" else ""
        importlib.import_module("convert.adapters.solidworks.Drawing.Definition." + suffix + name)
    tuple(codecs.lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
    require(not callable(getattr(SldprtAdapter(), "write", None)), "SDK blank drawing enabled public writing")
    AUDIT.BeginBuild()
    inputs = blank_input(job)
    candidate = MakeBlankFile(inputs)
    self_file = candidate.HeaderValue.FieldsValue["f38"]
    require(candidate.ModelGraph.ModelValue.FieldsValue["fa8"] is candidate.HeaderValue
            and candidate.UiGraph.DocumentValue.FieldsValue["model"] is candidate.ModelGraph.ModelValue
            and self_file.FieldsValue["shared"]["h18"].FieldsValue["value"].TextValue == inputs.FileValue.PathName
            and self_file.FieldsValue["shared"]["h10"].FieldsValue["value"].TextValue == inputs.OptionsValue.NameValue
            and self_file.FieldsValue["shared"]["f20"] == 4
            and self_file.FieldsValue["f60"] == inputs.FileValue.SavedAt
            and self_file.FieldsValue["refcfg"]["f08"].TextValue == ""
            and self_file.FieldsValue["refcfg"]["f10"] == -1,
            "SDK blank drawing lost actual model header UI or self-file identity")
    require(not any(name == "builders" or name.startswith("builders.") or name in ("Classes", "Core", "Streams") for name in sys.modules),
            "SDK blank drawing loaded a research construction or serialization module")
    require(SldprtArchive.from_bytes(candidate.BytesValue).streams == candidate.StreamsValue,
            "SDK blank drawing container changed its generated logical streams")
    definition = ReadBlankDef(candidate.StreamsValue["Contents/Definition"], 19000)
    require(WriteBlankDef(definition.GraphValue).OutputValue == candidate.StreamsValue["Contents/Definition"],
            "SDK blank drawing lost complete Definition read and reemission")
    header = ReadHeaderGraph(candidate.StreamsValue["Header2"], 19000)
    require(WriteHeadGraph(header, 19000) == candidate.StreamsValue["Header2"], "SDK blank drawing header readback differs")
    for name in ("_MO_VERSION_19000/Biography", "_MO_VERSION_19000/History"):
        history = ReadHistMut(candidate.StreamsValue[name], 19000)
        require(WriteHistMut(history.RootValue, 19000)[0] == candidate.StreamsValue[name], "SDK blank drawing history readback differs")
    public = open_document(candidate.BytesValue, source_format=KDrawingFormatId, strict=False)
    expected = inputs.DrawingValue.Sheets[0]
    require(public.drawing is not None and len(public.drawing.Sheets) == 1
            and public.drawing.Sheets[0].EntityName == expected.EntityName
            and public.drawing.Sheets[0].ScaleRatio == expected.ScaleRatio,
            "SDK blank drawing lost portable sheet semantics")
    require(not AUDIT.DeniedReads, "SDK blank drawing attempted runtime input access")
    result = {"schema": "kit.sw2026.sdk-blank-drawing-result.v1", "passed": True,
              "complete_sdk_only_blank_factory": True, "research_builder_modules_loaded": False,
              "complete_sdk_read_write_identical": True, "neutral_drawing_semantics": True,
              "actual_self_file_identity": True,
              "source_sheet_id": candidate.SourceSheetId, "native_sheet_id": candidate.ModelGraph.SheetValue.SheetValue.FieldsValue["f08"],
              "definition_map_next_index": definition.MapValue.CounterValue,
              "artifact_bytes": len(candidate.BytesValue), "artifact_sha256": digest(candidate.BytesValue),
              "artifact_base64": b64encode(candidate.BytesValue).decode("ascii"),
              "streams": {name: {"bytes": len(data), "sha256": digest(data)} for name, data in sorted(candidate.StreamsValue.items())},
              "runtime_input_file_access_attempts": len(AUDIT.DeniedReads), "heldout_inputs_read": 0,
              "vendor_runtime_executed": False, "native_acceptance": False, "public_writer_enabled": False}
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, IndexError) as error:
        raise ValueError("blank drawing constructor rejected: " + str(error)) from error
