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
from convert.adapters.solidworks.Archive.Construction.AssemblySets.MakeOrderedAsm import MakeOrderedAsm
from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindPart
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


def artifact(data, streams):
    return {"bytes": len(data), "sha256": sha256(data).hexdigest(), "blob": b64encode(data).decode("ascii"), "stream_order": list(streams),
            "streams": {name: {"bytes": len(blob), "sha256": sha256(blob).hexdigest(), "data": b64encode(blob).decode("ascii")} for name, blob in streams.items()}}


def main():
    child_input = REQUEST["child"]
    child = MakeBlindPart(FromData(child_input["document"]), settings(child_input["settings"]))
    candidate = MakeOrderedAsm(child, assembly_settings(REQUEST["assembly"]), occurrence_settings(REQUEST["occurrences"]), tuple(mate_settings(row) for row in REQUEST["mates"]))
    state = candidate.StateValue
    require(candidate.ChildValue is child and candidate.ConfigValue.RootValue is state.RootValue, "ordered assembly lost actual generated model identity")
    require(candidate.MatesValue.RootsValue == candidate.MateValues, "ordered assembly omitted an actual authored mate")
    require(state.RootValue.FieldsValue["fd48"] == 2 * len(candidate.MateValues), "ordered assembly wrapper counter differs")
    identifiers = [node.FieldsValue["f08"] for node in (state.RootValue, *state.FeatureValues, *candidate.OccurrenceValues, *candidate.MateValues)]
    dimensions = []
    for mate in candidate.MateValues:
        if mate.ClassValue.NameValue == "moMateDistanceDim_c":
            handle, = (row["o"] for row in mate.FieldsValue["f4b8"].FieldsValue["f850"])
            dimension = handle.FieldsValue["ff0"]
            dimensions.append(dimension.FieldsValue["f50"])
            require(dimension.FieldsValue["f50"] < mate.FieldsValue["f08"], "ordered distance allocated its mate before the real dimension")
    require(len(set((*identifiers, *dimensions))) == len(identifiers) + len(dimensions), "ordered persistent ids collide")
    require(candidate.HeaderValue.FieldsValue["f08"] == state.Allocator.NextValue and state.CurrentConfig.FieldsValue["f85c"] == state.Allocator.NextValue - 1,
            "ordered publication header and configuration differ")
    imports = sorted(name for name, module in tuple(sys.modules.items()) if str(getattr(module, "__file__", "")).startswith(str(ROOT / "re") + "/")
                     and name not in ("__main__", "SdkAssemblySettings", "SdkBlindPartSettings"))
    require(not imports and not AUDIT.DeniedReads, "ordered SDK construction imported research logic or read runtime input")
    return {"passed": True, "worker_pid": os.getpid(), "scope": "complete SDK-only ordered ordinary planar mates on one actual generated plain child",
            "assembly": artifact(candidate.BytesValue, candidate.StreamsValue), "child": artifact(child.BytesValue, child.StreamsValue),
            "mate_classes": [value.ClassValue.NameValue for value in candidate.MateValues], "mate_ids": [value.FieldsValue["f08"] for value in candidate.MateValues],
            "dimension_ids": dimensions, "next_id": state.Allocator.NextValue, "wrapper_next_id": state.RootValue.FieldsValue["fd48"],
            "actual_child_identity": True, "all_authored_mates_present": True, "unique_persistent_ids": True,
            "config_map_counter": candidate.ConfigValue.MapValue.CounterValue, "resolved_map_counter": candidate.ResolvedValue.MapValue.CounterValue,
            "mates_map_base": candidate.MatesValue.MapBase, "mates_map_terminal": candidate.MatesValue.MapValue.CounterValue,
            "runtime_input_file_reads": len(AUDIT.DeniedReads), "sdk_runtime_research_imports": len(imports), "native_acceptance": False, "public_writer_qualified": False}


print(json.dumps(main(), sort_keys=True, allow_nan=False))
