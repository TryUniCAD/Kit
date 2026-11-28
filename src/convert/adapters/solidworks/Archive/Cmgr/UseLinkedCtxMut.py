from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.Layouts.ContainerFields import (
    KContainerFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.ExternalFields import (
    KExternalFields,
)
from convert.adapters.solidworks.Archive.Cmgr.Layouts.LinkedAtomFields import (
    KLinkedAtomFields,
)


# only the saved owner lane requires manager body identities and local file references
def UseLinkedCtxMut(ContextValue: BodyContext) -> None:
    ContextValue.LayoutsValue = {
        **ContextValue.LayoutsValue,
        **KExternalFields,
        "moLinkedAtomIdNode_c": KLinkedAtomFields,
        "su_CDWordArray": KContainerFields["su_CDWordArray"],
    }
    ContextValue.SchemasValue = {
        **ContextValue.SchemasValue,
        "moLinkedAtomIdNode_c": (1,),
        "moExtObject_c": (1,),
        "moCStringHandle_c": (1,),
    }
