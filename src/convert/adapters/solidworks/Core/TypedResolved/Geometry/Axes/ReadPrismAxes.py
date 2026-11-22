from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadLogItems import (
    ReadLogItems,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.PrismAxes import (
    PrismAxes,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.PrismAxis import (
    PrismAxis,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.ReadOneAxis import (
    ReadOneAxis,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName


# each additional map vertex must have its unique owner in the three axis subgraphs
def AxisMembers(AxesValue: tuple[PrismAxis, ...]) -> frozenset[ArchiveNode]:
    Members = tuple(
        NodeValue
        for AxisValue in AxesValue
        for NodeValue in (
            AxisValue.NodeValue,
            AxisValue.DataValue,
            AxisValue.NameValue,
            *(
                OwnedNode
                for PickValue in AxisValue.PicksValue
                for OwnedNode in (
                    PickValue.WrapperValue,
                    PickValue.ReferenceValue,
                    PickValue.ComponentValue,
                )
            ),
        )
    )
    Owned = frozenset(Members)
    if len(Owned) != len(Members):
        raise ValueError("cache free origin axes contain shared exclusive owners")
    return Owned


# both physical headers must have one creation event for each actual registered axis
def CheckAxisLogs(
    ConfigHeader: ArchiveNode,
    HeaderValue: ArchiveNode,
    NodesValue: tuple[ArchiveNode, ...],
) -> None:
    IdsValue = tuple(FieldInt(Value.FieldsValue, "f08") for Value in NodesValue)
    for Header in (ConfigHeader, HeaderValue):
        Fields = Header.FieldsValue
        Entries = ReadLogItems(Fields.get("f20"), "moLogs_c")
        if (
            FieldInt(Fields, "f08") <= max(IdsValue)
            or FieldInt(Fields, "f08") != FieldInt(HeaderValue.FieldsValue, "f08")
            or tuple(FieldInt(Value.FieldsValue, "f48") for Value in Entries[1:])
            != IdsValue
            or any(
                len(ReadLogItems(Value, "moStamp_c")) != 1
                or FieldInt(ReadLogItems(Value, "moStamp_c")[0].FieldsValue, "f18")
                != FieldInt(Fields, "f70")
                for Value in Entries[1:]
            )
        ):
            raise ValueError("cache free origin axes lack complete creation ownership")


# the standalone prism has exactly the three positive principal axes after its stock
def ReadPrismAxes(
    LinkValue: NativeLink, HeaderValue: ArchiveNode, Features: Mapping[int, ArchiveNode]
) -> PrismAxes:
    Ordered = tuple(Features.values())
    NodesValue = tuple(
        Value for Value in Ordered if Value.ClassValue.NameValue == "moRefAxis_c"
    )
    Labels = tuple(ReadNativeName(Value) for Value in Ordered)
    if (
        len(NodesValue) != 3
        or NodesValue != Ordered[-3:]
        or len(set(Labels)) != len(Labels)
        or not all(ReadNativeName(Value).strip() for Value in NodesValue)
    ):
        raise ValueError("cache free origin axes have a different named root inventory")
    CheckAxisLogs(LinkValue.ConfigValue.HeaderValue, HeaderValue, NodesValue)
    First, Second, Third = (
        ReadOneAxis(LinkValue, HeaderValue, Features, Value, Direction)
        for Value, Direction in zip(
            NodesValue, ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)), strict=True
        )
    )
    AxesValue = (First, Second, Third)
    return PrismAxes(LinkValue, AxesValue, AxisMembers(AxesValue))
