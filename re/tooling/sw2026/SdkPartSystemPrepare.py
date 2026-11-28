from __future__ import annotations

from base64 import b64decode
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

from convert.adapters.solidworks.Archive.Bodies.BodyReport import GetBodyReport
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut

CODECS = tuple(lookup(name) for name in ("utf-16-le", "utf-8", "latin-1"))
REQUEST = json.load(sys.stdin)
AUDIT.BeginBuild()


def require(value, message):
    if not value:
        raise ValueError(message)


def require_node(node, class_name):
    require(type(node) is ArchiveNode and node.ClassValue == RuntimeClass(class_name, 1), "prepared graph has the wrong concrete owner: " + class_name)
    return node


def feature_name(node):
    return require_node(node.FieldsValue["f18"], "moNodeName_c").FieldsValue["f08"]


def check_manager(manager, built, request):
    fields = require_node(manager, "moConfigurationMgr_c").FieldsValue
    configs = tuple(row["o"] for row in fields["f370"]["items"])
    require(fields["f08"] == -1 and fields["f40c"] == len(configs) == built["configuration_count"], "prepared manager namespace differs")
    require(fields["f360"] is fields["f368"] is configs[request["manager"]["current"]], "prepared current configuration aliases differ")
    require(feature_name(manager) == request["manager"]["name"], "prepared manager name differs")
    for index, (node, authored) in enumerate(zip(configs, request["manager"]["configurations"], strict=True)):
        values = require_node(node, "moPartConfiguration_c").FieldsValue
        require(values["f08"] == index and values["f0c"] == 0 and feature_name(node) == authored["name"], "prepared configuration identity differs")
        require(values["f4a8"] == authored["description"] and values["f678"] == authored["updated_at"], "prepared configuration intent differs")
        require(values["f85c"] == (built["next_id"] - 1 if index == request["manager"]["current"] else 0), "prepared configuration allocator progress differs")
    return configs


def check_system(root, features, built, request):
    require(len(features) == built["feature_count"] == 17 and len({id(node) for node in features}) == 17, "prepared feature count or ownership differs")
    expected = list(request["system"]["folders"]) + [["moDetailCabinet_c", request["system"]["cabinet_name"]]]
    expected += [["moRefPlane_c", request["system"]["planes"][axis]] for axis in ("z", "y", "x")]
    expected += [["moOriginProfileFeature_c", request["system"]["origin_name"]]]
    for index, (node, (class_name, name)) in enumerate(zip(features, expected, strict=True)):
        require_node(node, class_name)
        require(feature_name(node) == name and node.FieldsValue["f08"] == built["feature_ids"][index], "prepared system identity differs")
        require(node.FieldsValue["f0c"] == int(index == 16), "prepared system update transition differs")
    folders = {node.ClassValue.NameValue: node for node in features[:12]}
    require(root.FieldsValue["f1e0"] is folders["moEnvFolder_c"], "configuration and resolved graphs duplicated the environment folder")
    require(folders["moMaterialFolder_c"].FieldsValue["flags380"] == 0x80000000, "material constructor Boolean encoding differs")
    ticks = (request["system"]["created_at"] + 11644473600) * 10_000_000
    for node in features[:12]:
        require((node.FieldsValue["f2a0"] & 0xFFFFFFFF) | ((node.FieldsValue["f2a4"] & 0xFFFFFFFF) << 32) == ticks,
                "folder provenance lost the authored native FILETIME")
    expected_normals = ((0.0, 0.0, 1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0))
    for node, normal in zip(features[13:16], expected_normals, strict=True):
        data = require_node(node.FieldsValue["f6f8"], "moDefaultRefPlnData_c")
        require(tuple(data.FieldsValue["normal"][axis] for axis in ("x", "y", "z")) == normal, "principal plane normal differs")
        require(node.FieldsValue["f6dc"] == (5 if request["system"]["construction_flag"] else 1), "explicit plane construction state differs")
    return {axis: node for axis, node in zip(("z", "y", "x"), features[13:16], strict=True)}


def check_origin(root, origin, planes, request):
    fields = origin.FieldsValue
    sketch = require_node(fields["pd_f80"], "sgSketch")
    require("f138" not in sketch.FieldsValue, "ordinary raw sketch invented a runtime profile backlink")
    require(fields["pd_f11c"] == -7 and fields["pd_f110"] is None, "origin native profile mode differs")
    reference = require_node(fields["pd_f78"], "moCompRefPlane_c")
    component = require_node(reference.FieldsValue["f58"], "moUnitComponent_c")
    require(component is not root.FieldsValue["f990"] and component.FieldsValue["owner"] is root, "origin component is not an exclusive owned copy")
    axis = request["system"]["origin_axis"]
    require(reference.FieldsValue["ff0"] == {"f00": planes[axis].FieldsValue["f08"], "f08": 2592000} and
            reference.FieldsValue["ff8"] is None and reference.FieldsValue["f100"] == {"x": 1, "y": 2, "z": 3}[axis], "origin principal support identity differs")
    points, dims = sketch.FieldsValue["points"], sketch.FieldsValue["dims"]
    require(len(points) == sketch.FieldsValue["npoints"] == 1 and len(dims["log_g1"]) == dims["nlog1"] == 1 and not sketch.FieldsValue["lines"],
            "origin point and constraint topology differs")
    point = points[0]["point"]
    require(point["pos"] == {"x": 0.0, "y": 0.0} and point["pflags"] == 0x1F and point["fe4"] == point["f0c"] == point["f20"] == 1,
            "origin marker or constraint reference count differs")
    logical = dims["log_g1"][0]["d"]
    require(logical["f80"] == 0x11 and logical["f90"] == 2 and logical["fa0"] == 0xFFFE, "origin logical fixed relation differs")
    handle = require_node(logical["h1"], "sgPointHandle")
    require(handle.FieldsValue["idx"] == 0 and "f18" not in handle.FieldsValue, "compact point handle lost its ordinary index encoding")
    require(sketch.FieldsValue["f140"]["f08"] == 2, "origin point creation counter differs")
    return {"origin_point_count": 1, "origin_fixed_relations": 1, "origin_component_owner_alias": True, "compact_origin_index": True}


def main():
    built, request = REQUEST["build"], REQUEST["request"]
    buffers = {name: b64decode(row["data"], validate=True) for name, row in built["streams"].items()}
    for name, data in buffers.items():
        require(len(data) == built["streams"][name]["bytes"] and sha256(data).hexdigest() == built["streams"][name]["sha256"], "generated subgraph stream custody differs")
    header = ReadHeaderGraph(buffers["Contents/Config-0-ModelHeader"], 19000)
    top_header = ReadHeaderGraph(buffers["Header2"], 19000)
    config = ReadConfigMut(buffers["Contents/Config-0"], 19000, header)
    manager = ReadCmgrMut(buffers["Contents/CMgr"], 19000)
    context = MakeLinkContext(config, manager)
    resolved = ReadResolvedMut(buffers["Contents/Config-0-ResolvedFeatures"], 19000, config.MapValue, context)
    root = require_node(config.RootValue, "moPart_c")
    require(root.FieldsValue["f08"] == built["root_id"] and feature_name(root) == request["name"], "prepared part identity differs")
    require(header.FieldsValue["f08"] == top_header.FieldsValue["f08"] == built["next_id"] and
            header.FieldsValue["fec"] == 1 and top_header.FieldsValue["fec"] == 0, "prepared header counter or model presence differs")
    require(root.FieldsValue["f2f8"] is None and not root.FieldsValue["f60"]["list"]["items"], "fresh part acquired an invented manager or feature list")
    check_manager(manager.RootValue, built, request)
    features = tuple(require_node(node, node.ClassValue.NameValue) for node in resolved.RootsValue)
    planes = check_system(root, features, built, request)
    origin_checks = check_origin(root, features[-1], planes, request)
    require(resolved.MapBase == config.MapValue.CounterValue == built["config_map_counter"] and resolved.MapValue.CounterValue == built["resolved_map_counter"], "linked map boundaries differ")
    original_entries = {entry.IndexValue: entry.EntryValue for entry in config.MapValue.EntriesValue}
    require(all(entry.EntryValue is original_entries[entry.IndexValue] for entry in resolved.MapValue.EntriesValue if entry.IndexValue in original_entries), "resolved prefix did not retain actual configuration aliases")
    config_bytes, repeated = WriteConfigMut(root, 19000, header)
    manager_usage = BodyUsage()
    manager_bytes = WriteCmgrMut(manager.RootValue, 19000, UsageValue=manager_usage)
    resolved_bytes, repeated_resolved = WriteResolMut(features, resolved.ExtraFields, 19000, repeated.MapValue, context)
    actual = {"Header2": WriteHeadGraph(top_header, 19000), "Contents/Config-0-ModelHeader": WriteHeadGraph(header, 19000),
              "Contents/Config-0": config_bytes, "Contents/CMgr": manager_bytes, "Contents/Config-0-ResolvedFeatures": resolved_bytes}
    comparisons = {name: {"bytes": len(data), "sha256": sha256(data).hexdigest(), "byte_identity": data == buffers[name]} for name, data in actual.items()}
    require(all(row["byte_identity"] for row in comparisons.values()), "SDK system graph failed complete stream byte identity")
    usage = {"config_load": config.ReportValue, "config_store": repeated.ReportValue, "manager_load": manager.ReportValue,
             "manager_store": GetBodyReport(manager_usage), "resolved_load": resolved.ReportValue, "resolved_store": repeated_resolved.ReportValue}
    require(all(row["completed"] and not row["missing_schemas"] and not row["provisional_schemas"] for row in usage.values()), "system graph has incomplete grammar")
    return {"passed": True, "scope": "independent SDK load and reserialization of complete fresh part system subgraph",
            "streams": comparisons, "usage": usage, "feature_count": len(features), "configuration_count": built["configuration_count"],
            "config_map_counter": config.MapValue.CounterValue, "resolved_map_counter": resolved.MapValue.CounterValue,
            "environment_alias": True, "independent_manager_namespace": True, "actual_map_prefix_aliases": True,
            **origin_checks, "runtime_input_file_reads": len(AUDIT.DeniedReads), "full_part_factory": False,
            "native_acceptance": False, "public_writer_qualified": False}


print(json.dumps(main(), sort_keys=True, allow_nan=False))
