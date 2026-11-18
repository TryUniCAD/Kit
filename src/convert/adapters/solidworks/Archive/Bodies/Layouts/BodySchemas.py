from types import MappingProxyType

# only concrete runtime descriptors with proven ordinary manager bodies enter the typed graph
KBodySchemas = MappingProxyType(
    {
        "moAssyMassPropsCache_c": (1,),
        "moCStringHandle_c": (1,),
        "moConfigObject_c": (1,),
        "moConfig_c": (1,),
        "moConfigurationMgr_c": (1,),
        "moConfiguration_c": (1,),
        "moContextChainComponent_c": (1,),
        "moCustomPropertyList": (1,),
        "moExtFeatureList_c": (1,),
        "moExtFeature_c": (1,),
        "moExtObject_c": (1,),
        "moLinkedAtomIdNode_c": (1,),
        "moNodeName_c": (1,),
        "moPartConfiguration_c": (1,),
        "moReferenceChain_c": (1,),
        "moVisualProperties_c": (1,),
        "suObList": (1,),
    }
)
