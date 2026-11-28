from math import cos, dist, hypot, isfinite, pi, sin, tan
from struct import pack

from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    DatumDot, DatumOffset, DatumPoint, DatumUnit,
)
from convert.adapters.solidworks.Archive.Construction.Datums.Angles.MakeAngleArc import KArcTolerance
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import DimensionGraph
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeCommonView import MakeCommonView
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeDistTail import MakeDistTail
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeHandleMut import MakeHandleMut
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeLengthParam import MakeLengthParam
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeValueFields import MakeValueFields
from convert.adapters.solidworks.Archive.Construction.Dimensions.ReadModelLinear import ReadModelLinear
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeAngleValue import MakeAngleValue
from convert.adapters.solidworks.Archive.Construction.Geometry.CrossVector import CrossVector
from convert.adapters.solidworks.Archive.Construction.Geometry.FrameXform import FrameXform
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import PlaneFrame
from convert.adapters.solidworks.Archive.Construction.Geometry.ReadRigidXform import ReadRigidXform
from convert.adapters.solidworks.Archive.Construction.Nodes.InitNodeMut import InitNodeMut
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.MakeAnnoView import ReadAnnoBasis
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.ReadAnnoView import ReadAnnoView
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

from BuildChamferBoundary import component, require, safe_pair


def edge_frame(shape, view):
    require(type(shape) is dict and set(shape) == {
        "body_id", "stock_bounds_m", "edge_axis", "corner", "distance_axis", "distance_m", "angle_rad",
    } and type(shape["body_id"]) is str and bool(shape["body_id"]),
            "chamfer drivers require explicit rectangular stock and one selected edge")
    require(type(shape["stock_bounds_m"]) is list and len(shape["stock_bounds_m"]) == 3,
            "chamfer drivers require three stock axes")
    bounds = tuple(safe_pair(interval) for interval in shape["stock_bounds_m"])
    axis, primary = shape["edge_axis"], shape["distance_axis"]
    require(type(axis) is int and type(primary) is int and 0 <= axis < 3 and 0 <= primary < 3
            and axis != primary, "chamfer distance must select one transverse stock side")
    secondary = next(index for index in range(3) if index not in (axis, primary))
    bits = shape["corner"]
    require(type(bits) is dict and set(bits) == {str(primary), str(secondary)}
            and all(type(value) is int and value in (0, 1) for value in bits.values()),
            "chamfer drivers require the actual two stock extremes of the selected edge")
    depth, angle = component(shape["distance_m"]), component(shape["angle_rad"])
    require(0 < angle < pi / 2 and 1e-14 <= depth < bounds[primary][1] - bounds[primary][0]
            and 0 < depth * tan(angle) < bounds[secondary][1] - bounds[secondary][0],
            "live chamfer values must leave a positive acute bevel inside both stock faces")
    mid = tuple(a / 2 + b / 2 if index == axis else bounds[index][bits[str(index)]]
                for index, (a, b) in enumerate(bounds))
    u, v = (tuple(float(2 * bits[str(side)] - 1) if index == side else 0.0 for index in range(3))
            for side in (primary, secondary))
    anchor = DatumOffset(mid, u, -depth)
    require(anchor != mid and all(isfinite(value) for value in anchor)
            and abs(dist(anchor, mid) - depth) <= 1e-12,
            "chamfer display origin must retain the finite distance from the selected edge")
    matrix, translation = ReadRigidXform(view.FieldsValue["f368"])
    basis = ReadAnnoBasis(tuple((matrix[index], matrix[index + 3], matrix[index + 6]) for index in range(3)))
    horizontal = DatumDot(u, basis[0])
    require(translation == (0.0, 0.0, 0.0) and abs(horizontal) == 1
            and horizontal == DatumDot(v, basis[1]) and abs(basis[2][axis]) == 1,
            "chamfer drivers require the proved signed annotation orientation")
    return PlaneFrame(anchor, *basis), mid, u, v, horizontal


def label_geometry(presentation, horizontal):
    require(type(presentation) is dict and set(presentation) == {
        "view", "distance_text", "angle_text_xy_m", "witness_length_m", "design_intent", "selected_leaders",
    }, "chamfer display requires explicit neutral label and witness intent")
    for key in ("distance_text", "angle_text_xy_m", "selected_leaders"):
        require(type(presentation[key]) in (list, tuple) and len(presentation[key]) == 2,
                "chamfer requires two explicit label coordinates and two leader roles")
    station, clearance = map(component, presentation["distance_text"])
    require(station > 1 and clearance * horizontal > 0,
            "chamfer distance requires text beyond the second witness on its proved side")
    radius = component(presentation["witness_length_m"])
    require(radius > 0, "chamfer angle requires a positive explicit witness length")
    label = (*map(component, presentation["angle_text_xy_m"]), 0.0)
    return station, clearance, radius, label


def make_view(feature, model, handle, presentation, membership, driver, is_angle):
    fields = MakeCommonView(handle, presentation["design_intent"],
                            presentation["selected_leaders"][int(is_angle)], 13 if is_angle else 18)
    style = ReadModelLinear(model)
    fields.update(style.ProjectionValue)
    fields.update(owner=feature, f2b0=({"v": membership},), n2b0=1,
                  f8a4=(fields["f8a4"] & ~0x50) | style.UnderText,
                  fb64=(fields["fb64"] & ~0x103000) | style.FlagValue,
                  f5b0={**fields["f5b0"], "data": pack("<d", driver)})
    return fields


def make_drivers_mut(model, feature, shape, presentation, allocator):
    require(feature.ClassValue == RuntimeClass("Chamfer_c", 1)
            and feature.FieldsValue.get("owner") is model
            and feature.FieldsValue.get("f08") == -1
            and not {"f810", "f818"} & feature.FieldsValue.keys(),
            "chamfer driver attachment requires one fresh owned schema-one feature")
    require(type(presentation) is dict and "view" in presentation and type(presentation["view"]) is str,
            "chamfer driver attachment requires one authored annotation view name")
    view = ReadAnnoView(model, presentation["view"])
    require(view.ClassValue == RuntimeClass("moAnnotationView_c", 1),
            "chamfer display requires the ordinary annotation view schema")
    frame, mid, u, v, horizontal = edge_frame(shape, view)
    station, clearance, radius, label = label_geometry(presentation, horizontal)
    depth, angle = float(shape["distance_m"]), float(shape["angle_rad"])
    anchor = frame.OriginValue

    distance_param = MakeLengthParam(feature, depth)
    distance_dim = ArchiveNode(RuntimeClass("ParallelPlaneDistanceDim_c", 1), MakeValueFields(feature, distance_param))
    distance_dim.FieldsValue.update(f80=DatumPoint(anchor), fa0=DatumPoint(mid),
                                    has_fe0=1, fe0=DatumPoint(u), fe8=DatumPoint(v),
                                    has_ff0=1, ff0=FrameXform(frame))
    distance_handle = MakeHandleMut(feature, distance_dim)
    distance_view = make_view(feature, model, distance_handle, presentation, view.FieldsValue["f360"], depth, False)
    distance_view.update(MakeDistTail())
    distance_view.update(f880=DatumPoint((0.0, horizontal, 0.0)), f8a8=station, f8b0=abs(clearance),
                         f988=DatumPoint((depth * horizontal, 0.0, 0.0)),
                         f9a0=DatumPoint((depth * horizontal, 0.0, 0.0)),
                         fa38=DatumPoint((horizontal, 0.0, 0.0)), fad0=depth)

    angle_param = ArchiveNode(RuntimeClass("moAngleParameter_c", 1), {})
    InitNodeMut(angle_param, "D2")
    angle_param.FieldsValue.update(owner=feature, f0c=0, f48=None, f58=angle, f68=0)
    angle_dim = MakeAngleValue(feature, angle_param)
    bevel_ray = DatumOffset(DatumOffset((0.0, 0.0, 0.0), u, -cos(angle)), v, sin(angle))
    first, second = DatumOffset(anchor, bevel_ray, radius), DatumOffset(anchor, u, -radius)
    require(first != anchor and second != anchor and first != second
            and all(isfinite(value) for value in (*first, *second))
            and all(abs(dist(anchor, point) - radius) <= 1e-12 for point in (first, second)),
            "chamfer witnesses must retain distinct finite world endpoints")
    angle_dim.FieldsValue.update(f80=DatumPoint(first), fa0=DatumPoint(second),
                                 fc0=DatumPoint(anchor), has_ff0=1, ff0=FrameXform(frame))
    angle_handle = MakeHandleMut(feature, angle_dim)
    angle_view = make_view(feature, model, angle_handle, presentation, view.FieldsValue["f360"], angle, True)
    local_first = (horizontal * radius * -cos(angle), horizontal * radius * sin(angle), 0.0)
    local_second = (-horizontal * radius, 0.0, 0.0)
    first_in = (horizontal * cos(angle), -horizontal * sin(angle), 0.0)
    second_in = (horizontal, 0.0, 0.0)
    direction = DatumUnit(label)
    crossing = CrossVector(first_in, second_in)
    require(crossing[2] > KArcTolerance
            and DatumDot(CrossVector(first_in, direction), crossing) < -KArcTolerance,
            "chamfer angle requires a label strictly exterior to the first witness")
    chord = 2 * radius * sin(angle / 2)
    require(isfinite(chord) and chord > 0 and isfinite(hypot(*label)),
            "chamfer display requires finite witness and label lengths")
    angle_view.update(f880=DatumPoint(direction), f8a8=-0.5, f8b0=hypot(*label), fad0=chord,
                      f958=DatumPoint(local_first), f988=DatumPoint(local_second),
                      f100c=0, f1010=1, f1008=1, ffb8=DatumPoint(first_in), ffd0=DatumPoint(second_in),
                      ffe8=-radius, fff0=0.0, fff8=-radius, f1000=0.0, f1018=0x18)

    distance_display = ArchiveNode(RuntimeClass("moDisplayDistanceDim_c", 1), distance_view)
    angle_display = ArchiveNode(RuntimeClass("moDisplayAngularDim_c", 1), angle_view)
    next_id = allocator.NextValue
    for _ in range(3):
        while next_id in allocator.ReservedSet:
            next_id += 1
        require(next_id < 0x7fffffff, "chamfer and both live drivers exceed persistent id capacity")
        next_id += 1
    allocator.AllocateMut(distance_dim, "f50")
    allocator.AllocateMut(angle_dim, "f50")
    feature.FieldsValue.update(f810=distance_display, f818=angle_display)
    return (DimensionGraph(distance_param, distance_dim, distance_handle, distance_display),
            DimensionGraph(angle_param, angle_dim, angle_handle, angle_display))
