from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblySysIn import (
    AssemblySysIn,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.System.AsmVocabulary import (
    KAsmEarly,
    KAsmFolders,
    KAsmLate,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.System.MakeAsmCabinet import (
    MakeAsmCabinet,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.System.MakeAsmExploded import (
    MakeAsmExploded,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.System.MakeAsmFolder import (
    MakeAsmFolder,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.System.MakeAsmNode import (
    MakeAsmNode,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.System.MakeAsmOrigin import (
    MakeAsmOrigin,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.System.MakeAsmPlane import (
    MakeAsmPlane,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.MakeLightMut import (
    MakeLightMut,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.MakeNotesMut import (
    MakeNotesMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# native assembly feature publication preserves its separate allocation and resolved order with an actual independent empty mate group
def MakeAsmSysMut(
    OwnerValue: ArchiveNode,
    InputValue: AssemblySysIn,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> tuple[tuple[ArchiveNode, ...], dict[str, ArchiveNode], ArchiveNode]:
    FolderNames = dict(InputValue.FolderNames)
    FolderValues = {
        ClassName: MakeAsmFolder(
            ClassName,
            FolderNames[ClassName],
            OwnerValue,
            TargetValue,
            Allocator,
            InputValue.CreatedAt,
        )
        for ClassName in KAsmFolders
    }
    EnvironmentValue = FolderValues["moEnvFolder_c"]
    OwnerValue.FieldsValue["f1e0"] = EnvironmentValue
    CabinetValue = MakeAsmCabinet(
        InputValue.CabinetName, OwnerValue, TargetValue, Allocator
    )
    PlaneNames = dict(InputValue.PlaneNames)
    PlaneValues = {
        AxisValue: MakeAsmPlane(
            AxisValue, PlaneNames[AxisValue], OwnerValue, TargetValue, Allocator
        )
        for AxisValue in ("z", "y", "x")
    }
    OriginValue = MakeAsmOrigin(
        InputValue.OriginName, OwnerValue, PlaneValues["z"], TargetValue, Allocator
    )
    GroupValue = MakeAsmNode(
        "moMateGroup_c", InputValue.MateGroupName, OwnerValue, TargetValue, Allocator
    )
    GroupValue.FieldsValue.update(
        {"discarded_manager_records": [], "f4e8": [], "f4f8": 0}
    )
    if InputValue.LightValues:
        EnvironmentValue.FieldsValue["f60"] = {
            "list": {
                "n": len(InputValue.LightValues),
                "items": [
                    {
                        "o": MakeLightMut(
                            EnvironmentValue, LightValue, TargetValue, Allocator
                        )
                    }
                    for LightValue in InputValue.LightValues
                ],
            },
            "tail": 0,
        }
    if InputValue.NotesValue is not None:
        NotesValue = MakeNotesMut(
            CabinetValue, InputValue.NotesValue, TargetValue, Allocator
        )
        CabinetValue.FieldsValue["f60"] = {
            "list": {
                "n": 2,
                "items": [{"o": NotesValue.HeadValue}, {"o": NotesValue.EndValue}],
            },
            "tail": 0,
        }
    if InputValue.HasEmptyExplodedView:
        OwnerValue.FieldsValue["f1590"] = MakeAsmExploded(
            OwnerValue, TargetValue, Allocator
        )
    FeatureValues = (
        *(FolderValues[ClassName] for ClassName in KAsmEarly),
        CabinetValue,
        *(FolderValues[ClassName] for ClassName in KAsmLate),
        *PlaneValues.values(),
        OriginValue,
        GroupValue,
    )
    return FeatureValues, PlaneValues, GroupValue
