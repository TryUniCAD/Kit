from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ResolvedSchemas import (
    KResolvedSchemas,
)

from convert.adapters.solidworks.Drawing.Definition.Emission.BlankInherited import (
    KBlankInherited,
)

# new drawing owners retain pinned runtime schemas rather than inheriting provisional class placeholders
KBlankSchemas = MappingProxyType(
    {
        **{ClassName: KResolvedSchemas[ClassName] for ClassName in KBlankInherited},
        "moAbsoluteRefPlnData_c": (1,),
        "moBlockFolder_c": (1,),
        "moDetailFolder_c": (1,),
        "moDrSheet": (1,),
        "moDrawing_c": (1,),
        "moDrwCompPropMgr_c": (1,),
        "moLayerMask_c": (1,),
        "moLayerMgr_c": (1,),
        "moMarkupCommentFolder_c": (1,),
        "moANSI_c": (1,),
        "moISO_c": (1,),
        "moBS_c": (1,),
        "moDIN_c": (1,),
        "moJIS_c": (1,),
        "moGB_c": (1,),
        "moGOST_c": (1,),
        "uiDrawingDoc_c": (1,),
        "uiLineFontMgr_c": (1,),
        "uoJournal_c": (0,),
        "uoSketch": (1,),
    }
)
