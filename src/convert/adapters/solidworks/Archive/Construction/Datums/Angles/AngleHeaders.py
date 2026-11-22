from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import (
    SetCfgStampMut,
)
from convert.adapters.solidworks.Archive.Construction.Header.MakeRootLog import (
    MakeRootLog,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import (
    MakePartHeaders,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import RequireNode


# the frontier accounts for the next dimension the plane and the next actual available native id
def AngleSlots(Allocator: PersistentIds) -> tuple[int, int, int]:
    Candidate = Allocator.NextValue
    Available: list[int] = []
    while len(Available) < 3:
        if Candidate >= 0x7FFFFFFF:
            raise ValueError("angular datum cannot allocate its dimension and feature")
        if Candidate not in Allocator.ReservedSet:
            Available.append(Candidate)
        Candidate += 1
    return Available[0], Available[1], Available[2]


# both complete part headers retain the actual registered hinge and plane creation events
def AngleHeaders(
    SystemValue: PartSystem,
    Settings: PartBuildInput,
    Allocator: PersistentIds,
    HingeValue: ArchiveNode,
    PlaneValue: ArchiveNode,
) -> tuple[ArchiveNode, ArchiveNode, ArchiveNode]:
    SetCfgStampMut(SystemValue.ConfigValues[0], Allocator)
    Headers = MakePartHeaders(SystemValue, Settings, Allocator)
    for Header in Headers[:2]:
        LogFields = RequireNode(Header.FieldsValue.get("f20"), "suObList").FieldsValue
        RowsValue = LogFields.get("items")
        if not isinstance(RowsValue, tuple):
            raise ValueError("angular datum needs an ordered creation log")
        LogFields["items"] = (
            *CastValue(tuple[ArchiveNode, ...], RowsValue),
            MakeRootLog(HingeValue, Settings.HeaderValue),
            MakeRootLog(PlaneValue, Settings.HeaderValue),
        )
    return Headers
