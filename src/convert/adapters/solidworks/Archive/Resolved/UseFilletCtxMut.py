from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Fillets.EdgeFields import (
    KEdgeFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Fillets.FilletFields import (
    KFilletFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Fillets.KeeperFields import (
    KKeeperFields,
)

# only the measured archive class descriptors are available to the explicit read lane
KFilletSchemas = {
    "Fillet_c": (1,),
    "edgeRadiusObject_c": (1,),
    "moCompEdge_c": (1,),
    "moCompFace_c": (1,),
    "moEdgeRef_c": (1,),
    "moFilletSurfIdRep_c": (1,),
    "moSurfaceIdRep_c": (1,),
}


# explicit read admission keeps legacy readers and all store entry points independent
def UseFilletCtxMut(ContextValue: BodyContext) -> None:
    if ContextValue.VersionValue != 19000 or ContextValue.FlagsValue != {
        "model_compressed_stream": 1,
        "model_is_part": 1,
        "cmgr_f658": 1,
    }:
        raise BodyUnsupported("unsupported ordinary SOLIDWORKS fillet archive context")
    ContextValue.LayoutsValue = {
        **ContextValue.LayoutsValue,
        **KEdgeFields,
        **KFilletFields,
        **KKeeperFields,
    }
    ContextValue.SchemasValue = {**ContextValue.SchemasValue, **KFilletSchemas}
    ContextValue.VirtualValue = {
        **ContextValue.VirtualValue,
        ("Fillet_c", 1000): "moFeature_c.SerializeXmlData",
        ("Fillet_c", 1016): True,
        ("Fillet_c", 1208): "moConcept_c.SerializeLWData",
        ("Fillet_c", 1216): "moConcept_c.SerializeResolvedData",
    }
