from math import copysign as CopySign

from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.PlacePoint import (
    PlacePoint,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.FrameXform import (
    FrameXform,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# canonical zero preserves the initializer wire representation across signed principal axes
def ScaleWallAxis(
    BasisValue: tuple[float, float, float], SenseValue: float
) -> tuple[float, float, float]:
    First, Second, Third = (
        Value * SenseValue if Value else 0.0 for Value in BasisValue
    )
    return First, Second, Third


# display endpoints and inverse frame are model space owners of the sketch local thickness span
def SetWallFrameMut(
    DimensionValue: ArchiveNode,
    SupportValue: PlaneFrame,
    SpanValue: tuple[float, float, float],
) -> None:
    StartValue, EndValue, AxialValue = SpanValue
    SenseValue = CopySign(1.0, EndValue - StartValue)
    First = PlacePoint(SupportValue, (StartValue, AxialValue, 0.0))
    Second = PlacePoint(SupportValue, (EndValue, AxialValue, 0.0))
    Radial = ScaleWallAxis(SupportValue.AxisU, SenseValue)
    Normal = ScaleWallAxis(SupportValue.NormalValue, SenseValue)
    Axial = ScaleWallAxis(SupportValue.AxisV, -1.0)
    FrameValue = PlaneFrame(First, Radial, Normal, Axial)
    DimensionValue.FieldsValue.update(
        f80=MakePoint(XValue=First[0], YValue=First[1], ZValue=First[2]),
        fa0=MakePoint(XValue=Second[0], YValue=Second[1], ZValue=Second[2]),
        has_fe0=1,
        fe0=MakePoint(XValue=Radial[0], YValue=Radial[1], ZValue=Radial[2]),
        fe8=MakePoint(XValue=Normal[0], YValue=Normal[1], ZValue=Normal[2]),
        has_ff0=1,
        ff0=FrameXform(FrameValue),
    )
