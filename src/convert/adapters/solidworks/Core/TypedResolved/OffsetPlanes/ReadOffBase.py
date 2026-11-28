from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.MakeOffsetRef import (
    MakeOffsetRef,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.OffBaseFrame import (
    OffBaseFrame,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadDatumFrame import (
    ReadDatumFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRef import (
    CheckPrismRef,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# local reference selection must name the actual persistent plane in the actual model
def ReadOffLink(
    Reference: ArchiveNode, RootValue: ArchiveNode, DatumId: int, ModeValue: int
) -> None:
    CheckPrismRef(Reference)
    Fields = Reference.FieldsValue
    Component = RequireNative(Fields.get("f58"), "moUnitComponent_c")
    if (
        Component.FieldsValue != {"has_ext": 0, "owner": RootValue}
        or Fields.get("ff0") != {"f00": DatumId, "f08": 2592000}
        or Fields.get("ff8") is not None
        or Fields.get("f100") != ModeValue
    ):
        raise ValueError("offset plane has a mismatched local selection owner")


# the selected principal datum must explain the wrapper transform and local anchor
def ReadOffBase(
    Wrapper: Mapping[str, object],
    RootValue: ArchiveNode,
    Features: Mapping[int, ArchiveNode],
) -> tuple[ArchiveNode, PlaneFrame]:
    Reference = RequireNative(Wrapper.get("f58"), "moCompRefPlane_c")
    DatumId = NativeRecord(Reference.FieldsValue.get("ff0")).get("f00")
    if type(DatumId) is not int:
        raise ValueError("offset plane lacks its real principal selection")
    Datum = RequireNative(Features[DatumId], "moRefPlane_c")
    ActualFrame, AxisValue = ReadDatumFrame(Datum)
    FrameValue = OffBaseFrame("xyz"[AxisValue - 1])
    ReadOffLink(Reference, RootValue, NativeNodeId(Datum), AxisValue)
    if ActualFrame != FrameValue or Wrapper != MakeOffsetRef(
        Reference, Datum, FrameValue
    ):
        raise ValueError("offset plane has a contradictory base carrier")
    return Datum, FrameValue
