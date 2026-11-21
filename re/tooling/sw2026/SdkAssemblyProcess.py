from base64 import b64encode
from codecs import lookup
from hashlib import sha256
import json
from pathlib import Path
import sys
import os

ROOT = Path(sys.argv[1])
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/tooling/sw2026")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from SdkAssemblySettings import assembly_settings, occurrence_settings, mate_settings
from SdkBlindPartSettings import settings
from SdkAssemblyFaults import fault_inputs
from convert.adapters.solidworks.Archive.Construction.Assembly.MakeAssembly import MakeAssembly
from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindPart
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileText
from interchange.serialization.Deserialize import FromData
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors

CODECS = tuple(lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()


def require(value, message):
    if not value:
        raise ValueError(message)


def file_handles():
    from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
    forms = ({"text": "independent file name"}, {"f08": "independent file name"}, {"value": CStringValue("independent file name", True)},
             {"text": "independent file name", "f08": "independent file name", "value": CStringValue("independent file name", True)})
    for fields in forms:
        require(ReadFileText(ArchiveNode(RuntimeClass("moCStringHandle_c", 1), fields)) == "independent file name", "generated or decoded file text representation differs")
    bad = ({}, {"text": "a", "f08": "b"}, {"value": "a"}, {"value": CStringValue("", True)}, {"text": "a", "value": CStringValue("b", True)})
    for fields in bad:
        try:
            ReadFileText(ArchiveNode(RuntimeClass("moCStringHandle_c", 1), fields))
        except ValueError:
            continue
        raise ValueError("ambiguous file text representation was accepted")
    return {"constructed_and_decoded": len(forms), "malformed_rejected": len(bad)}


def main():
    child_input = REQUEST["child"]
    child = MakeBlindPart(FromData(child_input["document"]), settings(child_input["settings"]))
    old_bytes = child.BytesValue
    inputs = assembly_settings(REQUEST["assembly"])
    occurrences = occurrence_settings(REQUEST["occurrences"])
    mate = mate_settings(REQUEST["mate"])
    if REQUEST.get("fault") is not None:
        altered = fault_inputs(REQUEST["fault"], child, inputs, occurrences, mate)
        try:
            MakeAssembly(*altered)
        except (ValueError, TypeError, KeyError) as error:
            require(child.BytesValue == old_bytes, "rejected assembly changed the generated child bytes")
            return {"passed": True, "worker_pid": os.getpid(), "rejected": True, "fault": REQUEST["fault"], "exception": type(error).__name__, "diagnostic": str(error), "child_bytes_unchanged": True, "writer_output_count": 0, "runtime_input_file_reads": len(AUDIT.DeniedReads), "sdk_runtime_research_imports": 0, "native_acceptance": False, "public_writer_qualified": False}
        raise ValueError("complete assembly admitted its declared malformed input")
    candidate = MakeAssembly(child, inputs, occurrences, mate)
    state = candidate.StateValue
    require(candidate.ChildValue is child and old_bytes == child.BytesValue, "assembly changed its actual independently generated child")
    require(candidate.ConfigValue.RootValue is state.RootValue and state.ManagerValue.FieldsValue["f360"] is state.CurrentConfig,
            "assembly lost actual configuration and model identity")
    require(candidate.HeaderValue.FieldsValue["f38"] is candidate.TopHeader.FieldsValue["f38"], "assembly headers lost actual self file alias")
    require(candidate.ResolvedValue.RootsValue[-1] is state.GroupValue and candidate.MatesValue.RootsValue == (candidate.MateValue,), "assembly lost its actual resolved group or separate mate graph")
    references = candidate.OccurrenceValues
    require(references[0].FieldsValue["f3b0"] is references[1].FieldsValue["f3b0"], "repeated child must share one actual directory entry")
    require(all(ref.FieldsValue["f4f8"].FieldsValue["f50"] is ref for ref in references), "occurrence external backlinks lost actual identity")
    require(candidate.HeaderValue.FieldsValue["f30"].FieldsValue["items"] == (references[0].FieldsValue["f3b0"],), "direct child directory does not retain its actual native object")
    ids = [node.FieldsValue["f08"] for node in (state.RootValue, *state.FeatureValues, *references, candidate.MateValue)]
    require(len(ids) == len(set(ids)), "persistent model feature occurrence and mate ids collide")
    imports = sorted(name for name, module in tuple(sys.modules.items())
                     if str(getattr(module, "__file__", "")).startswith(str(ROOT / "re") + "/")
                     and name not in ("__main__", "SdkAssemblySettings", "SdkBlindPartSettings", "SdkAssemblyFaults"))
    require(not imports and not AUDIT.DeniedReads, "SDK assembly construction imported research logic or read runtime input")
    return {"passed": True, "worker_pid": os.getpid(), "scope": "complete SDK-only two ordinary occurrences of one generated plain boss and one aligned planar mate",
            "name": REQUEST["assembly"]["name"], "next_id": state.Allocator.NextValue, "wrapper_next_id": state.RootValue.FieldsValue["fd48"],
            "feature_count": len(state.FeatureValues), "occurrence_count": len(references), "mate_class": candidate.MateValue.ClassValue.NameValue,
            "occurrence_ids": [value.FieldsValue["f08"] for value in references], "mate_id": candidate.MateValue.FieldsValue["f08"],
            "actual_child_identity": True, "actual_occurrence_backlinks": True, "actual_directory_alias": True, "actual_model_alias": True,
            "actual_self_file_alias": True, "unique_persistent_ids": True, "child_bytes_unchanged": True,
            "config_map_counter": candidate.ConfigValue.MapValue.CounterValue, "resolved_map_counter": candidate.ResolvedValue.MapValue.CounterValue,
            "mates_map_base": candidate.MatesValue.MapBase, "mates_map_terminal": candidate.MatesValue.MapValue.CounterValue,
            "file_handles": file_handles(),
            "assembly": {"bytes": len(candidate.BytesValue), "sha256": sha256(candidate.BytesValue).hexdigest(), "blob": b64encode(candidate.BytesValue).decode("ascii"), "stream_order": list(candidate.StreamsValue),
                         "streams": {name: {"bytes": len(data), "sha256": sha256(data).hexdigest(), "data": b64encode(data).decode("ascii")} for name, data in candidate.StreamsValue.items()}},
            "child": {"bytes": len(child.BytesValue), "sha256": sha256(child.BytesValue).hexdigest(), "blob": b64encode(child.BytesValue).decode("ascii"), "stream_order": list(child.StreamsValue),
                      "streams": {name: {"bytes": len(data), "sha256": sha256(data).hexdigest(), "data": b64encode(data).decode("ascii")} for name, data in child.StreamsValue.items()}},
            "usage": {"config": candidate.ConfigValue.ReportValue, "resolved": candidate.ResolvedValue.ReportValue, "mates": candidate.MatesValue.ReportValue},
            "runtime_input_file_reads": len(AUDIT.DeniedReads), "sdk_runtime_research_imports": len(imports), "native_acceptance": False, "public_writer_qualified": False}


print(json.dumps(main(), sort_keys=True, allow_nan=False))
