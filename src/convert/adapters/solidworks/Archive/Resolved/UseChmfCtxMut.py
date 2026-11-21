from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Chamfers.ChamferFields import (
    KChamferFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Fillets.EdgeFields import (
    KEdgeFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Fillets.KeeperFields import (
    KKeeperFields,
)


# the measured ordinary chamfer context shares edge and keeper layouts with retained edge fillets
def UseChmfCtxMut(ContextValue: BodyContext) -> None:
    if ContextValue.VersionValue != 19000 or ContextValue.FlagsValue != {
        "model_compressed_stream": 1,
        "model_is_part": 1,
        "cmgr_f658": 1,
    }:
        raise BodyUnsupported("unsupported ordinary SOLIDWORKS chamfer archive context")
    ContextValue.LayoutsValue = {
        **ContextValue.LayoutsValue,
        **KEdgeFields,
        **KKeeperFields,
        **KChamferFields,
    }
    ContextValue.SchemasValue = {
        **ContextValue.SchemasValue,
        "Chamfer_c": (1,),
        "moCompEdge_c": (1,),
        "moEdgeRef_c": (1,),
        "moFilletSurfIdRep_c": (1,),
        "moSurfaceIdRep_c": (1,),
    }
    ContextValue.VirtualValue = {
        **ContextValue.VirtualValue,
        ("Chamfer_c", 1000): "moFeature_c.SerializeXmlData",
        ("Chamfer_c", 1016): True,
        ("Chamfer_c", 1208): "moConcept_c.SerializeLWData",
        ("Chamfer_c", 1216): "moConcept_c.SerializeResolvedData",
    }
