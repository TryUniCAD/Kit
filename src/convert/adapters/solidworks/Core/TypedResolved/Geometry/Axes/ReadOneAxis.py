from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.ReadPlane import ReadVector
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.AxisPick import (
    AxisPick,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.PrismAxis import (
    PrismAxis,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.ReadAxisPick import (
    ReadAxisPick,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismAtom import (
    CheckPrismAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# ordinary axis roots cannot contribute bodies dependencies or extra presentation owners
def CheckAxisState(NodeValue: ArchiveNode) -> None:
    CheckPrismAtom(NodeValue)
    Fields = NodeValue.FieldsValue
    if (
        Fields.get("f0c") not in (0, 1)
        or Fields.get("f28") != 0x40000000
        or Fields.get("f2c") != 0
        or Fields.get("f2b0") != 19000
        or Fields.get("hidden") != 0
        or Fields.get("has_list68") != 0
        or Fields.get("f78") is not None
        or Fields.get("f6dc") != 4
        or Fields.get("f6e0") != 0
        or Fields.get("f6e8") is not None
        or Fields.get("f6f0") != 0
        or any(
            not IsLineState(Fields.get(FieldName))
            for FieldName in ("f60", "f368", "f388")
        )
    ):
        raise ValueError("cache free origin axis has unsupported feature state")


# the signed intersection is derived from the actual ordered parent normals
def AxisDirection(First: AxisPick, Second: AxisPick) -> tuple[float, float, float]:
    FirstX, FirstY, FirstZ = First.FrameValue.NormalValue
    OtherX, OtherY, OtherZ = Second.FrameValue.NormalValue
    return (
        FirstY * OtherZ - FirstZ * OtherY,
        FirstZ * OtherX - FirstX * OtherZ,
        FirstX * OtherY - FirstY * OtherX,
    )


# the stored distances must describe the same directed segment as the endpoint owners
def ReadAxisEnds(
    DataValue: ArchiveNode, Direction: tuple[float, float, float]
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    Fields = DataValue.FieldsValue
    AxisIndex = Direction.index(1.0)
    Start = ReadVector(Fields.get("f18"))
    EndValue = ReadVector(Fields.get("f30"))
    if (
        ReadVector(Fields.get("f50")) != Direction
        or ReadVector(Fields.get("f68")) != (0.0, 0.0, 0.0)
        or not Start[AxisIndex] < 0.0 < EndValue[AxisIndex]
        or Fields.get("f08") != -Start[AxisIndex]
        or Fields.get("f10") != EndValue[AxisIndex]
        or any(
            PointValue[OtherIndex] != 0.0
            for PointValue in (Start, EndValue)
            for OtherIndex in range(3)
            if OtherIndex != AxisIndex
        )
    ):
        raise ValueError("cache free origin axis has contradictory signed endpoints")
    return Start, EndValue


# the root data name and physical support selections stay joined to the same linked read
def ReadOneAxis(
    LinkValue: NativeLink,
    HeaderValue: ArchiveNode,
    Features: Mapping[int, ArchiveNode],
    NodeValue: ArchiveNode,
    Direction: tuple[float, float, float],
) -> PrismAxis:
    CheckAxisState(NodeValue)
    Fields = NodeValue.FieldsValue
    DataValue = RequireNative(Fields.get("f700"), "moPlaneInterAxisData_c")
    NameValue = RequireNative(Fields.get("f18"), "moNodeName_c")
    CheckTreeAlias(LinkValue, (NodeValue, DataValue, NameValue))
    First = ReadAxisPick(LinkValue, HeaderValue, Features, DataValue.FieldsValue["f80"])
    Second = ReadAxisPick(
        LinkValue, HeaderValue, Features, DataValue.FieldsValue["f88"]
    )
    if AxisDirection(First, Second) != Direction:
        raise ValueError("cache free origin axis has crossed or nonprincipal supports")
    Start, EndValue = ReadAxisEnds(DataValue, Direction)
    if ReadVector(Fields.get("f6c0")) != Start:
        raise ValueError("cache free origin axis has a different label anchor")
    return PrismAxis(NodeValue, DataValue, NameValue, (First, Second), Start, EndValue)
