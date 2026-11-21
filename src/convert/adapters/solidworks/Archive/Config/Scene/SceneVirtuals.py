from types import MappingProxyType

from convert.adapters.solidworks.Archive.Config.Scene.SceneTypes import (
    KAmbientClass,
    KDirectionClass,
    KEnvFolderClass,
)

# all three concrete scene owners use the same guarded inherited feature targets
KSceneVirtuals: MappingProxyType[tuple[str, int], str | int | bool | None] = (
    MappingProxyType(
        {
            (ClassValue.NameValue, SlotValue): TargetValue
            for ClassValue in (KEnvFolderClass, KAmbientClass, KDirectionClass)
            for SlotValue, TargetValue in (
                (1000, "moFeature_c.SerializeXmlData"),
                (1016, True),
                (1208, "moConcept_c.SerializeLWData"),
                (1216, "moConcept_c.SerializeResolvedData"),
            )
        }
    )
)
