from __future__ import annotations

from base64 import b64encode
from codecs import lookup
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(sys.argv[1])
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/tooling/sw2026"), str(ROOT / "re/tooling/sw2026/serial")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from Classes import registry
from builders.Part import construct_part
from builders.HeaderGraphBridge import generated_header_bytes
from defs.ConfigPart import direct_list_items
from convert.adapters.solidworks.Archive.Construction.Blind.BlindEndInput import BlindEndInput
from convert.adapters.solidworks.Archive.Construction.Blind.BlindEndRefs import BlindEndRefs
from convert.adapters.solidworks.Archive.Construction.Blind.MakeBlindEnd import MakeBlindEnd
from convert.adapters.solidworks.Archive.Construction.Blind.MakeBlindParam import MakeBlindParam
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import build_sldprt

REGISTRY = registry()
CODECS = tuple(lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()


def require(value, message):
    if not value:
        raise ValueError(message)


def reject(operation, label):
    try:
        operation()
    except (ValueError, TypeError, KeyError) as error:
        return {"case": label, "rejected": True, "exception": type(error).__name__, "diagnostic": str(error)}
    raise ValueError(f"malformed blind construction was accepted: {label}")


def malformed(inputs, refs, dimensions):
    result = [reject(lambda: BlindEndInput(inputs.DepthValue, False, 18999), "unsupported_version"),
              reject(lambda: BlindEndInput(inputs.DepthValue, True, 19000), "reverse_direction"),
              reject(lambda: BlindEndInput(True, False, 19000), "boolean_depth"),
              reject(lambda: BlindEndInput(0.0, False, 19000), "zero_depth"),
              reject(lambda: BlindEndInput(float("nan"), False, 19000), "nonfinite_depth"),
              reject(lambda: BlindEndInput(1e-15, False, 19000), "clamped_depth"),
              reject(lambda: MakeBlindParam(inputs, 5), "unsupported_parameter_role"),
              reject(lambda: MakeBlindEnd(inputs, BlindEndRefs(refs.ForwardValue, refs.ForwardValue, refs.ForwardDraft, refs.ReverseDraft, refs.FromEndValue)), "aliased_display")]
    dimension = dimensions[0].dimension
    previous = dimension.FieldsValue["f28"]
    dimension.FieldsValue["f28"] = MakeBlindParam(inputs, 3)
    try:
        result.append(reject(lambda: MakeBlindEnd(inputs, refs), "wrong_parameter_class"))
    finally:
        dimension.FieldsValue["f28"] = previous
    return result


def main():
    constructed = construct_part(registry=REGISTRY, **REQUEST)
    extrusion = constructed.extrusion
    require(extrusion is not None and constructed.revolution is None and constructed.blind_pocket is None,
            "SDK blind construction proof requires a single fresh boss")
    require(extrusion.condition == "blind" and not extrusion.reverse_direction and extrusion.from_offset is not None,
            "SDK blind construction proof requires its forward end and retained D19")
    inputs = BlindEndInput(REQUEST["document"]["depth_m"], False, 19000)
    dimensions = (*extrusion.dimensions, extrusion.from_offset)
    require(len(dimensions) == 5, "fresh blind factory must retain five actual dimension graphs")
    for ordinal, graph in zip((1, 2, 3, 4, 19), dimensions, strict=True):
        graph.dimension.FieldsValue["f28"] = MakeBlindParam(inputs, ordinal)
    old_end = extrusion.end_spec
    refs = BlindEndRefs(*(graph.display for graph in extrusion.dimensions), old_end["f140"])
    new_end = MakeBlindEnd(inputs, refs)
    require(new_end is not old_end and new_end.FieldsValue["f140"] is refs.FromEndValue,
            "SDK end owner must be fresh while retaining actual from end identity")
    extrusion.feature.FieldsValue["f818"] = new_end
    encoded, configuration = WriteConfigMut(constructed.model, 19000, constructed.model_header, ReadItems=direct_list_items)
    manager = ReadCmgrMut(constructed.streams["Contents/CMgr"], 19000)
    context = MakeLinkContext(configuration, manager)
    resolved, graph = WriteResolMut(constructed.features, None, 19000, configuration.MapValue, context)
    actual = {"Contents/Config-0": encoded, "Contents/CMgr": WriteCmgrMut(manager.RootValue, 19000),
              "Contents/Config-0-ModelHeader": generated_header_bytes(constructed.model_header, 19000),
              "Contents/Config-0-ResolvedFeatures": resolved,
              "Header2": WriteHeadGraph(ReadHeaderGraph(constructed.streams["Header2"], 19000), 19000)}
    comparisons = {name: {"bytes": len(data), "sha256": sha256(data).hexdigest(), "same_as_fresh_research_graph": data == constructed.streams[name]}
                   for name, data in actual.items()}
    require(all(row["same_as_fresh_research_graph"] for row in comparisons.values()), "SDK constructor changed the generated native graph bytes")
    reread = ReadResolvedMut(resolved, 19000, configuration.MapValue, context)
    require(WriteResolMut(reread.RootsValue, reread.ExtraFields, 19000, configuration.MapValue, context)[0] == resolved,
            "SDK constructed graph failed its memory round trip")
    original_fields = new_end.FieldsValue["f18"]
    malformed_cases = malformed(inputs, refs, dimensions)
    require(new_end.FieldsValue["f18"] is original_fields, "malformed checks changed the constructed owner")
    require(WriteResolMut(constructed.features, None, 19000, configuration.MapValue, context)[0] == resolved,
            "malformed checks changed the generated graph bytes")
    streams = {**constructed.streams, **actual}
    blob = build_sldprt(streams)
    return {"scope": "fresh ordinary forward blind parameter and end specification construction", "passed": True,
            "depth_m": inputs.DepthValue, "parameter_names": [f"D{ordinal}" for ordinal in (1, 2, 3, 4, 19)],
            "dimension_ids": [item.dimension.FieldsValue["f50"] for item in dimensions],
            "parameter_node_ids": [item.dimension.FieldsValue["f28"].FieldsValue["f08"] for item in dimensions],
            "retained_from_end": True, "streams": comparisons, "malformed": malformed_cases,
            "config_map_counter": configuration.MapValue.CounterValue, "resolved_map_counter": graph.MapValue.CounterValue,
            "resolved_usage": graph.ReportValue, "runtime_input_file_reads": len(AUDIT.DeniedReads),
            "blob": b64encode(blob).decode("ascii"), "bytes": len(blob), "sha256": sha256(blob).hexdigest(),
            "memory_roundtrip": True, "native_acceptance": False, "public_writer_qualified": False}


print(json.dumps(main(), sort_keys=True, allow_nan=False))
