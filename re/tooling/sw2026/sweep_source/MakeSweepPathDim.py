from math import hypot
from struct import pack

from convert.adapters.solidworks.Archive.Construction.Circles.MakeArcHandle import MakeArcHandle
from convert.adapters.solidworks.Archive.Construction.Circles.MakeRadialTail import MakeRadialTail
from convert.adapters.solidworks.Archive.Construction.Circles.RadialText import RadialText
from convert.adapters.solidworks.Archive.Construction.Circles.ReadRadialStyle import ReadRadialStyle
from convert.adapters.solidworks.Archive.Construction.Dimensions.DimensionGraph import DimensionGraph
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeCommonView import MakeCommonView
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeLengthParam import MakeLengthParam
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeLocalRef import MakeLocalRef
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import MakePoint
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.DimBaseFields import DimBaseFields
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from SweepModel import require


def node(name, fields):
    return ArchiveNode(RuntimeClass(name, 1), fields)


def make_value(profile, sketch, arc, points):
    center, start, end = points
    position = center.FieldsValue["pos"]
    radius = position["y"]
    require(center is not start and start is not end and center is not end
            and arc.FieldsValue["_sketch"] is sketch
            and arc.FieldsValue["_center"] is center
            and arc.FieldsValue["_start"] is start
            and arc.FieldsValue["_end"] is end
            and position["x"] == 0.0 and start.FieldsValue["pos"] == {"x": 0.0, "y": 0.0}
            and end.FieldsValue["pos"] == {"x": radius, "y": radius},
            "radial driver requires the actual signed quarter-arc incidence")
    parameter = MakeLengthParam(profile, radius)
    value = node("sgCircleDim", {
        **DimBaseFields(), "owner": profile, "_sketch": sketch, "f28": parameter,
        "f80": 3, "f90": 2, "f94": 0, "f98": 0, "fa0": 0, "g1": 0, "g2": 0,
        "dir": MakePoint(XValue=1.0), "h1": MakeArcHandle(sketch, arc, 0),
        "h2": node("sgEntHandle", {"_sketch": None, "idx": 0x777F, "f18": -2, "f1c": -1, "f08": 0}),
    })
    return parameter, value


def make_reference(profile, sketch, value):
    return node("moSkDimHandleRadial_c", {
        **MakeLocalRef(profile.FieldsValue["f2b0"]), "owner": profile, "_values": (value,),
        "has_f120": 0, "has_f128": 0, "f130": None, "f138": None, "f140": None,
        "f148": None, "f150": 0, "fe8": None, "f100": None, "f154": -1,
        "f118": 0, "ff0": sketch, "ff8": 0,
    })


def make_view(profile, frame, handle, radius, design_intent, leader):
    text = 0.015, 0.004
    first, second = text[0], text[1] - radius
    distance = hypot(first, second)
    center = MakePoint(YValue=radius)
    fields = MakeCommonView(handle, design_intent, leader, 20)
    style, solid = ReadRadialStyle(profile.FieldsValue["owner"], False)
    fields.update(style.ProjectionValue)
    fields.update(MakeRadialTail(False, solid))
    fields.update({
        "owner": profile, "f950": radius, "f7f8": "R", "f958": center, "f988": center,
        "fad0": radius, "f880": MakePoint(XValue=first / distance, YValue=second / distance),
        "f8a8": distance / radius, "f8b0": distance - radius,
        "f3e0": fields["f3e0"] & ~0x200, "f8a4": (fields["f8a4"] & ~0x8050) | style.UnderText,
        "fb64": (fields["fb64"] & ~0x103000) | style.FlagValue | 0x800,
        "fb60": fields["fb60"] | 0x200,
    })
    fields["f6a0"]["f38"] = RadialText(frame, text)
    fields["f5b0"]["data"] = pack("<d", radius)
    return node("moDisplayRadialDim_c", fields)


def make_path_dimension(profile, frame, sketch, arc, points, settings, allocator):
    parameter, value = make_value(profile, sketch, arc, points)
    handle = make_reference(profile, sketch, value)
    display = make_view(profile, frame, handle, parameter.FieldsValue["f58"],
                        settings.DesignIntent, settings.SelectedLeader)
    allocator.AllocateMut(value, "f50")
    return DimensionGraph(parameter, value, handle, display)
