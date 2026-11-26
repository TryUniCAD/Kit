from typing import cast as CastValue
from convert.adapters.solidworks.Archive.Construction.Configuration.MakeConfigMgr import (
    MakeConfigMgr,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.ManagerInput import (
    ManagerInput,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import (
    SetCfgStampMut,
)
from convert.adapters.solidworks.Archive.Construction.Model.MakePartRootMut import (
    MakePartRootMut,
)
from convert.adapters.solidworks.Archive.Construction.Model.PartRootInput import (
    PartRootInput,
)
from convert.adapters.solidworks.Archive.Construction.Model.PartRootRefs import (
    PartRootRefs,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Origin.MakeOriginMut import (
    MakeOriginMut,
)
from convert.adapters.solidworks.Archive.Construction.System.AttachSystemMut import (
    AttachSystemMut,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Construction.System.SystemInput import (
    SystemInput,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# fresh configuration and system construction must share one allocator and actual model while keeping local configuration ids independent
def MakePartSysMut(
    InputValue: PartRootInput,
    RefsValue: PartRootRefs,
    ManagerValue: ManagerInput,
    SystemValue: SystemInput,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> PartSystem:
    if (
        type(ManagerValue) is not ManagerInput
        or type(SystemValue) is not SystemInput
        or type(TargetValue) is not FeatureTarget
    ):
        raise TypeError(
            "part system composition requires typed manager system and target inputs"
        )
    RootValue = MakePartRootMut(InputValue, RefsValue, Allocator)
    ManagerNode = MakeConfigMgr(ManagerValue, RootValue, TargetValue)
    SystemNodes = AttachSystemMut(RootValue, SystemValue, TargetValue, Allocator)
    OriginValue = MakeOriginMut(
        SystemValue.OriginName,
        RootValue,
        SystemNodes.PlaneValues[SystemValue.OriginAxis],
        SystemValue.OriginAxis,
        TargetValue,
        Allocator,
    )
    ListFields = CastValue(dict[str, object], ManagerNode.FieldsValue["f370"])
    RowsValue = CastValue(list[dict[str, object]], ListFields["items"])
    ConfigValues = tuple(
        ArchiveNode.RequireNode(RowValue["o"]) for RowValue in RowsValue
    )
    SetCfgStampMut(ConfigValues[ManagerValue.CurrentIndex], Allocator)
    return PartSystem(
        RootValue,
        ManagerNode,
        ConfigValues,
        SystemNodes,
        OriginValue,
        (*SystemNodes.FeatureValues, OriginValue.ProfileValue),
    )
