from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.Layouts.ContainerFields import (
    KContainerFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.FileRefFields import (
    KFileRefFields,
)
from convert.adapters.solidworks.Archive.Cmgr.Layouts.LinkedAtomFields import (
    KLinkedAtomFields,
)
from convert.adapters.solidworks.Archive.Config.Material.BindMatReadMut import (
    BindMatReadMut,
)


# a saved assignment needs its actual manager linked atom and referenced file layout
def BindMatMgrMut(ContextValue: BodyContext) -> None:
    BindMatReadMut(ContextValue)
    ContextValue.LayoutsValue = {
        **ContextValue.LayoutsValue,
        **KFileRefFields,
        "moLinkedAtomIdNode_c": KLinkedAtomFields,
        "su_CDWordArray": KContainerFields["su_CDWordArray"],
    }
    ContextValue.SchemasValue = {
        **ContextValue.SchemasValue,
        "moLinkedAtomIdNode_c": (1,),
        "moExtObject_c": (1,),
        "moCStringHandle_c": (1,),
    }
