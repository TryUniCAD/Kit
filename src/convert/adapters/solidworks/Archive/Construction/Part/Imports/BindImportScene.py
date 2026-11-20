from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import (
    LightInput,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.MakeLightMut import (
    MakeLightMut,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)


# authored illumination belongs to the actual empty environment without adding a default scene
def BindImportScene(
    SystemValue: PartSystem,
    LightValues: tuple[LightInput, ...],
    TargetValue: FeatureTarget,
    Allocator: PersistentIds,
) -> None:
    FolderValue = SystemValue.SystemValues.FolderValues["moEnvFolder_c"]
    FieldsValue = FolderValue.FieldsValue
    if (
        SystemValue.RootValue.FieldsValue.get("f1e0") is not FolderValue
        or FieldsValue.get("owner") is not SystemValue.RootValue
        or FieldsValue.get("f60") != {"list": {"n": 0, "items": []}, "tail": 0}
    ):
        raise ValueError("authored lights require the actual empty environment")
    FieldsValue["f60"] = {
        "list": {
            "n": len(LightValues),
            "items": [
                {"o": MakeLightMut(FolderValue, LightValue, TargetValue, Allocator)}
                for LightValue in LightValues
            ],
        },
        "tail": 0,
    }
