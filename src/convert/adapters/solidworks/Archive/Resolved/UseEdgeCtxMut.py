from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.Layouts.ExternalFields import (
    KExternalFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Chamfers.ChmfRefFields import (
    KChmfRefFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Chamfers.ChamferFields import (
    KChamferFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Fillets.EdgeFields import (
    KEdgeFields,
)


# ordinary local edge references have shared surface and historical file layouts
def UseEdgeCtxMut(ContextValue: BodyContext) -> None:
    ContextValue.LayoutsValue = {
        **ContextValue.LayoutsValue,
        **KExternalFields,
        **KChmfRefFields,
        **KEdgeFields,
        "rf.suObArray": KChamferFields["rf.suObArray"],
    }
    ContextValue.SchemasValue = {
        **ContextValue.SchemasValue,
        "moCStringHandle_c": (1,),
        "moEndFaceSurfIdRep_c": (1,),
        "moExtObject_c": (1,),
        "moFR_c": (1,),
        "moFromSktEntSurfIdRep_c": (1,),
        "moCompEdge_c": (1,),
        "moEdgeRef_c": (1,),
    }
