from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ResolvedLayouts import (
    KResolvedLayouts,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Drawing.Definition.Emission.Layouts.DetailFields import (
    KDetailFields,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.Layouts.DocHeadFields import (
    KDocHeadFields,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.Layouts.DocHelperFields import (
    KDocHelperFields,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.Layouts.DocTailFields import (
    KDocTailFields,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.Layouts.ManagerFields import (
    KManagerFields,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.Layouts.RootFields import (
    KRootFields,
)
from convert.adapters.solidworks.Drawing.Definition.Writing.SheetFields import (
    KSheetFields,
)

# drawing serialization reuses shared owners while replacing the configuration only header binding
KBlankLayouts = MappingProxyType(
    {
        **KResolvedLayouts,
        **KRootFields,
        **KManagerFields,
        **KDetailFields,
        **KDocHelperFields,
        "moModel_c.FUN_4c17aa00": (
            NativeField("Node", "fa8"),
            *KResolvedLayouts["moModel_c.FUN_4c17aa00"][1:],
        ),
        "uiDrawingDoc_c": (*KDocHeadFields, *KDocTailFields),
        "moDrSheet": (NativeField("Base", "moModelFeature_c"), *KSheetFields),
    }
)
