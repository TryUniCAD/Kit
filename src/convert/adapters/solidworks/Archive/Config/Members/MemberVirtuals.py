from types import MappingProxyType

from convert.adapters.solidworks.Archive.Config.Scene.SceneVirtuals import (
    KSceneVirtuals,
)

# the sketch and exploded owners differ only in their concrete feature xml dispatch
KMemberVirtuals: MappingProxyType[tuple[str, int], str | int | bool | None] = (
    MappingProxyType(
        {
            ("moSketchBlockMgr_c", 1000): None,
            ("moPrtExplViewManager_c", 1000): "moFeature_c.SerializeXmlData",
            ("moSketchBlockMgr_c", 1016): True,
            ("moPrtExplViewManager_c", 1016): True,
            ("moSketchBlockMgr_c", 1208): "moConcept_c.SerializeLWData",
            ("moPrtExplViewManager_c", 1208): "moConcept_c.SerializeLWData",
            ("moSketchBlockMgr_c", 1216): "moConcept_c.SerializeResolvedData",
            ("moPrtExplViewManager_c", 1216): "moConcept_c.SerializeResolvedData",
            **KSceneVirtuals,
        }
    )
)
