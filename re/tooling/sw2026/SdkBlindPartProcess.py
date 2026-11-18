from __future__ import annotations

from base64 import b64encode
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from math import fsum, hypot
from pathlib import Path
import sys

ROOT = Path(sys.argv[1])
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "re/tooling/sw2026")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from SdkBlindPartSettings import settings
from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindPart
from convert.adapters.solidworks.Archive.Construction.Part.MakePolygonBlindPart import MakePolygonBlindPart
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
from interchange.Features.FeatureExtrude import ExtrudeEnd
from interchange.serialization.Deserialize import FromData

CODECS = tuple(lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
REQUEST = json.load(sys.stdin)
PROFILE = sys.argv[2] if len(sys.argv) == 3 else "rectangle"
BUILD = {"rectangle": MakeBlindPart, "polygon": MakePolygonBlindPart}[PROFILE]
AUDIT.BeginBuild()


def require(value, message):
    if not value:
        raise ValueError(message)


def altered_feature(document, **changes):
    feature = document.feature_timeline[0]
    definition = replace(feature.definition, **changes)
    return replace(document, feature_timeline=(replace(feature, definition=definition),))


def malformed(document, inputs):
    candidates = (
        ("reverse_direction", altered_feature(document, reversed=True), inputs),
        ("mid_plane", altered_feature(document, symmetric=True), inputs),
        ("through_all", altered_feature(document, end_condition=ExtrudeEnd.KThroughAll), inputs),
        ("inactive_configuration", replace(document, configurations=(replace(document.configurations[0], active=False),)), inputs),
        ("duplicate_sketch", replace(document, sketches=document.sketches * 2), inputs),
        ("native_payload", replace(document, metadata={**document.metadata, "extra": "unprojected"}), inputs),
        ("missing_loop", replace(document, sketches=(replace(document.sketches[0], closed_profile_entity_ids=()),)), inputs),
        ("wrong_parameter_name", replace(document, parameters=(replace(document.parameters[0], name="unknown"),)), inputs),
        ("wrong_parameter_owner", replace(document, parameters=(replace(document.parameters[0], owner_id="sketch/profile"),)), inputs),
        ("wrong_body_owner", replace(document, bodies=(replace(document.bodies[0], final_feature_id="missing"),)), inputs),
        ("negative_density", document, replace(inputs, DensityValue=-1.0)),
        ("wrong_front_support", document, replace(inputs, SystemValue=replace(inputs.SystemValue, OriginAxis="x"))),
    )
    if PROFILE == "polygon":
        sketch = document.sketches[0]
        first = sketch.entities[0]
        reversed_line = replace(first.geometry, start=first.geometry.end, end=first.geometry.start)
        for name, line in (
            ("broken_ordered_endpoint", replace(first, geometry=reversed_line)),
            ("construction_loop_edge", replace(first, construction=True)),
            ("fixed_loop_edge", replace(first, fixed=True)),
        ):
            candidate = replace(document, sketches=(replace(sketch, entities=(line, *sketch.entities[1:])),))
            candidates += ((name, candidate, inputs),)
    result = []
    for name, candidate, values in candidates:
        try:
            BUILD(candidate, values)
        except (ValueError, TypeError, KeyError) as error:
            result.append({"case": name, "rejected": True, "exception": type(error).__name__, "diagnostic": str(error)})
        else:
            raise ValueError("malformed complete neutral part was accepted: " + name)
    return result


def prism(vertices, depth):
    following = (*vertices[1:], vertices[0])
    edges = tuple(zip(vertices, following, strict=True))
    cross = tuple(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in edges)
    double_area = fsum(cross)
    area = abs(double_area) / 2
    perimeter = fsum(hypot(x2 - x1, y2 - y1) for (x1, y1), (x2, y2) in edges)
    center = [fsum((start[axis] + end[axis]) * weight for (start, end), weight in zip(edges, cross, strict=True))
              / (3 * double_area) for axis in (0, 1)]
    return {"body_count": 1, "volume_m3": area * depth, "area_m2": 2 * area + perimeter * depth,
            "com_m": [*center, depth / 2]}


def main():
    document = FromData(REQUEST["document"])
    require(type(document) is CadDocument, "process must receive a real serialized neutral cad document")
    inputs = settings(REQUEST["settings"])
    candidate = BUILD(document, inputs)
    require(candidate.ConfigValue.RootValue is candidate.SystemValue.RootValue, "candidate lost its actual configuration model alias")
    require(candidate.HeaderValue.FieldsValue["f38"] is candidate.TopHeader.FieldsValue["f38"], "headers must share the actual self file node")
    require(candidate.CurrentConfig is candidate.SystemValue.ManagerValue.FieldsValue["f360"], "candidate lost its actual active configuration")
    require(candidate.ManagerHeader.ClassValue == RuntimeClass("dmConfigMgrHeader_c", 1) and candidate.ManagerHeader.FieldsValue["f60"] == inputs.OutputValue.SavedAt,
            "candidate lost its actual generated manager header save event")
    require(candidate.ResolvedValue.RootsValue[-2] is candidate.ProfileValue.ProfileValue and candidate.ResolvedValue.RootsValue[-1] is candidate.BossValue.FeatureValue,
            "candidate lost its actual profile and boss roots")
    require(candidate.BossValue.FeatureValue.FieldsValue["f60"]["list"]["items"][0]["o"] is candidate.ProfileValue.ProfileValue,
            "boss dependency does not refer to the actual generated profile")
    dimensions = (*candidate.BossValue.DimensionsValue, candidate.BossValue.FromValue)
    identifiers = [graph.DimensionValue.FieldsValue["f50"] for graph in dimensions]
    require(len(dimensions) == len(set(identifiers)) == 5, "five real dimension lifetimes must consume independent ids")
    require(all(graph.ParameterValue.FieldsValue["f08"] == -1 and graph.DimensionValue.FieldsValue["retaining_handles"] == (graph.HandleValue,) and graph.HandleValue.FieldsValue["ff0"] is graph.DimensionValue for graph in dimensions),
            "dimension handle or unassigned parameter identity differs")
    require(all(type(node) is ArchiveNode for node in (candidate.SystemValue.RootValue, candidate.ProfileValue.ProfileValue, candidate.ProfileValue.GeometryValue.SketchValue,
        candidate.BossValue.FeatureValue, *(node for graph in dimensions for node in (graph.ParameterValue, graph.DimensionValue, graph.HandleValue, graph.DisplayValue)))), "candidate must use plain SDK archive nodes")
    plan = candidate.PlanValue
    width, height, depth = plan.WidthValue, plan.HeightValue, plan.DepthValue
    volume = width * height * depth
    bounds = {"body_count": 1, "volume_m3": volume, "area_m2": 2 * (width * height + width * depth + height * depth),
              "com_m": [sum(point[0] for point in plan.VerticesValue) / 4, sum(point[1] for point in plan.VerticesValue) / 4, depth / 2]}
    if PROFILE == "polygon":
        bounds = prism(plan.VerticesValue, depth)
    imports = sorted(name for name, module in tuple(sys.modules.items())
                     if str(getattr(module, "__file__", "")).startswith(str(ROOT / "re") + "/")
                     and name not in ("__main__", "SdkBlindPartSettings"))
    require(not imports, "SDK-only construction imported research implementation: " + repr(imports))
    scope = ("complete SDK-only plain forward blind boss candidate from a real neutral document" if PROFILE == "rectangle"
             else "complete SDK-only straight polygon and forward blind boss from a real neutral document")
    return {"passed": True, "scope": scope,
            "name": plan.NameValue, "native_path": inputs.OutputValue.PathName, "root_id": candidate.SystemValue.RootValue.FieldsValue["f08"],
            "next_id": candidate.HeaderValue.FieldsValue["f08"], "feature_count": len(candidate.ResolvedValue.RootsValue),
            "configuration_count": len(candidate.SystemValue.ConfigValues), "dimension_ids": identifiers,
            "parameter_names": [graph.ParameterValue.FieldsValue["f18"].FieldsValue["f08"] for graph in dimensions],
            "depth_m": depth, "vertices_m": plan.VerticesValue, "analytic_geometry": bounds,
            "actual_model_alias": True, "actual_active_configuration": True, "actual_profile_dependency": True,
            "actual_self_file_alias": True, "actual_manager_header": True, "plain_archive_nodes": True, "retained_from_dimension": True,
            "config_map_counter": candidate.ConfigValue.MapValue.CounterValue, "resolved_map_counter": candidate.ResolvedValue.MapValue.CounterValue,
            "usage": {"config": candidate.ConfigValue.ReportValue, "resolved": candidate.ResolvedValue.ReportValue},
            "malformed": malformed(document, inputs),
            "streams": {name: {"bytes": len(data), "sha256": sha256(data).hexdigest(), "data": b64encode(data).decode("ascii")} for name, data in candidate.StreamsValue.items()},
            "bytes": len(candidate.BytesValue), "sha256": sha256(candidate.BytesValue).hexdigest(), "blob": b64encode(candidate.BytesValue).decode("ascii"),
            "runtime_input_file_reads": len(AUDIT.DeniedReads), "sdk_runtime_research_imports": len(imports),
            "native_acceptance": False, "public_writer_qualified": False}


print(json.dumps(main(), sort_keys=True, allow_nan=False))
