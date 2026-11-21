from types import MappingProxyType

# the ordinary profile admits only its measured concrete class descriptors
KOrdDefSchemas = MappingProxyType(
    {
        "uiPartDoc_c": (1,),
        "moANSI_c": (1,),
        "moISO_c": (1,),
        "moBS_c": (1,),
        "moDIN_c": (1,),
        "moJIS_c": (1,),
        "moGB_c": (1,),
        "moGOST_c": (1,),
        "moLineStyle_c": (1,),
        "uiLFConfig_c": (1,),
        "uiLineFontMgr_c": (1,),
        "uiUserModelEnv_c": (1,),
        "moBomInfoMgr_c": (1,),
        "uoJournal_c": (0,),
    }
)

# assembly and appearance classes remain available to established aggregate paths
KModelDefSchemas = MappingProxyType(
    {
        **KOrdDefSchemas,
        "uiAssemblyDoc_c": (1,),
        "PWMaterialProperties_c": (1,),
    }
)
