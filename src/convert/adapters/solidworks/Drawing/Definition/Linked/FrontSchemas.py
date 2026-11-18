from types import MappingProxyType

from convert.adapters.solidworks.Drawing.Definition.Emission.BlankSchemas import (
    KBlankSchemas,
)

# concrete linked owners need explicit runtime schemas without widening the existing blank admission
KFrontSchemas = MappingProxyType(
    {
        **KBlankSchemas,
        **{
            ClassName: (1,)
            for ClassName in (
                "moScaleSysScale_c",
                "moLineStyle_c",
                "uiLFConfig_c",
                "moCompProfile_c",
                "moEdgeRef_c",
                "moFromSktEntSurfIdRep_c",
                "moEndFaceSurfIdRep_c",
                "moFR_c",
                "moChainComponent_c",
                "moReferenceChain_c",
                "moExtFeatureList_c",
                "moAbsoluteView",
                "moDrawingRefPlnData_c",
                "moDisplayProfileFeature_c",
                "moReferenceInternal_c",
                "moReferenceModel_c",
                "moExtFeature_c",
                "suObArray",
            )
        },
    }
)
