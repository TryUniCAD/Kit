from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Fillets.EdgeFields import (
    KEdgeFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Shells.ShellFields import (
    KShellFields,
)


# native saved shells reuse the part context and its typed face references
def UseShellCtxMut(ContextValue: BodyContext) -> None:
    if ContextValue.VersionValue != 19000 or ContextValue.FlagsValue != {
        "model_compressed_stream": 1,
        "model_is_part": 1,
        "cmgr_f658": 1,
    }:
        raise BodyUnsupported("unsupported ordinary SOLIDWORKS shell archive context")
    ContextValue.LayoutsValue = {
        **ContextValue.LayoutsValue,
        **KEdgeFields,
        **KShellFields,
    }
    ContextValue.SchemasValue = {
        **ContextValue.SchemasValue,
        "moCompFace_c": (1,),
        "moCompEdge_c": (1,),
        "moEdgeRef_c": (1,),
        "moShell_c": (1,),
    }
    ContextValue.VirtualValue = {
        **ContextValue.VirtualValue,
        ("moShell_c", 1000): "moFeature_c.SerializeXmlData",
        ("moShell_c", 1016): True,
        ("moShell_c", 1208): "moConcept_c.SerializeLWData",
        ("moShell_c", 1216): "moConcept_c.SerializeResolvedData",
    }
