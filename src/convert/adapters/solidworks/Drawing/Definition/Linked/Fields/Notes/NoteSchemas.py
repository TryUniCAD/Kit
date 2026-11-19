from types import MappingProxyType

# only exact independently bound concrete runtime descriptors enter the drawing note graph
KNoteSchemas = MappingProxyType(
    {
        "moDisplayNote_c": (1,),
        "moFavoriteHandle_c": (1,),
        "moTextDataControl_c": (1,),
        "moTextDataSpaceHolder_c": (1,),
        "moTextDataChar_c": (1,),
        "moGenTextData_c": (1,),
        "moTextDataLineHead_c": (1,),
        "moGenericText_c": (1,),
        "moGenTextDataList_c": (1,),
        "moAbsolutePoint_c": (1,),
        "moCompBEntRef_c": (1,),
        "moCompCompositeEdge_c": (1,),
        "moCompEdge_c": (1,),
        "moGeneralCurveRef_w": (1,),
        "moCompNote_c": (1,),
        "moCompDetailItem_c": (1,),
        "moDetailItem_c": (1,),
        "moNoteData_c": (1,),
        "moAttachPointData_c": (1,),
        "moParametricPoint_c": (1,),
        "suHyperlink_c": (1,),
        "su_CMapStringToString": (0,),
        "su_CMapStringToInt": (0,),
    }
)
