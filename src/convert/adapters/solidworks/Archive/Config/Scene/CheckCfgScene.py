from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Config.Scene.CheckSceneName import (
    CheckSceneName,
)
from convert.adapters.solidworks.Archive.Config.Scene.ReadSceneRows import ReadSceneRows
from convert.adapters.solidworks.Archive.Config.Scene.RequireNewNode import (
    RequireNewNode,
)
from convert.adapters.solidworks.Archive.Config.Scene.SceneTypes import (
    KAmbientClass,
    KDirectionClass,
)
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode

# the two actual part scenes give bounded positional roles for the allowed light graph
KSceneShapes = (
    (KAmbientClass,),
    (KAmbientClass, KDirectionClass, KDirectionClass, KDirectionClass),
)


# post descent validation must detect borrowed or repeated links that bypass body callbacks
def CheckCfgScene(RootValue: ArchiveNode, MapValue: ArchiveMaps) -> None:
    LightValues = tuple(
        RequireNewNode(Value, MapValue) for Value in ReadSceneRows(RootValue)
    )
    ClassShape = tuple(Value.ClassValue for Value in LightValues)
    if ClassShape not in KSceneShapes or len(set(LightValues)) != len(LightValues):
        raise BodyUnsupported("unsupported SOLIDWORKS scene light ownership")
    if any(ReadSceneRows(Value) for Value in LightValues):
        raise BodyUnsupported("SOLIDWORKS light resolved lists require empty owners")
    NameValues = tuple(
        CheckSceneName(Value, MapValue) for Value in (RootValue, *LightValues)
    )
    if len(set(NameValues)) != len(NameValues):
        raise BodyUnsupported("SOLIDWORKS scene name objects must remain distinct")
