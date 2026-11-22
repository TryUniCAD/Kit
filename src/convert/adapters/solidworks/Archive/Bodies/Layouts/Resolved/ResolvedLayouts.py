from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Part.PartLayouts import (
    KPartLayouts,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.BodyFields import (
    KBodyFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ComponentFields import (
    KComponentFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.CoreFields import (
    KCoreFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.DimensionFields import (
    KDimensionFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.FeatureFields import (
    KFeatureFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.FolderFields import (
    KFolderFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.GeometryFields import (
    KGeometryFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.MaterialFields import (
    KMaterialFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ProfileFields import (
    KProfileFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.RevolveFields import (
    KRevolveFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.SketchFields import (
    KSketchFields,
)

# resolved field owners share the same typed serialization kernel and existing configuration definitions
KResolvedLayouts = MappingProxyType(
    {
        "mgMatrix_c.restore": KPartLayouts["mgMatrix_c.restore"],
        "mgVector_c.restore": KPartLayouts["mgVector_c.restore"],
        "mgXform_c.restore": KPartLayouts["mgXform_c.restore"],
        "moComponent_c": KPartLayouts["moComponent_c"],
        "moConcept_c.SerializeLWData": KPartLayouts["moConcept_c.SerializeLWData"],
        "moConcept_c.SerializeResolvedData": KPartLayouts[
            "moConcept_c.SerializeResolvedData"
        ],
        "moEntVisProp_c": KPartLayouts["moEntVisProp_c"],
        "moFeature_c": KPartLayouts["moFeature_c"],
        "moFeature_c.FUN_4bb2b240": KPartLayouts["moFeature_c.FUN_4bb2b240"],
        "moFeature_c.SerializeXmlData": KPartLayouts["moFeature_c.SerializeXmlData"],
        "moFolder_c": KPartLayouts["moFolder_c"],
        "moModelFeature_c": KPartLayouts["moModelFeature_c"],
        "moNodeList_c.Serialize": KPartLayouts["moNodeList_c.Serialize"],
        "moNodeName_c": KPartLayouts["moNodeName_c"],
        "moNode_c.SerializeLWData": KPartLayouts["moNode_c.SerializeLWData"],
        "moNode_c.SerializeNode": KPartLayouts["moNode_c.SerializeNode"],
        "moUnitComponent_c": KPartLayouts["moUnitComponent_c"],
        "moVisProp_c": KPartLayouts["moVisProp_c"],
        "rf.suObList": KPartLayouts["rf.suObList"],
        "suObList": KPartLayouts["suObList"],
        "su_CStringArray": KPartLayouts["su_CStringArray"],
        "utLineWidth_c.Serialize0": KPartLayouts["utLineWidth_c.Serialize0"],
        "utLineWidth_c.Serialize2": KPartLayouts["utLineWidth_c.Serialize2"],
        **KBodyFields,
        **KComponentFields,
        **KCoreFields,
        **KDimensionFields,
        **KFeatureFields,
        **KFolderFields,
        **KGeometryFields,
        **KMaterialFields,
        **KProfileFields,
        **KRevolveFields,
        **KSketchFields,
    }
)
