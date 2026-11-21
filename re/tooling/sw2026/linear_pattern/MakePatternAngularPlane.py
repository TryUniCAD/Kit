from dataclasses import dataclass
from struct import pack

from Core import Obj
from builders.Extrude import common_display_fields
from builders.Model import reference_wrapper_fields
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import SetCfgStampMut
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import DimensionGraph
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeHandleMut import MakeHandleMut
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeAngleValue import MakeAngleValue
from convert.adapters.solidworks.Archive.Construction.Geometry.FrameXform import FrameXform
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import PlaneFrame
from convert.adapters.solidworks.Archive.Construction.Header.MakeRootLog import MakeRootLog
from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import KAtomLists, KAtomWords
from convert.adapters.solidworks.Archive.Construction.Nodes.InitNodeMut import InitNodeMut
from convert.adapters.solidworks.Archive.Construction.Nodes.MakeModelFeat import MakeModelFeat
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import MakePartHeaders
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import CompRefFields
from convert.adapters.solidworks.Archive.Construction.PlanarMates.SignedStamp import SignedStamp
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import PartSystem
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName, ReadRows

from CheckPatternAngleOwners import matrix, node_fields, point, require, selected_target
from MakePatternAnnotationCatalog import display_membership
from MakePatternHingeAxis import wrapper as plane_wrapper
from MakePatternPrincipalDisplay import point as write_point
from PatternAngleArc import make_angle_arc_fields
from PatternAngleGeometry import canonical_angle_geometry
from PatternAngleWire import ANGLE, ANGLE_PLANE, COINCIDENT, INTERFACE
from PatternHingeGeometry import AXIS, ORIGIN


@dataclass(frozen=True, slots=True)
class AngularPlaneIntent:
    name: str
    angle_rad: float
    reverse: bool
    annotation_view: str
    design_intent: bool
    selected_leader: int
    shifted_point_m: tuple[float, float, float]


def typed_node(name, fields):
    return ArchiveNode(RuntimeClass(name, 1), fields)


def bound_hinge(system, settings, allocator, hinge, headers):
    require(type(system) is PartSystem and type(allocator) is PersistentIds and len(system.ConfigValues) == 1
            and system.ManagerValue.FieldsValue["f360"] is system.ConfigValues[0],
            "angular datum requires the actual ordinary generated part and active configuration")
    fields = node_fields(hinge, "moRefAxis_c")
    identifier = fields["f08"]
    require(fields["owner"] is system.RootValue and allocator.Allocations.get((hinge, "f08")) == identifier,
            "angular datum requires its actual registered hinge from the same model")
    require(len(headers) == 3 and all(header.FieldsValue["f08"] == allocator.NextValue for header in headers[:2])
            and system.ConfigValues[0].FieldsValue["f85c"] == allocator.NextValue - 1,
            "angular datum allocation must extend the hinge's current header and configuration")
    fresh = MakePartHeaders(system, settings, allocator)
    require(tuple(WriteHeadGraph(header, 19000) for header in headers[:2])
            == tuple(WriteHeadGraph(header, 19000) for header in fresh[:2]),
            "angular datum requires the actual fresh hinge headers and their original provenance")
    data = node_fields(fields["f700"], "moPlaneInterAxisData_c")
    supports = tuple(selected_target(node_fields(data[key], "moPlaneRef_w"), "moCompRefPlane_c", "moRefPlane_c",
                                     system.RootValue, system.FeatureValues, headers[:2]) for key in ("f80", "f88"))
    top, right = (system.SystemValues.PlaneValues[key] for key in ("y", "x"))
    require(supports[0][0] is top and supports[1][0] is right and supports[0][1] is not supports[1][1]
            and [ReadNodeName(node) for node in (top, right)] == ["Top Plane", "Right Plane"],
            "angular datum requires ordered registered Top and Right hinge supports")
    top_data = node_fields(top.FieldsValue["f6f8"], "moDefaultRefPlnData_c")
    top_z = point(top_data["display_root"])[2]
    ends = point(data["f18"]), point(data["f30"])
    require(point(data["f50"]) == AXIS and point(data["f68"]) == ORIGIN
            and ends == ((0.0, 0.0, top_z - top_data["b3"]), (0.0, 0.0, top_z - top_data["b2"]))
            and (data["f08"], data["f10"]) == (ends[0][2], -ends[1][2]),
            "angular datum requires the actual directed finite clipping of the hinge")
    return ends, right


def feature_slots(allocator):
    next_id = allocator.NextValue
    available = []
    while len(available) < 3:
        require(next_id < 0x7FFFFFFF, "angular datum cannot allocate its dimension, feature and final header frontier")
        if next_id not in allocator.ReservedSet:
            available.append(next_id)
        next_id += 1
    return tuple(available)


def line_wrapper(system, hinge, headers, ends, creation):
    owner = system.RootValue
    fields = CompRefFields(owner.FieldsValue["f990"])
    fields.update(ff0={"f00": hinge.FieldsValue["f08"], "f08": creation}, ff8=None)
    reference = Obj("moCompRefAxis_c", fields)
    start, finish = ends
    fields = reference_wrapper_fields(reference=reference)
    fields.update(
        f68=1, f08=SignedStamp(headers[0].FieldsValue["f40"]), f0c=system.ConfigValues[0].FieldsValue["f08"],
        fb0=0.0, fb8=start[2] - finish[2], fc8=write_point(start), fe0=write_point(AXIS), ff8=0,
    )
    return typed_node("moLineRef_w", fields)


def make_angle_driver(plane, intent, geometry, arc, membership):
    parameter = typed_node("moAngleParameter_c", {})
    InitNodeMut(parameter, "D1")
    parameter.FieldsValue.update(owner=plane, f0c=0, f48=None, f58=intent.angle_rad, f68=0)
    dimension = MakeAngleValue(plane, parameter)
    first, second, centre = geometry["witness_points_m"]
    local_transform = FrameXform(PlaneFrame(centre, *geometry["dimension_basis"]))
    dimension.FieldsValue.update(f80=write_point(first), fa0=write_point(second), fc0=write_point(centre),
                                 has_ff0=1, ff0=local_transform)
    handle = MakeHandleMut(plane, dimension)
    fields = common_display_fields(handle=handle, angular=True, design_intent=intent.design_intent,
                                   selected_leader=intent.selected_leader)
    fields.update(arc)
    fields.update(owner=plane, f2b0=membership["f2b0"], ff68=write_point(intent.shifted_point_m),
                  f5b0={**fields["f5b0"], "data": pack("<d", intent.angle_rad)})
    display = typed_node("moDisplayAngularDim_c", fields)
    return DimensionGraph(parameter, dimension, handle, display)


def constraint_rows(right, line, angle):
    def pick():
        return {"u": 0.5, "v": 0.5, "f20": write_point(ORIGIN)}

    return typed_node(INTERFACE, {
        "f08": typed_node(ANGLE, {"f08": right, **pick(), "f38": angle, "f40": 0}),
        "f10": typed_node(COINCIDENT, {"f08": line, **pick()}),
        "f18": typed_node(COINCIDENT, {"f08": None, **pick()}),
    })


def make_angular_plane_mut(system, settings, allocator, hinge, headers, intent):
    require(type(intent) is AngularPlaneIntent and type(intent.name) is str and intent.name and "\x00" not in intent.name
            and intent.name not in {ReadNodeName(node) for node in (*system.FeatureValues, hinge)},
            "angular datum requires its own authored feature name and intent")
    require(type(intent.design_intent) is bool and type(intent.selected_leader) is int
            and -(1 << 31) <= intent.selected_leader < (1 << 31)
            and type(intent.shifted_point_m) is tuple and all(type(value) is float for value in intent.shifted_point_m)
            and intent.shifted_point_m == ORIGIN, "ordinary angular datum needs an explicit signed leader and zero shifted point")
    require(settings.TargetValue.FileVersion == 19000, "angular datum requires an ordinary 2026 archive")
    ends, right = bound_hinge(system, settings, allocator, hinge, headers)
    geometry = canonical_angle_geometry(*ends, intent.angle_rad, reverse=intent.reverse)
    arc = make_angle_arc_fields(*ends, intent.angle_rad, reverse=intent.reverse)
    membership = display_membership(system.RootValue, intent.annotation_view)
    views = node_fields(system.RootValue.FieldsValue["fa48"], "suObList")
    selected = [node_fields(row["o"], "moAnnotationView_c") for row in ReadRows(views["items"])]
    view_id = membership["f2b0"][0]["v"]
    require(intent.annotation_view == "*Back"
            and [matrix(view["f368"]) for view in selected if view["f360"] == view_id] == [geometry["dimension_basis"]],
            "angular datum requires the actual named Back annotation and its angular dimension frame")
    dimension_id, plane_id, frontier = feature_slots(allocator)
    creation = settings.HeaderValue.CreatedAt
    line = line_wrapper(system, hinge, headers, ends, creation)
    base = plane_wrapper(system, right, "x", headers)
    plane = MakeModelFeat("moRefPlane_c", intent.name, system.RootValue, settings.TargetValue)
    fields = plane.FieldsValue
    fields.update(dict.fromkeys(KAtomWords, 0))
    fields.update({key: [] for key in KAtomLists})
    fields.update(f368={"n": 0, "items": []}, f388={"n": 0, "items": []},
                  f538=None, f4a0=1, f6c0=write_point(geometry["name_corner_m"]),
                  f6dc=4, f6e0=0, f6e8=None, f6f0=0)
    basis = geometry["basis_u_v_n"]
    frame = FrameXform(PlaneFrame(geometry["root_m"], *basis))
    data = {
        "owner": plane, "root": write_point(geometry["root_m"]), "normal": write_point(basis[2]), "f20": frame,
        **{f"b{index}": value for index, value in enumerate(geometry["ordered_borders_m"])},
        "f48": None, "f50": 0, "f54": -4, "f58": -4, "old_e5": 0,
        "f5c": 22, "f60": 0, "f64": 0, "f68": None, "f70": None, "f78": None,
        "f88": constraint_rows(base, line, intent.angle_rad), "f148": int(3 * point(line.FieldsValue["fe0"])[2]),
    }
    fields["f6f8"] = typed_node(ANGLE_PLANE, data)
    graph = make_angle_driver(plane, intent, geometry, arc, membership)
    data["f150"] = graph.DisplayValue
    require(allocator.AllocateMut(graph.DimensionValue, "f50") == dimension_id and allocator.AllocateMut(plane) == plane_id
            and allocator.NextValue == frontier, "actual angular dimension and plane allocations departed from their order")
    SetCfgStampMut(system.ConfigValues[0], allocator)
    final = MakePartHeaders(system, settings, allocator)
    for header in final[:2]:
        logs = node_fields(header.FieldsValue["f20"], "suObList")
        logs["items"] += tuple(MakeRootLog(node, settings.HeaderValue) for node in (hinge, plane))
    return plane, graph, final
