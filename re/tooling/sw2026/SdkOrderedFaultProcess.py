from codecs import lookup
from dataclasses import replace
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
from convert.adapters.solidworks.Archive.Construction.Assembly.Headers.MakeAsmHeaders import MakeAsmHeaders
from convert.adapters.solidworks.Archive.Construction.Assembly.MakeAsmBase import MakeAsmBase
from convert.adapters.solidworks.Archive.Construction.Assembly.MakeAsmMateMut import MakeAsmMateMut
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.PutOccsMut import PutOccsMut
from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindPart
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from interchange.serialization.Deserialize import FromData
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors

from SdkOrderedFaults import FAULTS
CODECS = tuple(lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()


def snapshot(state, headers, references):
    return {"allocator_next": state.Allocator.NextValue, "allocations": len(state.Allocator.Allocations),
            "wrapper_counter": state.RootValue.FieldsValue["fd48"], "configuration_progress": state.CurrentConfig.FieldsValue["f85c"],
            "header_counters": [header.FieldsValue["f08"] for header in headers], "fixed_flags": [value.FieldsValue["f408"] for value in references],
            "log_ids": [[value.FieldsValue["f48"] for value in header.FieldsValue["f20"].FieldsValue["items"]] for header in headers]}


def malformed(name, state, headers, previous, mate):
    first = previous[0]
    wrapper = first.FieldsValue["f410"][0]["o"]
    if name == "missing_prior":
        previous = ()
    elif name == "duplicate_prior":
        previous = (first, first)
    elif name == "stale_header":
        headers[0].FieldsValue["f08"] -= 1
    elif name == "stale_config":
        state.CurrentConfig.FieldsValue["f85c"] -= 1
    elif name == "counter_reuse":
        state.RootValue.FieldsValue["fd48"] = 0
    elif name == "missing_log":
        headers[0].FieldsValue["f20"].FieldsValue["items"] = headers[0].FieldsValue["f20"].FieldsValue["items"][:1]
    elif name == "prior_owner":
        first.FieldsValue["owner"] = state.RootValue
    elif name == "wrapper_mate_id":
        wrapper.FieldsValue["f74"] = -1
    elif name == "wrapper_absolute_id":
        wrapper.FieldsValue["f78"] = 2
    elif name == "wrapper_endpoint_id":
        wrapper.FieldsValue["f7c"] = 1
    elif name == "prior_solved":
        first.FieldsValue["f3b8"] = 1
    elif name == "prior_alignment":
        first.FieldsValue["f3b4"] = 0
    elif name == "wrong_anchor":
        mate = replace(mate, FixedIndex=1 - mate.FixedIndex)
    elif name == "prior_name":
        mate = replace(mate, NameValue=first.FieldsValue["f18"].FieldsValue["f08"])
    elif name == "foreign_component":
        wrapper.FieldsValue["f58"].FieldsValue["f58"].FieldsValue["owner"] = None
    elif name == "missing_dimension":
        first.FieldsValue["f4b8"] = None
    elif name in ("late_dimension", "dimension_collision"):
        handle = first.FieldsValue["f4b8"].FieldsValue["f850"][0]["o"]
        handle.FieldsValue["ff0"].FieldsValue["f50"] = first.FieldsValue["f08"] if name == "late_dimension" else state.RootValue.FieldsValue["f08"]
    elif name == "replaced_prior_node":
        previous = (ArchiveNode(first.ClassValue, dict(first.FieldsValue)),)
    elif name == "replaced_dimension_node":
        handle = first.FieldsValue["f4b8"].FieldsValue["f850"][0]["o"]
        dimension = handle.FieldsValue["ff0"]
        handle.FieldsValue["ff0"] = ArchiveNode(dimension.ClassValue, dict(dimension.FieldsValue))
    else:
        raise ValueError("unknown ordered mate fault")
    return previous, mate


def main():
    request = REQUEST["request"]
    child = MakeBlindPart(FromData(request["child"]["document"]), settings(request["child"]["settings"]))
    inputs = assembly_settings(request["assembly"])
    state = MakeAsmBase(inputs)
    headers = MakeAsmHeaders(state, inputs)
    references = PutOccsMut(state, child, inputs, occurrence_settings(request["occurrences"]), headers)
    first = MakeAsmMateMut(state, child, inputs, mate_settings(request["mates"][0]), references, headers)
    previous, mate = malformed(REQUEST["fault"], state, headers, (first,), mate_settings(request["mates"][1]))
    before = snapshot(state, headers, references)
    try:
        MakeAsmMateMut(state, child, inputs, mate, references, headers, previous)
    except (ValueError, TypeError, KeyError) as error:
        after = snapshot(state, headers, references)
        if after != before:
            raise ValueError("rejected ordered mate changed actual publication state") from error
        return {"passed": True, "worker_pid": os.getpid(), "fault": REQUEST["fault"], "rejected": True, "exception": type(error).__name__, "diagnostic": str(error),
                "actual_parent_state_unchanged": True, "before": before, "after": after, "writer_output_count": 0, "runtime_input_file_reads": len(AUDIT.DeniedReads),
                "native_acceptance": False, "public_writer_qualified": False}
    raise ValueError("ordered mate admitted its declared malformed prior state")


print(json.dumps(main(), sort_keys=True, allow_nan=False))
