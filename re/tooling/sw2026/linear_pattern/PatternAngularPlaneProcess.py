from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent), str(HERE.parents[1]), str(HERE.parents[1] / "serial")]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
sys.addaudithook(audit.InspectEvent)

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeBlindMut import MakeBlindMut
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import CheckPartInput
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartProfMut import MakePartProfMut
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectPlain import ProjectPlain
from convert.adapters.solidworks.Archive.Construction.Part.SelectBlindEnd import SelectBlindEnd
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadLogItems import ReadLogItems
from convert.adapters.solidworks.Archive.Counts.ReadCount import ReadCount
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName, RequireNode
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
from interchange.serialization.Deserialize import FromData

from CheckPatternAngleOwners import check_angles, node_fields, point, require
from MakePatternAngularPlane import AngularPlaneIntent, make_angular_plane_mut
from MakePatternAnnotationCatalog import add_catalog_mut
from MakePatternHingeAxis import make_hinge_mut
from PatternAngleArc import make_angle_arc_fields
from PatternAngleWire import ANGLE_PLANE, INTERFACE, read_resolved, write_resolved
from PatternHingeGeometry import ORIGIN
from PatternHingeWire import write_roots


def snapshot_signature(snapshot):
    return (snapshot.CounterValue, tuple((row.IndexValue,
             row.EntryValue.ClassValue if isinstance(row.EntryValue, ArchiveNode) else row.EntryValue)
             for row in snapshot.EntriesValue))


def check_fresh_owners(plane, graph, system, allocator):
    data = node_fields(plane.FieldsValue["f6f8"], ANGLE_PLANE)
    display, handle, dim, param = graph.DisplayValue, graph.HandleValue, graph.DimensionValue, graph.ParameterValue
    roles = (display, handle, dim, param)
    require(plane.FieldsValue["owner"] is system.RootValue and data["owner"] is plane
            and all(node.FieldsValue["owner"] is plane for node in roles)
            and len(set(roles)) == len(roles) and data["f150"] is display and display.FieldsValue["f850"][0]["o"] is handle
            and handle.FieldsValue["ff0"] is dim and dim.FieldsValue["f28"] is param
            and dim.FieldsValue["retaining_handles"] == (handle,) and dim.FieldsValue["refcount"] == 1
            and allocator.Allocations[(dim, "f50")] == dim.FieldsValue["f50"]
            and allocator.Allocations[(plane, "f08")] == plane.FieldsValue["f08"]
            and not any(node is param for node, _ in allocator.Allocations),
            "fresh plane, dimension, parameter and retaining handle have incorrect graph ownership")


def check_read_owners(roots, model, headers, ends, intent, epoch):
    tree = check_angles(model, roots, headers, ends, intent.angle_rad)
    hinge, plane = roots[-2:]
    require(hinge.ClassValue.NameValue == "moRefAxis_c" and plane.ClassValue.NameValue == "moRefPlane_c"
            and ReadNodeName(plane) == intent.name and plane.FieldsValue["f08"] == tree["feature"]["id"],
            "the actual selected hinge and angle plane changed root order")
    data = node_fields(plane.FieldsValue["f6f8"], ANGLE_PLANE)
    display_node = RequireNode(data["f150"], "moDisplayAngularDim_c")
    display = display_node.FieldsValue
    dim = node_fields(node_fields(display["f850"][0]["o"], "moFeatureDimHandle_c")["ff0"], "AngleDim_c")
    param = node_fields(dim["f28"], "moAngleParameter_c")
    expected = make_angle_arc_fields(*ends, intent.angle_rad)
    require(all(display[key] == value for key, value in expected.items())
            and display["ff80"] == intent.selected_leader and point(display["ff68"]) == intent.shifted_point_m
            and bool(display["fb60"] & 0x100) == intent.design_intent and param["f08"] == -1,
            "ordinary angular display changed an actual arc, presentation or parameter owner")
    plane_id, hinge_id = plane.FieldsValue["f08"], hinge.FieldsValue["f08"]
    require(hinge_id < dim["f50"] < plane_id
            and all(header.FieldsValue["f08"] == plane_id + 1 for header in headers)
            and all(DatumTime(header, identity) == epoch for header in headers for identity in (hinge_id, plane_id)),
            "shared allocator order or creation provenance changed in the serialized headers")
    logs = tuple(tuple(log.FieldsValue["f48"] for log in ReadLogItems(header.FieldsValue["f20"], "moLogs_c"))
                 for header in headers)
    require(logs[0] == logs[1] == (model.FieldsValue["f08"], hinge_id, plane_id),
            "header creation events must join the actual model, hinge and plane in authored order")
    tree["style"] = {"selected_leader": display["ff80"], "shifted_point_m": point(display["ff68"]),
                     "design_intent": bool(display["fb60"] & 0x100)}
    tree["allocation"] = {"hinge": hinge_id, "angle_dimension": dim["f50"], "plane": plane_id, "next_header_id": plane_id + 1}
    tree["arc_display_byte_range"] = [display_node.StartOffset, display_node.EndOffset]
    return tree


def refuse_before_allocation(system, settings, allocator, hinge, headers, intent):
    start = (allocator.NextValue, dict(allocator.Allocations), system.ConfigValues[0].FieldsValue["f85c"])
    header_state = headers[0].FieldsValue
    stale = ArchiveNode(headers[0].ClassValue, {**header_state, "f40": header_state["f40"] + 1})
    probes = (
        ("borrowed_camera_name", hinge, headers, replace(intent, annotation_view="*Front")),
        ("reversed_angle", hinge, headers, replace(intent, reverse=True)),
        ("implicit_or_boolean_leader", hinge, headers, replace(intent, selected_leader=True)),
        ("unsupported_shifted_point", hinge, headers, replace(intent, shifted_point_m=(0.0, 0.002, 0.0))),
        ("unregistered_hinge", ArchiveNode(hinge.ClassValue, dict(hinge.FieldsValue)), headers, intent),
        ("stale_hinge_header", hinge, (stale, *headers[1:]), intent),
    )
    refusals = {}
    for role, axis, stamps, guarded in probes:
        try:
            make_angular_plane_mut(system, settings, allocator, axis, stamps, guarded)
        except ValueError as error:
            refusals[role] = str(error)
        require(start == (allocator.NextValue, allocator.Allocations, system.ConfigValues[0].FieldsValue["f85c"]),
                "a rejected angular input consumed a persistent identity or changed the configuration")
    require(len(refusals) == len(probes), "an invalid angular owner or style reached graph construction")
    return refusals


def refuse_changed_owners(roots, model, headers, ends, intent, epoch):
    data = node_fields(roots[-1].FieldsValue["f6f8"], ANGLE_PLANE)
    interface = node_fields(data["f88"], INTERFACE)
    display = node_fields(data["f150"], "moDisplayAngularDim_c")
    dim = node_fields(node_fields(display["f850"][0]["o"], "moFeatureDimHandle_c")["ff0"], "AngleDim_c")
    param = node_fields(dim["f28"], "moAngleParameter_c")
    line = node_fields(interface["f10"].FieldsValue["f08"], "moLineRef_w")
    axis_ref = node_fields(line["f58"], "moCompRefAxis_c")
    actual = axis_ref["ff0"]
    actual_camera = [view["o"].FieldsValue["f360"] for view in model.FieldsValue["f9f8"] if view["o"].FieldsValue["f358"] == "*Back"]
    require(len(actual_camera) == 1, "ordinary part changed the distinct Back camera")
    probes = (
        ("camera_id_in_annotation_slot", display, "f2b0", [{"v": actual_camera[0]}]),
        ("crossed_constraint_owner", interface, "f10", interface["f18"]),
        ("unattached_driver_value", param, "f58", intent.angle_rad * 0.5),
        ("crossed_hinge_creation_event", axis_ref, "ff0", {**actual, "f08": actual["f08"] + 1}),
        ("altered_foreshortened_leader", display, "ff80", intent.selected_leader + 1),
    )
    refusals = {}
    for role, owner, field, value in probes:
        saved = owner[field]
        owner[field] = value
        try:
            check_read_owners(roots, model, headers, ends, intent, epoch)
        except ValueError as error:
            refusals[role] = str(error)
        finally:
            owner[field] = saved
    require(len(refusals) == len(probes), "altered linked parameter, style or reference escaped readback")
    return refusals


def build(request):
    require(type(request) is dict and set(request) == {"document", "path", "epoch", "axis_name", "plane", "views", "active", "shown"},
            "angular plane graph consumes only explicit authored neutral model and presentation")
    intent_fields = request["plane"]
    require(type(intent_fields) is dict and set(intent_fields) == set(AngularPlaneIntent.__dataclass_fields__)
            and isinstance(intent_fields["shifted_point_m"], list), "angular datum requires its own explicit style inputs")
    intent = AngularPlaneIntent(**{**intent_fields, "shifted_point_m": tuple(intent_fields["shifted_point_m"])})
    document = FromData(request["document"])
    plan = ProjectPlain(document)
    require(plan.AxisValue == "z" and not plan.Reversed and min(x for x, _ in plan.VerticesValue) == 0.0
            and min(y for _, y in plan.VerticesValue) == 0.0, "angular datum graph requires a standalone ordinary Front plate")
    epoch = request["epoch"]
    settings = replace(MakePartRecipe(plan, epoch), OutputValue=SelfFileInput(request["path"], epoch))
    CheckPartInput(document, settings, plan, (request["axis_name"], intent.name))
    allocator = PersistentIds()
    system = MakePartBaseMut(settings, plan, allocator)
    profile = MakePartProfMut(system, settings, plan, allocator)
    boss = MakeBlindMut(plan.FeatureName, system.RootValue, profile, SelectBlindEnd(plan, None, None), settings.TargetValue,
                        allocator, settings.DesignIntent, settings.SelectedLeader)
    bounds = ORIGIN, (plan.WidthValue, plan.HeightValue, plan.DepthValue)
    axis, initial = make_hinge_mut(system, settings, allocator, request["axis_name"], bounds)
    add_catalog_mut(system.RootValue, request["views"], request["active"], request["shown"], version=19000)
    rejected = refuse_before_allocation(system, settings, allocator, axis, initial, intent)
    plane, driver, final = make_angular_plane_mut(system, settings, allocator, axis, initial, intent)
    check_fresh_owners(plane, driver, system, allocator)
    raw_headers = tuple(WriteHeadGraph(header, 19000) for header in final[:2])
    headers = tuple(ReadHeaderGraph(raw, 19000) for raw in raw_headers)
    require(tuple(WriteHeadGraph(header, 19000) for header in headers) == raw_headers, "linked header bytes changed in readback")
    raw_cmgr = WriteCmgrMut(system.ManagerValue, 19000)
    cmgr = ReadCmgrMut(raw_cmgr, 19000)
    require(WriteCmgrMut(cmgr.RootValue, 19000) == raw_cmgr and cmgr.RootValue.FieldsValue["f658"] == 0
            and cmgr.RootValue.FieldsValue["f360"].FieldsValue["f85c"] == allocator.NextValue - 1,
            "manager lost the actual final active configuration progress")
    raw_config, config = WriteConfigMut(system.RootValue, 19000, final[0])
    decoded_config = ReadConfigMut(raw_config, 19000, headers[0])
    rewritten_config, config_replay = WriteConfigMut(decoded_config.RootValue, 19000, headers[0])
    require(rewritten_config == raw_config and decoded_config.MapValue == config_replay.MapValue
            and snapshot_signature(decoded_config.MapValue) == snapshot_signature(config.MapValue),
            "root config replay changed its linked field order or owned map")
    link = MakeLinkContext(decoded_config, cmgr)
    roots = (*system.FeatureValues, profile.ProfileValue, boss.FeatureValue, axis, plane)
    raw_resolved, emitted = write_resolved(roots, None, config.MapValue, link)
    decoded, extra, read_map = read_resolved(raw_resolved, decoded_config.MapValue, link)
    replay, written = write_resolved(decoded, extra, decoded_config.MapValue, link)
    require(replay == raw_resolved and read_map == written and extra is None
            and snapshot_signature(emitted) == snapshot_signature(read_map),
            "complete standalone angular prefix changed generated bytes or map ordering")
    preceding, preceding_map = write_roots(roots[:-1], config.MapValue, link)
    count, start = ReadCount(raw_resolved, 4)
    prefix_count, prefix_start = ReadCount(preceding, 4)
    require(count == len(roots) == prefix_count + 1 and preceding[:4] == raw_resolved[:4]
            and raw_resolved[start:].startswith(preceding[prefix_start:]) and preceding_map.CounterValue < emitted.CounterValue,
            "angular attachment changed a prior feature root or its map order")
    axis_data = node_fields(axis.FieldsValue["f700"], "moPlaneInterAxisData_c")
    ends = point(axis_data["f18"]), point(axis_data["f30"])
    observed = check_read_owners(decoded, decoded_config.RootValue, headers, ends, intent, epoch)
    malformed = refuse_changed_owners(decoded, decoded_config.RootValue, headers, ends, intent, epoch)
    streams = {"Config-0": raw_config, "CMgr": raw_cmgr, "Config-0-ModelHeader": raw_headers[0],
               "Header2": raw_headers[1], "Config-0-ResolvedFeatures": raw_resolved}
    result = {"streams": {key: {"bytes": len(value), "sha256": sha256(value).hexdigest()} for key, value in streams.items()},
              "observed": observed, "root_count": len(decoded), "map_counters": [config.MapValue.CounterValue, read_map.CounterValue],
              "preserved_prior_root_count": prefix_count, "prefix_map_counter": preceding_map.CounterValue,
              "standalone_plate_size_m": bounds[1], "fresh_owner_aliases": True, "guarded_runtime_reads": len(audit.DeniedReads),
              "cad_files_written": 0, "bad_inputs": rejected, "bad_readback_owners": malformed}
    return result, raw_resolved


def main():
    for encoding in ("utf-16-le", "utf-8", "latin-1"):
        lookup(encoding)
    envelope = json.load(sys.stdin)
    audit.BeginBuild()
    require(type(envelope) is dict and set(envelope) == {"model", "contrast_leader"},
            "expected a standalone authored model and a separately explicit style contrast")
    request = envelope["model"]
    result, baseline = build(request)
    leader = envelope["contrast_leader"]
    require(type(leader) is int and leader != request["plane"]["selected_leader"],
            "leader contrast requires a different explicit signed input")
    change, after = build({**request, "plane": {**request["plane"], "selected_leader": leader}})
    start, end = result["observed"]["arc_display_byte_range"]
    delta = [index for index, (first, second) in enumerate(zip(baseline, after, strict=True)) if first != second]
    scope = [key for key in result["streams"] if result["streams"][key] != change["streams"][key]]
    require(scope == ["Config-0-ResolvedFeatures"] and len(delta) == 1 and start < delta[0] < end
            and result["map_counters"] == change["map_counters"]
            and change["observed"]["style"]["selected_leader"] == leader
            and result["observed"]["geometry_prediction"] == change["observed"]["geometry_prediction"],
            "independent style contrast changed owners outside the selected leader")
    result["independent_style_contrast"] = {"requested_leader": leader, "changed_streams": scope,
                                           "differing_bytes_in_actual_display": len(delta),
                                           "resolved_sha256": sha256(after).hexdigest()}
    print(json.dumps(result, allow_nan=False, sort_keys=True))


if __name__ == "__main__":
    main()
