from collections.abc import Mapping
from math import pi as CircleRatio

from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismParam import (
    ReadPrismParam,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Patterns.ReadTiltFrame import (
    ReadTiltFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.ReadTiltHinge import (
    ReadTiltHinge,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.ReadTiltRef import (
    ReadTiltRef,
)
from convert.adapters.solidworks.Core.TypedResolved.Patterns.TiltOwner import TiltOwner
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the angular direction derives from its real hinge constraint and separately owned live parameter
def ReadPatTilt(
    LinkValue: NativeLink,
    HeaderValue: ArchiveNode,
    Features: Mapping[int, ArchiveNode],
    DatumValue: ArchiveNode,
    HingeValue: ArchiveNode,
) -> tuple[PlaneFrame, tuple[float, float, float], TiltOwner]:
    DataValue = RequireNative(
        DatumValue.FieldsValue.get("f6f8"),
        "moConstraintCoincLineAtAnglePlaneRefplaneData_c",
    )
    Fields = DataValue.FieldsValue
    Interface = RequireNative(Fields.get("f88"), "moConstraintRefplaneInterfaceData_c")
    Shape = Interface.FieldsValue
    AngleGeom = RequireNative(Shape.get("f08"), "moRefPlaneAngleGeom_c")
    HingeGeom = RequireNative(Shape.get("f10"), "moRefPlaneCoincidentGeom_c")
    FreeGeom = RequireNative(Shape.get("f18"), "moRefPlaneCoincidentGeom_c")
    Display = RequireNative(Fields.get("f150"), "moDisplayAngularDim_c")
    Dimension, Parameter, AngleValue = ReadPrismParam(Display, True)
    CheckTreeAlias(
        LinkValue,
        (
            DataValue,
            Interface,
            AngleGeom,
            HingeGeom,
            FreeGeom,
            Display,
            Dimension,
            Parameter,
        ),
    )
    DimensionId = Dimension.FieldsValue.get("f50")
    if (
        HingeGeom is FreeGeom
        or FreeGeom.FieldsValue.get("f08") is not None
        or (Fields.get("f5c"), Fields.get("f148")) != (22, -3)
        or AngleGeom.FieldsValue.get("f40") != 0
        or AngleGeom.FieldsValue.get("f38") != AngleValue
        or not 0.0 < AngleValue < CircleRatio / 2
        or ReadNativeName(Parameter) != "D1"
        or type(DimensionId) is not int
        or not 0 <= DimensionId < NativeNodeId(DatumValue)
    ):
        raise ValueError("angular datum requires its local unreversed live driver")
    TopValue, RightValue, HingeRefs, StartValue, EndValue = ReadTiltHinge(
        LinkValue, HeaderValue, Features, HingeValue
    )
    BaseValue, BaseRef = ReadTiltRef(
        LinkValue, HeaderValue, Features, AngleGeom.FieldsValue.get("f08")
    )
    AxisValue, AxisRef = ReadTiltRef(
        LinkValue, HeaderValue, Features, HingeGeom.FieldsValue.get("f08"), True
    )
    if (
        BaseValue is not RightValue
        or AxisValue is not HingeValue
        or len({*HingeRefs, BaseRef, AxisRef}) != 4
    ):
        raise ValueError("angular plane and hinge do not own their distinct selections")
    FrameValue, CenterValue = ReadTiltFrame(Fields, AngleValue, StartValue, EndValue)
    return (
        FrameValue,
        CenterValue,
        TiltOwner(HingeValue, TopValue, RightValue, Dimension, Parameter, AngleValue),
    )
