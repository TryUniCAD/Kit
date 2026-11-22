from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Shells.SaveTreeFields import (
    KSaveTreeFields,
    KSaveTreeVirts,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Shells.ShellFields import (
    KShellFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Shells.StockSaveFields import (
    KStockSaveFields,
)
from convert.adapters.solidworks.Archive.Resolved.UseEdgeCtxMut import UseEdgeCtxMut


# native saved shells reuse the part context and its typed face references
def UseShellCtxMut(ContextValue: BodyContext) -> None:
    UseEdgeCtxMut(ContextValue)
    ContextValue.LayoutsValue = {
        **ContextValue.LayoutsValue,
        **KStockSaveFields,
        **KShellFields,
        **KSaveTreeFields,
    }
    ContextValue.SchemasValue = {
        **ContextValue.SchemasValue,
        "ThreeDRadiusDim_c": (1,),
        "moBBoxCenterData_c": (1,),
        "moCompFace_c": (1,),
        "moCompFeature_c": (1,),
        "moFaceRef_c": (1,),
        "moFtrFolder_c": (1,),
        "moHistoryFeatItemData_c": (1,),
        "moNotesAreaFtrFolder_c": (1,),
        "moPMarkRecord_c": (1,),
        "moPerBodyChooserData_c": (1,),
        "moShell_c": (1,),
        "moSketchChain_c": (1,),
        "moSketchRegion_c": (1,),
    }
    ContextValue.VirtualValue = {
        **ContextValue.VirtualValue,
        **KSaveTreeVirts,
        ("moShell_c", 1000): "moFeature_c.SerializeXmlData",
        ("moShell_c", 1016): True,
        ("moShell_c", 1208): "moConcept_c.SerializeLWData",
        ("moShell_c", 1216): "moConcept_c.SerializeResolvedData",
    }
    ContextValue.FlagsValue["read_shell"] = 1
