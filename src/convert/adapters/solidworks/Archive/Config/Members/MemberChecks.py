from collections.abc import Callable
from types import MappingProxyType

from convert.adapters.solidworks.Archive.Config.Members.CfgMemberTypes import (
    KExplViewClass,
    KRelMgrClass,
    KSketchBlockClass,
    KThreadMgrClass,
)
from convert.adapters.solidworks.Archive.Config.Members.CheckCfgOwner import (
    CheckCfgOwner,
)
from convert.adapters.solidworks.Archive.Config.Members.CheckRelMember import (
    CheckRelMember,
)
from convert.adapters.solidworks.Archive.Config.Members.CheckThreadMap import (
    CheckThreadMap,
)
from convert.adapters.solidworks.Archive.Config.Scene.CheckCfgScene import CheckCfgScene
from convert.adapters.solidworks.Archive.Config.Scene.SceneTypes import KEnvFolderClass
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

# standalone checks need only the resolved root and never inspect external map ownership
KNodeChecks: MappingProxyType[RuntimeClass, Callable[[ArchiveNode], None]] = (
    MappingProxyType(
        {
            KRelMgrClass: CheckRelMember,
            KSketchBlockClass: CheckCfgOwner,
            KExplViewClass: CheckCfgOwner,
            KThreadMgrClass: CheckThreadMap,
        }
    )
)

# checks for child identity need the same archive map used by the caller
KMemberChecks: MappingProxyType[
    RuntimeClass, Callable[[ArchiveNode, ArchiveMaps], None]
] = MappingProxyType({KEnvFolderClass: CheckCfgScene})
