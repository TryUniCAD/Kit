from types import MappingProxyType

# only exact independently bound concrete runtime descriptors enter the drawing note graph
KNoteSchemas = MappingProxyType(
    {
        "moDisplayNote_c": (1,),
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
