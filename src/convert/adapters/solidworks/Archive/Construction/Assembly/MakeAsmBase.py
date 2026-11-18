from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Config.MakeAsmManager import (
    MakeAsmManager,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Model.MakeAsmRoot import (
    MakeAsmRoot,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.System.MakeAsmSysMut import (
    MakeAsmSysMut,
)
from convert.adapters.solidworks.Archive.Construction.Configuration.ConfigSpec import (
    ConfigSpec,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Presentation.MakePartRefs import (
    MakePartRefs,
)
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the assembly model manager and system graph must share one actual root and allocator while analysis units remain absent on this native profile
def MakeAsmBase(InputValue: AssemblyInput) -> AssemblyState:
    Allocator = PersistentIds()
    RefsValue = MakePartRefs(
        InputValue.StyleValue,
        InputValue.DocumentUnits,
        UnitInput("m", "radian", "mks", 4),
    )
    RootValue = MakeAsmRoot(InputValue.NameValue, RefsValue, Allocator)
    ConfigValue = ConfigSpec(
        InputValue.ConfigName, "", InputValue.HeaderValue.ModifiedAt
    )
    ManagerValue = MakeAsmManager(
        InputValue.ManagerName, ConfigValue, RootValue, InputValue.TargetValue
    )
    FeatureValues, PlaneValues, GroupValue = MakeAsmSysMut(
        RootValue, InputValue.SystemValue, InputValue.TargetValue, Allocator
    )
    CurrentConfig = ArchiveNode.RequireNode(ManagerValue.FieldsValue["f360"])
    CurrentConfig.FieldsValue["f85c"] = Allocator.NextValue - 1
    return AssemblyState(
        RootValue,
        ManagerValue,
        CurrentConfig,
        FeatureValues,
        PlaneValues,
        GroupValue,
        Allocator,
    )
