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
from convert.adapters.solidworks.Archive.Bodies.Layouts.ObListFields import (
    KObListFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
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

# the ordinary part definition shares counted archive fields and owns its density tail
KModelDefLayouts = MappingProxyType(
    {
        **KContainerFields,
        **KGeometryFields,
        **KFontFields,
        **KDocEnvironmentFields,
        **KDocHelperFields,
        **KDocStyleFields,
        **KDocTransformFields,
        "suObList": KObListFields,
        "uiPartDoc_c": (
            *KDocHeadFields,
            *KDocTailFields,
            NativeField("Scalar", "f1688", "f64"),
        ),
    }
)
