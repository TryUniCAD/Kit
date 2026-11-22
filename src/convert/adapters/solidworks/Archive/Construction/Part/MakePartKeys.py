from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipsePlan import (
    EllipsePlan,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.CutGraph import CutGraph
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
from convert.adapters.solidworks.Archive.Construction.Part.MakeCutKeys import (
    MakeCutKeys,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.PartPlan import (
    KPartPlan,
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
    PlanValue: KPartPlan | EllipsePlan,
    SketchDims: tuple[KeywordDim, ...] = (),
    *,
    CutValue: CutGraph | None = None,
    CutSketchDims: tuple[KeywordDim, ...] = (),
    AdditionalRows: tuple[KeywordFeature, ...] = (),
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
    SecondDepth = PlanValue.SecondDepth
    DepthName = PlanValue.DepthName if type(PlanValue) is BlindPlan else "D1"
    DepthDims: tuple[KeywordDim, ...] = (
        KeywordDim(DepthName, PlanValue.DepthValue / ScaleValue, None),
    )
    if SecondDepth is not None:
        DepthDims += (KeywordDim("D2", SecondDepth / ScaleValue, None),)
    PlainValues = FeatureValues
    if CutValue is not None:
        if (
            FeatureValues[-2] is not CutValue.ProfileValue.ProfileValue
            or FeatureValues[-1] is not CutValue.FeatureValue
        ):
            raise ValueError("cut keywords must refer to the actual emitted history")
        PlainValues = FeatureValues[:-2]
    for IndexValue, NodeValue in enumerate(PlainValues):
        TagValue = (
            "Sketch"
            if IndexValue == len(PlainValues) - 2
            else "Extrusion" if IndexValue == len(PlainValues) - 1 else "Feature"
        )
        Dimensions = (
            DepthDims
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
    if CutValue is not None:
        RowsValue.extend(
            MakeCutKeys(CutValue, CutSketchDims, InputValue.DocumentUnits.LengthUnit)
        )
    return MakeKeywords(
        PlanValue.NameValue,
        InputValue.HeaderValue.ModifiedAt,
        ConfigValues,
        (*RowsValue, *AdditionalRows),
    )
