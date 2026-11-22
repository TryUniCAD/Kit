from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Part.PartSchemas import (
    KPartSchemas,
)

# current resolved object descriptors extend the pinned configuration class vocabulary without guessing schemas
KResolvedSchemas = MappingProxyType(
    {
        "moNodeName_c": KPartSchemas["moNodeName_c"],
        "moUnitComponent_c": KPartSchemas["moUnitComponent_c"],
        "suObList": KPartSchemas["suObList"],
        "AngleDim_c": (1,),
        "ParallelPlaneDistanceDim_c": (1,),
        "moAngleParameter_c": (1,),
        "moAtom_c": (1,),
        "moBaseBody_c": (1,),
        "moPMarkRecord_c": (1,),
        "moCommentsFolder_c": (1,),
        "moCompRefPlane_c": (1,),
        "moDefaultRefPlnData_c": (1,),
        "moDetailCabinet_c": (1,),
        "moDisplayAngularDim_c": (1,),
        "moDisplayDistanceDim_c": (1,),
        "moDocsFolder_c": (1,),
        "moEndSpec_c": (1,),
        "moEqnFolder_c": (1,),
        "moExtrusion_c": (1,),
        "moFavoriteFolder_c": (1,),
        "moFavoriteHandle_c": (1,),
        "moFeatureDimHandle_c": (1,),
        "moFromEndSpec_c": (1,),
        "moHistoryFolder_c": (1,),
        "moInkMarkupFolder_c": (1,),
        "moLengthParameter_c": (1,),
        "moMaterialFolder_c": (1,),
        "moOriginProfileFeature_c": (1,),
        "moProfileFeature_c": (1,),
        "moRefPlane_c": (1,),
        "moSelectionSetFolder_c": (1,),
        "moSensorFolder_c": (1,),
        "moSolidBodyFolder_c": (1,),
        "moSurfaceBodyFolder_c": (1,),
        "sgLineHandle": (1,),
        "sgPointHandle": (1,),
        "sgSketch": (1,),
    }
)
