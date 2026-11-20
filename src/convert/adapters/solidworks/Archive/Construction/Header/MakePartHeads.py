from pathlib import PureWindowsPath

from convert.adapters.solidworks.Archive.Construction.Files.MakeSelfFile import (
    MakeSelfFile,
)
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Header.HeaderInput import (
    HeaderInput,
)
from convert.adapters.solidworks.Archive.Construction.Header.MakePartHeader import (
    MakePartHeader,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeMgrHeader import (
    MakeMgrHeader,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Format import KPartSuffix


# both standalone roles must share the same self record while the manager projects the actual part
def MakePartHeads(
    RootValue: ArchiveNode,
    ManagerValue: ArchiveNode,
    InputValue: HeaderInput,
    OutputValue: SelfFileInput,
    Allocator: PersistentIds,
) -> tuple[ArchiveNode, ArchiveNode, ArchiveNode]:
    RequireRootNode(ManagerValue, "moConfigurationMgr_c")
    if ManagerValue.FieldsValue.get("owner") is not RootValue:
        raise ValueError("SOLIDWORKS manager header requires the same actual part")
    if type(OutputValue) is not SelfFileInput:
        raise TypeError("SOLIDWORKS part headers require an explicit self file input")
    if PureWindowsPath(OutputValue.PathName).suffix.casefold() != KPartSuffix:
        raise ValueError("native self path must identify a part")
    ManagerHeader = MakeMgrHeader(ManagerValue, OutputValue.SavedAt)
    ConfigValue = ArchiveNode.RequireNode(ManagerValue.FieldsValue["f360"])
    ModelHeader = MakePartHeader(RootValue, InputValue, Allocator, True)
    TopHeader = MakePartHeader(RootValue, InputValue, Allocator, False)
    SelfValue = MakeSelfFile(RootValue, ModelHeader, ConfigValue, OutputValue)
    ModelHeader.FieldsValue["f38"] = SelfValue
    TopHeader.FieldsValue["f38"] = SelfValue
    return ModelHeader, TopHeader, ManagerHeader
