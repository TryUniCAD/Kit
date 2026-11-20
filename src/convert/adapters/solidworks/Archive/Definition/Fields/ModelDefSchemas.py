from types import MappingProxyType

# only concrete classes verified for the ordinary definition shape may publish object tags
KModelDefSchemas = MappingProxyType(
    {
        "uiPartDoc_c": (1,),
        "uiAssemblyDoc_c": (1,),
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
        "PWMaterialProperties_c": (1,),
        "uoJournal_c": (0,),
    }
)
