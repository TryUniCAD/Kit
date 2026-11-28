from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector


# both saved section transports must own the same vertex free periodic boundary
def CheckSectFins(
    NodesValue: Mapping[int, XmtNode], EdgeValue: XmtNode, FaceValue: XmtNode
) -> tuple[XmtNode, ...]:
    LoopValue = RequireXmt(NodesValue, FaceValue.Integer("loop"), 15)
    FirstUse = RequireXmt(NodesValue, LoopValue.Integer("halfedge"), 17)
    OtherUse = RequireXmt(NodesValue, FirstUse.Integer("other"), 17)
    if (
        LoopValue.Integer("face") != FaceValue.IndexValue
        or LoopValue.Integer("next")
        or FirstUse.Integer("loop") != LoopValue.IndexValue
        or FirstUse.Integer("forward") != FirstUse.IndexValue
        or FirstUse.Integer("backward") != FirstUse.IndexValue
        or OtherUse.Integer("loop")
        or OtherUse.Integer("other") != FirstUse.IndexValue
        or EdgeValue.Integer("halfedge") != FirstUse.IndexValue
        or (FirstUse.String("sense"), OtherUse.String("sense")) != ("+", "-")
        or any(
            UseValue.Integer("edge") != EdgeValue.IndexValue
            or UseValue.Integer("vertex")
            or UseValue.Integer("curve")
            for UseValue in (FirstUse, OtherUse)
        )
    ):
        raise ValueError("SOLIDWORKS saved sweep section has foreign trim owners")
    return LoopValue, FirstUse, OtherUse


# planar sheet owners are followed by their actual links before either carrier contributes geometry
def ReadSwSect(
    NodesValue: Mapping[int, XmtNode],
    BodyValue: XmtNode,
    *,
    Embedded: bool = False,
    SavedResult: bool = True,
) -> CircleGeometry:
    RegionValue = RequireXmt(NodesValue, BodyValue.Integer("region"), 19)
    ShellValue = RequireXmt(NodesValue, BodyValue.Integer("shell"), 13)
    FaceValue = RequireXmt(NodesValue, ShellValue.Integer("face"), 14)
    PlaneValue = RequireXmt(NodesValue, BodyValue.Integer("boundary_surface"), 50)
    EdgeValue = RequireXmt(NodesValue, BodyValue.Integer("edge"), 16)
    CurveValue = RequireXmt(NodesValue, EdgeValue.Integer("curve"), 31)
    FinValues = CheckSectFins(NodesValue, EdgeValue, FaceValue)
    if Embedded and (
        BodyValue.IndexValue != 1
        or BodyValue.Integer("owner")
        or BodyValue.Integer("next") != (2 if SavedResult else 0)
        or set(NodesValue)
        != {
            Value.IndexValue
            for Value in (
                BodyValue,
                RegionValue,
                ShellValue,
                FaceValue,
                PlaneValue,
                EdgeValue,
                CurveValue,
                *FinValues,
            )
        }
        or BodyValue.Integer("next") in NodesValue
    ):
        raise ValueError("SOLIDWORKS saved sweep has an alternate embedded sheet")
    CheckSectOwners(
        BodyValue, RegionValue, ShellValue, FaceValue, PlaneValue, EdgeValue, CurveValue
    )
    FrameValue = PrincipalFrame("x")
    for Value, OriginName in ((PlaneValue, "pvec"), (CurveValue, "centre")):
        if (
            Value.FieldsValue[OriginName] != FrameValue.OriginValue
            or Value.FieldsValue["normal"] != FrameValue.NormalValue
            or Value.FieldsValue["x_axis"] != FrameValue.AxisU
            or Value.String("sense") != "+"
        ):
            raise ValueError(
                "SOLIDWORKS saved sweep section carrier has a foreign frame"
            )
    return CircleGeometry(
        PlaneVector(0.0, 0.0), RequireScalar(CurveValue.FieldsValue["radius"])
    )


# one section must use its own body region shell face and boundary carriers throughout
def CheckSectOwners(
    BodyValue: XmtNode,
    RegionValue: XmtNode,
    ShellValue: XmtNode,
    FaceValue: XmtNode,
    PlaneValue: XmtNode,
    EdgeValue: XmtNode,
    CurveValue: XmtNode,
) -> None:
    if (
        BodyValue.Integer("body_type") != 3
        or BodyValue.Integer("vertex")
        or BodyValue.Integer("boundary_point")
        or BodyValue.Integer("boundary_curve") != CurveValue.IndexValue
        or RegionValue.String("type") != "V"
        or RegionValue.Integer("body") != BodyValue.IndexValue
        or RegionValue.Integer("shell") != ShellValue.IndexValue
        or ShellValue.Integer("body") != BodyValue.IndexValue
        or ShellValue.Integer("region") != RegionValue.IndexValue
        or ShellValue.Integer("front_face") != FaceValue.IndexValue
        or FaceValue.Integer("shell") != ShellValue.IndexValue
        or FaceValue.Integer("front_shell") != ShellValue.IndexValue
        or FaceValue.Integer("surface") != PlaneValue.IndexValue
        or PlaneValue.Integer("owner") != FaceValue.IndexValue
        or EdgeValue.Integer("owner") != BodyValue.IndexValue
        or CurveValue.Integer("owner") != EdgeValue.IndexValue
        or any(
            Value.Integer("next") or Value.Integer("previous")
            for Value in (RegionValue, EdgeValue, PlaneValue, CurveValue)
        )
    ):
        raise ValueError(
            "SOLIDWORKS saved sweep section lacks its owned closed boundary"
        )
