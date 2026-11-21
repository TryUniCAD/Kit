from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyFaces import (
    ReadBodyFaces,
)


# an ordinary concentric selection must resolve one actual cylinder on one complete three face solid
def PickCylFace(NodesValue: Mapping[int, XmtNode]) -> tuple[XmtNode, XmtNode, XmtNode]:
    FacesValue = tuple(Value for Value in NodesValue.values() if Value.KindValue == 14)
    Matches = tuple(
        Value
        for Value in FacesValue
        if NodesValue[Value.Integer("surface")].KindValue == 51
    )
    BodiesValue = tuple(Value for Value in NodesValue.values() if Value.KindValue == 12)
    if len(Matches) != 1 or len(BodiesValue) != 1 or len(FacesValue) != 3:
        raise ValueError(
            "concentric child is outside the ordinary single cylinder body profile"
        )
    FaceValue, BodyValue = Matches[0], BodiesValue[0]
    SurfaceValue = RequireXmt(NodesValue, FaceValue.Integer("surface"), 51)
    FaceIndexes = ReadBodyFaces(NodesValue, BodyValue, 3)
    if (
        FaceValue.IndexValue not in FaceIndexes
        or SurfaceValue.Integer("owner") != FaceValue.IndexValue
        or any(
            NodesValue[Value.Integer("surface")].KindValue != 50
            for Value in FacesValue
            if Value is not FaceValue
        )
    ):
        raise ValueError("concentric cylinder or caps have foreign body ownership")
    return FaceValue, SurfaceValue, BodyValue
