from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordConfig import (
    KeywordConfig,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import (
    KeywordDim,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import (
    KeywordFeature,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeywords import (
    MakeKeywords,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)


# part keyword rows must project the actual generated feature and configuration identities with the driving depth in explicit presentation units
def MakePartKeys(
    SystemValue: PartSystem,
    FeatureValues: tuple[ArchiveNode, ...],
    InputValue: PartBuildInput,
    PlanValue: BlindPlan,
    SketchDims: tuple[KeywordDim, ...] = (),
) -> bytes:
    ConfigValues = tuple(
        KeywordConfig(
            FieldInt(NodeValue.FieldsValue, "f08"), ReadNodeName(NodeValue), ""
        )
        for NodeValue in SystemValue.ConfigValues
    )
    RowsValue: list[KeywordFeature] = []
    ScaleValue = {"mm": 0.001, "m": 1.0, "in": 0.0254}[
        InputValue.DocumentUnits.LengthUnit
    ]
    for IndexValue, NodeValue in enumerate(FeatureValues):
        TagValue = (
            "Sketch"
            if IndexValue == len(FeatureValues) - 2
            else "Extrusion" if IndexValue == len(FeatureValues) - 1 else "Feature"
        )
        Dimensions = (
            (KeywordDim("D1", PlanValue.DepthValue / ScaleValue, None),)
            if TagValue == "Extrusion"
            else SketchDims if TagValue == "Sketch" else ()
        )
        RowsValue.append(
            KeywordFeature(
                FieldInt(NodeValue.FieldsValue, "f08"),
                ReadNodeName(NodeValue),
                NodeValue.ClassValue.NameValue,
                TagValue,
                Dimensions,
                (),
                None,
                None,
            )
        )
    return MakeKeywords(
        PlanValue.NameValue,
        InputValue.HeaderValue.ModifiedAt,
        ConfigValues,
        tuple(RowsValue),
    )
