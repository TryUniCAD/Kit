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
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import (
    MakeSketchKeys,
)
from convert.adapters.solidworks.Archive.Construction.Sweeps.Sketch.SweepProfiles import (
    SweepProfiles,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)


# sweep index rows take their names and dimensions from the actual allocated ordinary graph
def SweepKeyRow(
    NodeValue: ArchiveNode,
    TagValue: str,
    Dimensions: tuple[KeywordDim, ...] = (),
    KindValue: str | None = None,
) -> KeywordFeature:
    ClassValue = NodeValue.ClassValue
    if not isinstance(ClassValue, RuntimeClass):
        raise ValueError("ordinary sweep keys require a concrete feature owner")
    return KeywordFeature(
        FieldInt(NodeValue.FieldsValue, "f08"),
        ReadNodeName(NodeValue),
        ClassValue.NameValue if KindValue is None else KindValue,
        TagValue,
        Dimensions,
        (),
        None,
        None,
    )


# both editable dimensions and the swept boss keep their own explicitly typed keyword rows
def MakeSweepKeys(
    NameValue: str,
    SystemValue: PartSystem,
    ProfilesValue: SweepProfiles,
    SweepValue: ArchiveNode,
    InputValue: PartBuildInput,
) -> bytes:
    ConfigRows = tuple(
        KeywordConfig(
            FieldInt(NodeValue.FieldsValue, "f08"), ReadNodeName(NodeValue), ""
        )
        for NodeValue in SystemValue.ConfigValues
    )
    UnitValue = InputValue.DocumentUnits.LengthUnit
    KeyRows = (
        *(SweepKeyRow(NodeValue, "Feature") for NodeValue in SystemValue.FeatureValues),
        SweepKeyRow(
            ProfilesValue.SectionValue,
            "Sketch",
            MakeSketchKeys((ProfilesValue.DiameterValue,), UnitValue),
        ),
        SweepKeyRow(
            ProfilesValue.PathValue,
            "Sketch",
            MakeSketchKeys((ProfilesValue.RadiusValue,), UnitValue),
        ),
        SweepKeyRow(SweepValue, "Feature", KindValue="Sweep"),
    )
    return MakeKeywords(NameValue, InputValue.OutputValue.SavedAt, ConfigRows, KeyRows)
