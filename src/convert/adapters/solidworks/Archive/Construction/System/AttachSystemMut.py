from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.System.MakeCabinet import (
    MakeCabinet,
)
from convert.adapters.solidworks.Archive.Construction.System.MakePrincipal import (
    MakePrincipal,
)
from convert.adapters.solidworks.Archive.Construction.System.MakeSysFolder import (
    MakeSysFolder,
)
from convert.adapters.solidworks.Archive.Construction.System.SystemClasses import (
    KFolderCaches,
)
from convert.adapters.solidworks.Archive.Construction.System.SystemInput import (
    SystemInput,
)
from convert.adapters.solidworks.Archive.Construction.System.SystemNodes import (
    SystemNodes,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# fresh part attachment binds its actual environment and equation owners while keeping the resolved feature sequence independently serialized
def AttachSystemMut(
    OwnerValue: ArchiveNode,
    InputValue: SystemInput,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> SystemNodes:
    RequireRootNode(OwnerValue, "moPart_c")
    if (
        type(InputValue) is not SystemInput
        or OwnerValue.FieldsValue.get("f1e0") is not None
    ):
        raise ValueError(
            "system attachment requires explicit inputs and a fresh unattached model"
        )
    RelationValue = ArchiveNode.RequireNode(OwnerValue.FieldsValue["f9d0"])
    RequireRootNode(RelationValue, "moRelMgr_c")
    FoldersValue = {
        ClassName: MakeSysFolder(
            ClassName,
            NameValue,
            OwnerValue,
            TargetValue,
            Allocator,
            InputValue.CreatedAt,
        )
        for ClassName, NameValue in InputValue.FolderValues
    }
    CabinetValue = MakeCabinet(
        InputValue.CabinetName, OwnerValue, TargetValue, Allocator
    )
    NamesValue = dict(InputValue.PlaneNames)
    PlanesValue = {
        AxisValue: MakePrincipal(
            AxisValue,
            NamesValue[AxisValue],
            OwnerValue,
            TargetValue,
            Allocator,
            InputValue.PlaneFlags,
        )
        for AxisValue in ("z", "y", "x")
    }
    CachesValue = {
        FieldName: FoldersValue[ClassName]
        for FieldName, ClassName in KFolderCaches.items()
    }
    OwnerValue.FieldsValue["f1e0"] = CachesValue["f1e0"]
    FoldersValue["moEqnFolder_c"].FieldsValue["_relation_manager"] = RelationValue
    RelationValue.FieldsValue["_equation_folder"] = FoldersValue["moEqnFolder_c"]
    FeatureValues = (*FoldersValue.values(), CabinetValue, *PlanesValue.values())
    return SystemNodes(
        FoldersValue, CabinetValue, PlanesValue, FeatureValues, CachesValue
    )
