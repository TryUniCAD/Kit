from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Circles.ReadLocalCirc import (
    ReadLocalCirc,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# an unrelated curved profile must not gain presentation admission from a matching feature class alone
def CheckThruCircle(
    ProfileValue: ArchiveNode, LoopValue: LineLoop, LinkValue: NativeLink
) -> None:
    SketchValue = RequireNative(ProfileValue.FieldsValue.get("pd_f80"), "sgSketch")
    ShapeValue = ReadLocalCirc(SketchValue, LinkValue, AllowFree=True)
    if ShapeValue is None or ShapeValue[1] is not None:
        raise ValueError(
            "through-all presentation needs its actual undimensioned circle"
        )
    CircleValue = ShapeValue[0]
    CenterX, CenterY = CircleValue.CenterValue
    RadiusValue = CircleValue.RadiusValue
    XValues = tuple(Value.PositionValue[0] for Value in LoopValue.PointsValue.values())
    YValues = tuple(Value.PositionValue[1] for Value in LoopValue.PointsValue.values())
    if not (
        min(XValues) < CenterX - RadiusValue < CenterX + RadiusValue < max(XValues)
        and min(YValues) < CenterY - RadiusValue < CenterY + RadiusValue < max(YValues)
    ):
        raise ValueError("through-all presentation circle is not enclosed by its stock")
