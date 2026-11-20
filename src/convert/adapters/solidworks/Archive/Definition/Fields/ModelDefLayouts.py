from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.FontFields import (
    KFontFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.GeometryFields import (
    KGeometryFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.ContainerFields import (
    KContainerFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Definition.Fields.AppearanceFields import (
    KAppearanceFields,
)
from convert.adapters.solidworks.Archive.Definition.Fields.AssemblyDefTail import (
    KAssemblyDefTail,
)
from convert.adapters.solidworks.Archive.Definition.Fields.DocEnvironmentFields import (
    KDocEnvironmentFields,
)
from convert.adapters.solidworks.Archive.Definition.Fields.DocHeadFields import (
    KDocHeadFields,
)
from convert.adapters.solidworks.Archive.Definition.Fields.DocHelperFields import (
    KDocHelperFields,
)
from convert.adapters.solidworks.Archive.Definition.Fields.DocStyleFields import (
    KDocStyleFields,
)
from convert.adapters.solidworks.Archive.Definition.Fields.DocTailFields import (
    KDocTailFields,
)
from convert.adapters.solidworks.Archive.Definition.Fields.DocTransformFields import (
    KDocTransformFields,
)

# ordinary model definitions compose the shared ui fields with their own concrete tails
KModelDefLayouts = MappingProxyType(
    {
        **KContainerFields,
        **KGeometryFields,
        **KFontFields,
        **KAppearanceFields,
        **KDocEnvironmentFields,
        **KDocHelperFields,
        **KDocStyleFields,
        **KDocTransformFields,
        **KAssemblyDefTail,
        "uiPartDoc_c": (
            *KDocHeadFields,
            *KDocTailFields,
            NativeField("Scalar", "f1688", "f64"),
        ),
        "uiAssemblyDoc_c": (
            *KDocHeadFields,
            *KDocTailFields,
            NativeField("Base", "uiAssemblyDoc_c.Serialize.own"),
        ),
    }
)
