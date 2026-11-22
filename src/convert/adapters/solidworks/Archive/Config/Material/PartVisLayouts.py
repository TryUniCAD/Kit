from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.LightFields import (
    KLightFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Visual.MatPropFields import (
    KMatPropFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Visual.MatTextureFields import (
    KMatTextureFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Visual.MatVisualFields import (
    KMatVisualFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Visual.PbrVisFields import (
    KPbrVisFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Visual.RvVisualFields import (
    KRvVisualFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Visual.VisualPropFields import (
    KVisualPropFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.FeatureFields import (
    KFeatureFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Config.Link.CheckPartRoot import KPartRoot
from convert.adapters.solidworks.Archive.Config.Material.MatVisualTypes import (
    KMatVisualClass,
)
from convert.adapters.solidworks.Archive.Config.Scene.SceneTypes import KNodeNameClass

# the model header aliases are already installed when the real lightweight model prefix starts
KPartVisLayouts = MappingProxyType(
    {
        KPartRoot.NameValue: (
            NativeField("Scalar", "fb0", "i32"),
            NativeField("Scalar", "fb4", "u32"),
            NativeField("Base", "moConcept_c.SerializeLWData"),
        ),
        KNodeNameClass.NameValue: KLightFields[KNodeNameClass.NameValue],
        KMatVisualClass.NameValue: KMatVisualFields,
        "moConcept_c.SerializeLWData": KFeatureFields["moConcept_c.SerializeLWData"],
        "moNode_c.SerializeLWData": KFeatureFields["moNode_c.SerializeLWData"],
        "uoMaterialProperties.restore": KMatPropFields,
        "uoMaterialTextureProperties.restore": KMatTextureFields,
        "uoRVAppearanceProperties.restore": KRvVisualFields,
        "moUserProperty_c.restore": KVisualPropFields,
        **KPbrVisFields,
    }
)
