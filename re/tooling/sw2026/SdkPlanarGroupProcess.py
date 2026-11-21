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

from SdkAssemblySettings import assembly_settings, occurrence_settings
from SdkBlindPartSettings import settings
from SdkNativeRoundTrips import roundtrips
from SdkPlanarGroupSettings import group_settings
from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.MakePlanarGroup import MakePlanarGroup
from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindPart
from convert.adapters.solidworks.Archive.Construction.Part.MakeRectDimPart import MakeRectDimPart
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import RectDimInput
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
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


def artifact(blob, streams):
    return {"bytes": len(blob), "sha256": sha256(blob).hexdigest(), "blob": b64encode(blob).decode("ascii"), "stream_order": list(streams),
            "streams": {name: {"bytes": len(data), "sha256": sha256(data).hexdigest(), "data": b64encode(data).decode("ascii")} for name, data in streams.items()}}


def endpoint(wrapper, references):
    comp = wrapper.FieldsValue["f58"]
    chain = comp.FieldsValue["f58"].FieldsValue["f20"]
    external, = (row["o"] for row in chain.FieldsValue["f08"].FieldsValue["f08"])
    occurrence = external.FieldsValue["f50"]
    matches = [index for index, reference in enumerate(references) if reference is occurrence]
    require(len(matches) == 1 and occurrence.FieldsValue["f4f8"] is external, "a planar endpoint lost its unique actual occurrence backlink")
    return {"occurrence": matches[0], "datum_id": comp.FieldsValue["ff0"]["f00"],
            "selection": [wrapper.FieldsValue[key] for key in ("f74", "f78", "f7c")]}


def main():
    require(set(REQUEST) == {"assembly", "child", "occurrences", "mates", "fixed_occurrence"}, "complete planar groups require their exact declared neutral shape")
    inputs = REQUEST["child"]
    require(set(inputs) in ({"document", "settings"}, {"document", "settings", "rectangle_dimensions"}), "the group child has unsupported or missing neutral state")
    child_settings = settings(inputs["settings"])
    document = FromData(inputs["document"])
    if "rectangle_dimensions" in inputs:
        raw = inputs["rectangle_dimensions"]
        require(set(raw) == {"width_text_m", "height_text_m", "route_centerline"}, "rectangle presentation must be explicit and complete")
        dims = RectDimInput(tuple(raw["width_text_m"]), tuple(raw["height_text_m"]), child_settings.DesignIntent, child_settings.SelectedLeader, raw["route_centerline"])
        child = MakeRectDimPart(document, child_settings, dims)
    else:
        child = MakeBlindPart(document, child_settings)
    require(all(set(row) == {"name", "origin", "u", "v"} for row in REQUEST["occurrences"]), "group occurrences include unqualified state")
    candidate = MakePlanarGroup(child, assembly_settings(REQUEST["assembly"]), occurrence_settings(REQUEST["occurrences"]), group_settings(REQUEST["mates"]), REQUEST["fixed_occurrence"])
    total, proofs = 0, {}
    for name, value, has_mates in (("assembly", candidate, True), ("child", child, False)):
        link, mates, manager, cmgr, rows = roundtrips(SldprtArchive.from_bytes(value.BytesValue, name), has_mates)
        if has_mates:
            require(len(mates.RootsValue) == len(candidate.MateValues), "typed MatesList changed the complete authored mate count")
        proofs[name] = rows
        total += len(rows)
    endpoints = []
    dimensions = []
    for index, (node, request) in enumerate(zip(candidate.MateValues, REQUEST["mates"], strict=True)):
        rows = [endpoint(row["o"], candidate.OccurrenceValues) for row in node.FieldsValue["f410"]]
        require([row["occurrence"] for row in rows] == [row["occurrence"] for row in request["endpoints"]], "an ordered mate changed its explicit endpoint indices")
        require(all(row["selection"] == [node.FieldsValue["f08"], 2 * index + ordinal, ordinal] for ordinal, row in enumerate(rows)), "resolved wrapper allocation lost actual mate order")
        require(all(row["datum_id"] == child.SystemValue.SystemValues.PlaneValues[end["axis"]].FieldsValue["f08"] for row, end in zip(rows, request["endpoints"], strict=True)), "an ordered mate changed its actual child datum identity")
        if node.ClassValue.NameValue == "moMateDistanceDim_c":
            handle, = (row["o"] for row in node.FieldsValue["f4b8"].FieldsValue["f850"])
            dimensions.append(handle.FieldsValue["ff0"].FieldsValue["f50"])
            require(dimensions[-1] < node.FieldsValue["f08"], "distance dimension must allocate before its mate")
        endpoints.append({"kind": request["kind"], "name": request["name"], "mate_id": node.FieldsValue["f08"], "endpoints": rows})
    fixed = [index for index, value in enumerate(candidate.OccurrenceValues) if value.FieldsValue["f408"]]
    require(fixed == [REQUEST["fixed_occurrence"]] and candidate.StateValue.RootValue.FieldsValue["fd48"] == 2 * len(candidate.MateValues), "complete group anchor or wrapper counter differs")
    imports = sorted(name for name, module in tuple(sys.modules.items()) if str(getattr(module, "__file__", "")).startswith(str(ROOT / "re") + "/")
                     and name not in ("__main__", "SdkAssemblySettings", "SdkBlindPartSettings", "SdkNativeRoundTrips", "SdkPlanarGroupSettings"))
    require(not imports and not AUDIT.DeniedReads, "SDK group construction imported research rules or read runtime inputs")
    return {"passed": True, "worker_pid": os.getpid(), "assembly": artifact(candidate.BytesValue, candidate.StreamsValue), "child": artifact(child.BytesValue, child.StreamsValue),
            "occurrence_count": len(candidate.OccurrenceValues), "mate_count": len(candidate.MateValues), "endpoints": endpoints, "fixed_indices": fixed,
            "dimension_ids": dimensions, "next_id": candidate.StateValue.Allocator.NextValue, "wrapper_next_id": candidate.StateValue.RootValue.FieldsValue["fd48"],
            "round_trips": total, "proofs": proofs, "runtime_input_file_reads": len(AUDIT.DeniedReads), "sdk_runtime_research_imports": len(imports),
            "heldout_inputs_read": 0, "native_processes_started": 0, "native_acceptance": False, "public_writer_qualified": False}


print(json.dumps(main(), sort_keys=True, allow_nan=False))
