from convert.adapters.solidworks.Container.Format import (
    SOLID_BODY_FEATURE_TYPES as SolidBodyFeatureTypes,
)
from convert.adapters.solidworks.Core.Native import NativeFeature


# this definition exists because focused behavior needs one stable owner
def SolidBody(Features: tuple[NativeFeature, ...]) -> NativeFeature | None:
    return next(
        (
            Feature
            for Feature in Features
            if Feature.kind.casefold().strip() in SolidBodyFeatureTypes
        ),
        None,
    )
