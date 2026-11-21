from math import degrees as Degrees

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
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)


# keyword presentation must use the actual generated profile feature and angular parameter while preserving native consumed sketch framing
def MakeRevKeys(
    SystemValue: PartSystem,
    FeatureValues: tuple[ArchiveNode, ...],
    InputValue: PartBuildInput,
    PlanValue: RevolvePlan,
) -> bytes:
    ConfigValues = tuple(
        KeywordConfig(
            FieldInt(NodeValue.FieldsValue, "f08"), ReadNodeName(NodeValue), ""
        )
        for NodeValue in SystemValue.ConfigValues
    )
    RowsValue = tuple(
        KeywordFeature(
            FieldInt(NodeValue.FieldsValue, "f08"),
            ReadNodeName(NodeValue),
            NodeValue.ClassValue.NameValue,
            "Feature",
            (),
            (),
            None,
            None,
        )
        for NodeValue in FeatureValues[:-2]
    )
    ProfileValue, FeatureValue = FeatureValues[-2:]
    AnglesValue = (KeywordDim("D1", Degrees(PlanValue.AngleValue), "degree"),)
    if PlanValue.AgainstAngle is not None:
        Secondary = KeywordDim("D2", Degrees(PlanValue.AgainstAngle), "degree")
        AnglesValue = (
            (*AnglesValue, Secondary)
            if PlanValue.IsReverse
            else (Secondary, *AnglesValue)
        )
    RowsValue += (
        KeywordFeature(
            FieldInt(ProfileValue.FieldsValue, "f08"),
            ReadNodeName(ProfileValue),
            None,
            "Sketch",
            (),
            (),
            True,
            None,
        ),
        KeywordFeature(
            FieldInt(FeatureValue.FieldsValue, "f08"),
            ReadNodeName(FeatureValue),
            "Revolve",
            "Feature",
            AnglesValue,
            (),
            None,
            None,
        ),
    )
    return MakeKeywords(
        PlanValue.NameValue, InputValue.HeaderValue.ModifiedAt, ConfigValues, RowsValue
    )
