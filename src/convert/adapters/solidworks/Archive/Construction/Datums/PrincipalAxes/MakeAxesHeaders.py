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
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadLogItems import (
    ReadLogItems,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
)


# both freshly generated headers must account for each actual registered axis event
def MakeAxesHeaders(
    SystemValue: PartSystem,
    InputValue: PartBuildInput,
    Allocator: PersistentIds,
    AxisNodes: tuple[ArchiveNode, ...],
) -> tuple[ArchiveNode, ArchiveNode, ArchiveNode]:
    if any(
        Feature.FieldsValue.get("owner") is not SystemValue.RootValue
        or Allocator.Allocations.get((Feature, "f08"))
        != FieldInt(Feature.FieldsValue, "f08")
        for Feature in AxisNodes
    ):
        raise ValueError("axis creation events require actual allocated feature owners")
    SetCfgStampMut(SystemValue.ConfigValues[0], Allocator)
    Headers = MakePartHeaders(SystemValue, InputValue, Allocator)
    for Header in Headers[:2]:
        LogValue = RequireNode(Header.FieldsValue.get("f20"), "suObList")
        Entries = ReadLogItems(LogValue, "moLogs_c")
        if len(Entries) != 1 or FieldInt(Entries[0].FieldsValue, "f48") != FieldInt(
            SystemValue.RootValue.FieldsValue, "f08"
        ):
            raise ValueError(
                "principal axis headers require their actual root creation event"
            )
        LogValue.FieldsValue["items"] = (
            *Entries,
            *(
                MakeRootLog(NodeValue, InputValue.HeaderValue)
                for NodeValue in AxisNodes
            ),
        )
    return Headers
