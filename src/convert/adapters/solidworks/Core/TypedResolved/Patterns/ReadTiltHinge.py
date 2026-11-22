from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadDatumFrame import (
    ReadDatumFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.ReadPlane import ReadVector
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Patterns.ReadTiltRef import (
    ReadTiltRef,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# finite hinges preserve the ordered principal plane pair and its actual clipped interval
def ReadTiltHinge(
    LinkValue: NativeLink,
    HeaderValue: ArchiveNode,
    Features: Mapping[int, ArchiveNode],
    HingeValue: ArchiveNode,
) -> tuple[
    ArchiveNode,
    ArchiveNode,
    tuple[ArchiveNode, ArchiveNode],
    tuple[float, float, float],
    tuple[float, float, float],
]:
    AxisValue = RequireNative(
        HingeValue.FieldsValue.get("f700"), "moPlaneInterAxisData_c"
    )
    CheckTreeAlias(LinkValue, (HingeValue, AxisValue))
    Fields = AxisValue.FieldsValue
    TopValue, TopRef = ReadTiltRef(LinkValue, HeaderValue, Features, Fields.get("f80"))
    RightValue, RightRef = ReadTiltRef(
        LinkValue, HeaderValue, Features, Fields.get("f88")
    )
    StartValue = ReadVector(Fields.get("f18"))
    EndValue = ReadVector(Fields.get("f30"))
    if (
        ReadDatumFrame(TopValue)[1] != 2
        or ReadDatumFrame(RightValue)[1] != 1
        or TopRef is RightRef
        or ReadVector(Fields.get("f50")) != (0.0, 0.0, -1.0)
        or ReadVector(Fields.get("f68")) != (0.0, 0.0, 0.0)
        or StartValue[:2] != (0.0, 0.0)
        or EndValue[:2] != (0.0, 0.0)
        or not StartValue[2] > 0.0 > EndValue[2]
        or (Fields.get("f08"), Fields.get("f10")) != (StartValue[2], -EndValue[2])
    ):
        raise ValueError("angular datum requires the local top and right intersection")
    return TopValue, RightValue, (TopRef, RightRef), StartValue, EndValue
