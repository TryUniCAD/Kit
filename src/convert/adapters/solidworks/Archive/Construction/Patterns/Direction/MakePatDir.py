from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    DatumPoint,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Direction.CheckPatRef import (
    CheckPatRef,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Direction.CheckPatTime import (
    CheckPatTime,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Direction.ReadPatDir import (
    ReadPatDir,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import (
    CompRefFields,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.WrapperFields import (
    WrapperFields,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the selected plane owns a fresh local component reference and a separately derived resolved line
def MakePatDir(
    SystemValue: PartSystem,
    Settings: PartBuildInput,
    Allocator: PersistentIds,
    PlaneValue: ArchiveNode,
    Headers: tuple[ArchiveNode, ArchiveNode],
) -> ArchiveNode:
    LineValue = ReadPatDir(PlaneValue)
    UnitValue, ConfigId, PlaneId = CheckPatRef(SystemValue, Allocator, PlaneValue)
    Epoch, Access = CheckPatTime(
        Headers, PlaneValue, PlaneId, ConfigId, Settings.HeaderValue.CreatedAt
    )
    RefFields = CompRefFields(UnitValue)
    RefFields.update(ff0={"f00": PlaneId, "f08": Epoch}, ff8=None, f100=0)
    Reference = ArchiveNode(RuntimeClass("moCompRefPlane_c", 1), RefFields)
    Fields = WrapperFields(Reference)
    Fields.update(
        f08=Access,
        f0c=ConfigId,
        f68=1,
        fb0=0.0,
        fb8=LineValue.SpanValue,
        fc8=DatumPoint(LineValue.PointValue),
        fe0=DatumPoint(LineValue.DirectionValue),
        ff8=0,
    )
    return ArchiveNode(RuntimeClass("moLineRef_w", 1), Fields)
