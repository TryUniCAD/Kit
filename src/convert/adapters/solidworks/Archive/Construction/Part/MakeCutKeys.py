from convert.adapters.solidworks.Archive.Construction.Extrusion.CutGraph import CutGraph
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import (
    KeywordDim,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import (
    KeywordFeature,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import (
    MakeSketchKeys,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)


# the cut keywords refer to the actual profile and its live depth parameter
def MakeCutKeys(
    CutValue: CutGraph, SketchDims: tuple[KeywordDim, ...], UnitValue: str
) -> tuple[KeywordFeature, KeywordFeature]:
    ProfileValue = CutValue.ProfileValue.ProfileValue
    FeatureValue = CutValue.FeatureValue
    ProfileId = FieldInt(ProfileValue.FieldsValue, "f08")
    return (
        KeywordFeature(
            ProfileId,
            ReadNodeName(ProfileValue),
            ProfileValue.ClassValue.NameValue,
            "Sketch",
            SketchDims,
            (),
            None,
            None,
        ),
        KeywordFeature(
            FieldInt(FeatureValue.FieldsValue, "f08"),
            ReadNodeName(FeatureValue),
            None,
            "Extrusion",
            MakeSketchKeys((CutValue.DepthValue,), UnitValue),
            (ProfileId,),
            None,
            None,
        ),
    )
