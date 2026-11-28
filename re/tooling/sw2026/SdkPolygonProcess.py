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
from convert.adapters.solidworks.Archive.Construction.Sketch.MakePolygon import MakePolygon
from convert.adapters.solidworks.Archive.Construction.Sketch.PolygonInput import PolygonInput
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
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
    raise ValueError(f"malformed polygon construction was accepted: {label}")


def malformed(inputs, profile):
    invalid_rings = (
        ("too_few_vertices", ((0.0, 0.0), (1.0, 0.0))),
        ("repeated_closure", ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (0.0, 0.0))),
        ("zero_area", ((0.0, 0.0), (1.0, 0.0), (2.0, 0.0))),
        ("adjacent_overlap", ((0.0, 0.0), (2.0, 0.0), (1.0, 0.0), (1.0, 1.0))),
        ("crossed_ring", ((0.0, 0.0), (3.0, 2.0), (0.0, 3.0), (2.0, 0.0))),
        ("nonadjacent_touch", ((0.0, 0.0), (3.0, 0.0), (3.0, 3.0), (1.0, 0.0), (0.0, 3.0))),
        ("nonfinite_position", ((0.0, 0.0), (1.0, float("nan")), (0.0, 1.0))),
        ("boolean_coordinate", ((False, 0.0), (1.0, 0.0), (0.0, 1.0))),
        ("wrong_coordinate_width", ((0.0, 0.0), (1.0, 0.0, 2.0), (0.0, 1.0))),
    )
    result = [reject(lambda vertices=vertices: PolygonInput(vertices, 19000), label) for label, vertices in invalid_rings]
    result.append(reject(lambda: PolygonInput(inputs.VerticesValue, 18999), "unsupported_version"))
    result.append(reject(lambda: PolygonInput(inputs.VerticesValue, True), "boolean_version"))
    fields = dict(profile.FieldsValue)
    fields["pd_f110"] = profile
    result.append(reject(lambda: MakePolygon(inputs, ArchiveNode(profile.ClassValue, fields)), "derived_profile"))
    fields = dict(profile.FieldsValue)
    fields["f08"] = -1
    result.append(reject(lambda: MakePolygon(inputs, ArchiveNode(profile.ClassValue, fields)), "unallocated_profile"))
    result.append(reject(lambda: MakePolygon(inputs, ArchiveNode(ExternalClass(profile.ClassValue.NameValue, 1), dict(profile.FieldsValue))), "external_class_placeholder"))
    return result


def main():
    output = {"path_name": rf"C:\KitConstruction\{REQUEST['document']['name']}.SLDPRT",
              "saved_at": REQUEST["provenance"]["modified_at"]}
    constructed = construct_part(registry=REGISTRY, **REQUEST, output=output)
    require(constructed.extrusion is not None and constructed.revolution is None and constructed.blind_pocket is None,
            "SDK polygon construction proof requires a single fresh polygon boss")
    profile = constructed.profile.profile
    inputs = PolygonInput(REQUEST["document"]["vertices_m"], 19000)
    graph = MakePolygon(inputs, profile)
    require(all(type(node) is ArchiveNode for node in (graph.SketchValue, *graph.PointValues, *graph.LineValues)),
            "SDK polygon factory must construct plain archive nodes")
    require(graph.SketchValue.FieldsValue["f138"] is profile, "SDK sketch lost its actual profile backlink")
    profile.FieldsValue["pd_f80"] = graph.SketchValue
    encoded, configuration = WriteConfigMut(constructed.model, 19000, constructed.model_header, ReadItems=direct_list_items)
    manager = ReadCmgrMut(constructed.streams["Contents/CMgr"], 19000)
    context = MakeLinkContext(configuration, manager)
    resolved, resolved_graph = WriteResolMut(constructed.features, None, 19000, configuration.MapValue, context)
    actual = {"Contents/Config-0": encoded, "Contents/CMgr": WriteCmgrMut(manager.RootValue, 19000),
              "Contents/Config-0-ModelHeader": generated_header_bytes(constructed.model_header, 19000),
              "Contents/Config-0-ResolvedFeatures": resolved,
              "Header2": WriteHeadGraph(ReadHeaderGraph(constructed.streams["Header2"], 19000), 19000)}
    comparisons = {name: {"bytes": len(data), "sha256": sha256(data).hexdigest(), "same_as_fresh_research_graph": data == constructed.streams[name]}
                   for name, data in actual.items()}
    require(all(row["same_as_fresh_research_graph"] for row in comparisons.values()), "SDK polygon changed fresh generated native stream bytes")
    malformed_cases = malformed(inputs, profile)
    require(WriteResolMut(constructed.features, None, 19000, configuration.MapValue, context)[0] == resolved,
            "malformed checks changed the generated graph bytes")
    blob = build_sldprt({**constructed.streams, **actual})
    handles = tuple(point.FieldsValue[name] for point in graph.PointValues for name in ("h1", "h2"))
    require(len({id(handle) for handle in handles}) == 2 * len(inputs.VerticesValue), "endpoint handles must have independent identities")
    return {"scope": "fresh ordinary local closed polygon geometry construction", "passed": True,
            "vertices_m": inputs.VerticesValue, "point_count": len(graph.PointValues), "line_count": len(graph.LineValues),
            "independent_handle_count": len(handles), "plain_archive_nodes": True, "profile_backlink": True,
            "streams": comparisons, "malformed": malformed_cases,
            "config_map_counter": configuration.MapValue.CounterValue, "resolved_map_counter": resolved_graph.MapValue.CounterValue,
            "resolved_usage": resolved_graph.ReportValue, "runtime_input_file_reads": len(AUDIT.DeniedReads),
            "blob": b64encode(blob).decode("ascii"), "bytes": len(blob), "sha256": sha256(blob).hexdigest(),
            "native_acceptance": False, "public_writer_qualified": False}


print(json.dumps(main(), sort_keys=True, allow_nan=False))
