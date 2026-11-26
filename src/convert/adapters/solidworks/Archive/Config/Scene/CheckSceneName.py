from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Config.Scene.RequireNewNode import (
    RequireNewNode,
)
from convert.adapters.solidworks.Archive.Config.Scene.SceneTypes import KNodeNameClass
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# auxiliary links would need additional presentation owners beyond the observed name node
def CheckSceneName(FeatureValue: ArchiveNode, MapValue: ArchiveMaps) -> ArchiveNode:
    FieldsValue = FeatureValue.FieldsValue
    if (
        FieldsValue["has_list68"] != 0
        or FieldsValue["has_f1e8"] != 0
        or any(
            FieldsValue[NameValue] is not None for NameValue in ("f78", "f258", "f2f0")
        )
    ):
        raise BodyUnsupported("unsupported SOLIDWORKS scene feature links")
    NameNode = RequireNewNode(FieldsValue["f18"], MapValue)
    if NameNode.ClassValue != KNodeNameClass:
        raise BodyUnsupported("SOLIDWORKS scene feature requires its own name node")
    return NameNode
