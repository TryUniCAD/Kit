from convert.adapters.solidworks.Archive.Construction.System.SystemClasses import (
    KSystemFolders,
)
from convert.adapters.solidworks.Archive.Construction.Units.UnitVocabulary import (
    KUnitClasses,
)

# a complete archive inventory must reject additional owners outside the ordinary constructor grammar
KPrismClasses = (
    KSystemFolders
    | frozenset(KUnitClasses.values())
    | frozenset(
        (
            "moPart_c",
            "moConfigurationMgr_c",
            "moPartConfiguration_c",
            "moNodeName_c",
            "moUnitComponent_c",
            "moView_c",
            "moRelMgr_c",
            "moUnitsTable_c",
            "moVisualProperties_c",
            "moTransRefPlaneData_c",
            "gcXhatch_c",
            "uoModelData_c",
            "moExtObject_c",
            "suObList",
            "moDetailCabinet_c",
            "moRefPlane_c",
            "moDefaultRefPlnData_c",
            "moOriginProfileFeature_c",
            "moProfileFeature_c",
            "sgSketch",
            "sgPointHandle",
            "sgLineHandle",
            "moCompRefPlane_c",
            "moExtrusion_c",
            "moEndSpec_c",
            "moFromEndSpec_c",
            "moLengthParameter_c",
            "moAngleParameter_c",
            "moDisplayDistanceDim_c",
            "moDisplayAngularDim_c",
            "moFeatureDimHandle_c",
            "ParallelPlaneDistanceDim_c",
            "AngleDim_c",
            "moFavoriteHandle_c",
            "moSkDimHandleValG2_c",
            "sgPntPntDist",
            "moPointBackedUpData_c",
            "moSketchExtRef_w",
            "moCompSketchEntHandle_c",
            "sgExtEnt_c",
        )
    )
)
