from __future__ import annotations

from base64 import b64encode
from codecs import lookup
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(sys.argv[1])
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(AUDIT.InspectEvent)

from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Configuration.ConfigSpec import ConfigSpec
from convert.adapters.solidworks.Archive.Construction.Configuration.ManagerInput import ManagerInput
from convert.adapters.solidworks.Archive.Construction.Header.HeaderInput import HeaderInput
from convert.adapters.solidworks.Archive.Construction.Header.MakePartHeader import MakePartHeader
from convert.adapters.solidworks.Archive.Construction.Model.PartRootInput import PartRootInput
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import FeatureTarget
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Presentation.MakePartRefs import MakePartRefs
from convert.adapters.solidworks.Archive.Construction.Presentation.StyleInput import StyleInput
from convert.adapters.solidworks.Archive.Construction.System.MakePartSysMut import MakePartSysMut
from convert.adapters.solidworks.Archive.Construction.System.SystemInput import SystemInput
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut

CODECS = tuple(lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()


def require(value, message):
    if not value:
        raise ValueError(message)


def unit_input(values):
    return UnitInput(values["length_unit"], values["angle_unit"], values["unit_system"], values["decimal_places"])


def construct(request):
    styles = request["styles"]
    style = StyleInput(styles["standard"], styles["font_name"], styles["line_style_name"], styles["language_id"],
                       tuple(styles["print_widths_m"]), tuple(styles["exclusion_names"]),
                       tuple(styles["task_labels"]), tuple(styles["cutlist_expressions"]))
    refs = MakePartRefs(style, unit_input(request["document_units"]), unit_input(request["analysis_units"]))
    manager = request["manager"]
    manager_input = ManagerInput(manager["name"], tuple(ConfigSpec(row["name"], row["description"], row["updated_at"])
                                                       for row in manager["configurations"]), manager["current"])
    system = request["system"]
    system_input = SystemInput(tuple(tuple(row) for row in system["folders"]), tuple(system["planes"].items()),
                               system["cabinet_name"], system["origin_name"], system["origin_axis"],
                               system["created_at"], system["construction_flag"])
    inputs = PartRootInput(request["name"], request["hatch_name"], request["version"])
    target = FeatureTarget(request["target"]["date_code"], request["target"]["parasolid_version"], request["version"])
    allocator = PersistentIds(request["next_id"], tuple(request["reserved_ids"]))
    graph = MakePartSysMut(inputs, refs, manager_input, system_input, target, allocator)
    return graph, allocator


def verify(graph, allocator, request):
    root, manager, features = graph.RootValue, graph.ManagerValue, graph.FeatureValues
    require(type(root) is ArchiveNode and len(features) == 17 and len({id(node) for node in features}) == 17,
            "system construction requires one concrete part and seventeen distinct system features")
    require(len(allocator.Allocations) == 18 and all(node not in {key[0] for key in allocator.Allocations} for node in graph.ConfigValues),
            "configuration ids consumed the global feature allocator")
    require(manager.FieldsValue["f08"] == -1 and [node.FieldsValue["f08"] for node in graph.ConfigValues] == list(range(len(graph.ConfigValues))),
            "configuration manager identity namespaces differ")
    require(manager.FieldsValue["f360"] is manager.FieldsValue["f368"] is graph.ConfigValues[request["manager"]["current"]],
            "current configuration aliases differ")
    require(root.FieldsValue["f2f8"] is None and not root.FieldsValue["f60"]["list"]["items"],
            "constructor part graph invented a manager pointer or embedded feature sequence")
    require(root.FieldsValue["f1e0"] is graph.SystemValues.FolderValues["moEnvFolder_c"],
            "environment folder is not the shared actual object")
    relations = root.FieldsValue["f9d0"]
    require(relations.FieldsValue["_equation_folder"] is graph.SystemValues.FolderValues["moEqnFolder_c"] and
            graph.SystemValues.FolderValues["moEqnFolder_c"].FieldsValue["_relation_manager"] is relations,
            "equation folder runtime ownership differs")
    require(root.FieldsValue["f990"].FieldsValue["owner"] is root, "self component lost its root cycle")
    for index, node in enumerate(graph.ConfigValues):
        require(node.FieldsValue["f85c"] == (allocator.NextValue - 1 if index == request["manager"]["current"] else 0),
                "configuration progress did not follow the active allocator lifecycle")
    origin = graph.OriginValue
    require(origin.SketchValue.FieldsValue["f138"] is origin.ProfileValue and
            origin.ProfileValue.FieldsValue["pd_f80"] is origin.SketchValue,
            "origin sketch lost its actual profile backlink")
    require(origin.PlaneReference.FieldsValue["f58"] is not root.FieldsValue["f990"] and
            origin.PlaneReference.FieldsValue["f58"].FieldsValue["owner"] is root,
            "origin wrapper did not retain an exclusive component copy")
    require(origin.PointValue.FieldsValue["f20"] == origin.SketchValue.FieldsValue["dims"]["nlog1"] == 1 and
            origin.Constraint.FieldsValue["h1"].FieldsValue["_point"] is origin.PointValue,
            "origin point relation ownership differs")
    require(root.FieldsValue["f0c"] == origin.ProfileValue.FieldsValue["f0c"] == 1 and
            all(node.FieldsValue["f0c"] == 0 for node in graph.SystemValues.FeatureValues),
            "constructor update state differs from the separate system initialization transition")
    require([node.FieldsValue["f18"].FieldsValue["f08"] for node in graph.SystemValues.PlaneValues.values()] ==
            [request["system"]["planes"][axis] for axis in ("z", "y", "x")], "principal plane creation order differs")


def malformed(request):
    cases = (("unsupported_version", ("version",), 18999),
             ("boolean_version", ("version",), True),
             ("unsupported_standard", ("styles", "standard"), 2),
             ("empty_font", ("styles", "font_name"), ""),
             ("short_print_widths", ("styles", "print_widths_m"), [0.001] * 7),
             ("language_out_of_range", ("styles", "language_id"), 65536),
             ("unsupported_length_unit", ("document_units", "length_unit"), "unknown"),
             ("bad_current_configuration", ("manager", "current"), 100),
             ("empty_configurations", ("manager", "configurations"), []),
             ("incomplete_system_folders", ("system", "folders"), request["system"]["folders"][:-1]),
             ("incomplete_principal_planes", ("system", "planes"), {"z": "only"}),
             ("unsupported_origin_plane", ("system", "origin_axis"), "oblique"),
             ("nonboolean_plane_state", ("system", "construction_flag"), 1),
             ("invalid_folder_epoch", ("system", "created_at"), -1))
    results = []
    for name, keys, replacement in cases:
        changed = json.loads(json.dumps(request))
        parent = changed
        for key in keys[:-1]:
            parent = parent[key]
        parent[keys[-1]] = replacement
        try:
            construct(changed)
        except (TypeError, ValueError) as error:
            results.append({"case": name, "rejected": True, "diagnostic": str(error)})
        else:
            raise ValueError("unsupported complete system request was accepted: " + name)
    return results


def main():
    graph, allocator = construct(REQUEST)
    verify(graph, allocator, REQUEST)
    provenance = REQUEST["provenance"]
    header_input = HeaderInput(provenance["author"], provenance["company"], provenance["comment"],
                               provenance["created_at"], provenance["modified_at"], provenance["updated_at"])
    model_header = MakePartHeader(graph.RootValue, header_input, allocator, True)
    top_header = MakePartHeader(graph.RootValue, header_input, allocator, False)
    configuration_bytes, configuration = WriteConfigMut(graph.RootValue, 19000, model_header)
    manager_usage = BodyUsage()
    manager_bytes = WriteCmgrMut(graph.ManagerValue, 19000, UsageValue=manager_usage)
    context = {"model_compressed_stream": 1, "model_is_part": 1, "cmgr_f658": graph.ManagerValue.FieldsValue["f658"]}
    resolved_bytes, resolved = WriteResolMut(graph.FeatureValues, None, 19000, configuration.MapValue, context)
    require(resolved.MapBase == configuration.MapValue.CounterValue, "resolved base is not the actual configuration snapshot")
    actual = {"Header2": WriteHeadGraph(top_header, 19000), "Contents/Config-0-ModelHeader": WriteHeadGraph(model_header, 19000),
              "Contents/Config-0": configuration_bytes, "Contents/CMgr": manager_bytes,
              "Contents/Config-0-ResolvedFeatures": resolved_bytes}
    require(not any(getattr(module, "__file__", "") and str(getattr(module, "__file__", "")).startswith(str(ROOT / "re")) for name, module in sys.modules.items() if name != "__main__"),
            "construction imported a research runtime dependency")
    return {"passed": True, "scope": "fresh ordinary part configuration and system subgraph from SDK constructors only",
            "root_id": graph.RootValue.FieldsValue["f08"], "next_id": allocator.NextValue,
            "feature_count": len(graph.FeatureValues), "configuration_count": len(graph.ConfigValues),
            "feature_ids": [node.FieldsValue["f08"] for node in graph.FeatureValues],
            "runtime_cache_count": len(graph.SystemValues.RuntimeCaches), "global_allocations": len(allocator.Allocations),
            "manager_local_namespace": True, "environment_alias": True, "exclusive_origin_component": True,
            "origin_fixed_relation": True, "pending_origin_update": True, "research_imports": 0,
            "config_map_counter": configuration.MapValue.CounterValue, "resolved_map_counter": resolved.MapValue.CounterValue,
            "usage": {"config": configuration.ReportValue, "manager": GetBodyReport(manager_usage), "resolved": resolved.ReportValue},
            "malformed": malformed(REQUEST),
            "streams": {name: {"bytes": len(data), "sha256": sha256(data).hexdigest(), "data": b64encode(data).decode("ascii")} for name, data in actual.items()},
            "runtime_input_file_reads": len(AUDIT.DeniedReads), "full_part_factory": False,
            "native_acceptance": False, "public_writer_qualified": False}


print(json.dumps(main(), sort_keys=True, allow_nan=False))
