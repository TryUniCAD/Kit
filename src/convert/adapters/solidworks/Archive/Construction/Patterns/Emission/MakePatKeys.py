from dataclasses import replace as ReplaceValue

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
from convert.adapters.solidworks.Archive.Construction.Patterns.Emission.ReadPatAngle import (
    ReadPatAngle,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Graph.PatPartGraph import (
    PatPartGraph,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import (
    MakeSketchKeys,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
    RequireNode,
)
from convert.adapters.solidworks.Core.Preparation.TwoStock.StockKeywords import (
    StockKeyRow,
)

# these archive runtime classes have independent keyword feature vocabulary in the measured part
KPatKeyKinds = {
    "moRefAxis_c": "Axis",
    "moRefPlane_c": "Plane",
    "moLPattern_c": "LPattern",
}


# the ordinary pattern keyword stream indexes feature groups and orders their persistent ids lexically
def PatKeyOrder(Value: KeywordFeature) -> tuple[str, str]:
    return Value.TagValue, str(Value.IdValue)


# indexed feature rows refer to actual graph owners and their measured keyword type names
def PatKeyRow(
    Value: ArchiveNode, DimsValue: tuple[KeywordDim, ...] = ()
) -> KeywordFeature:
    RowValue = StockKeyRow(Value, "Feature", DimsValue)
    return ReplaceValue(
        RowValue,
        KindValue=KPatKeyKinds.get(Value.ClassValue.NameValue, RowValue.KindValue),
    )


# the local index exposes only the two active drivers of the actual pattern owner
def ReadPatKeyDims(GraphValue: PatPartGraph) -> tuple[KeywordDim, ...]:
    CountDrive, PitchDrive, *_ = GraphValue.DriverValues
    Count = RequireNode(CountDrive.ParameterValue, "moIntegerParameter_c")
    Pitch = RequireNode(PitchDrive.ParameterValue, "moLengthParameter_c")
    PatternFields = RequireNode(GraphValue.PatternValue, "moLPattern_c").FieldsValue
    if (
        PatternFields.get("f1258") is not CountDrive.DisplayValue
        or PatternFields.get("f1260") is not PitchDrive.DisplayValue
        or Count.FieldsValue.get("owner") is not GraphValue.PatternValue
        or Pitch.FieldsValue.get("owner") is not GraphValue.PatternValue
        or ReadNodeName(Count) != "D1"
        or ReadNodeName(Pitch) != "D3"
    ):
        raise ValueError("pattern Keywords require the actual live count and pitch")
    UnitValue = GraphValue.StockValue.SettingsValue.DocumentUnits.LengthUnit
    return (
        KeywordDim("D1", FieldInt(Count.FieldsValue, "f58"), None),
        *MakeSketchKeys((PitchDrive,), UnitValue),
    )


# the complete index includes the stock sketches and operations and the actual local pattern datums
def MakePatKeys(GraphValue: PatPartGraph) -> bytes:
    StockValue = GraphValue.StockValue
    SystemValue = StockValue.SystemValue
    Settings = StockValue.SettingsValue
    (Config,) = SystemValue.ConfigValues
    Configs = (
        KeywordConfig(FieldInt(Config.FieldsValue, "f08"), ReadNodeName(Config), None),
    )
    UnitValue = Settings.DocumentUnits.LengthUnit
    Words = tuple(PatKeyRow(NodeValue) for NodeValue in SystemValue.FeatureValues)
    for StockBoss in (StockValue.PlateValue, StockValue.SeedValue):
        Profile = StockBoss.ProfileValue.ProfileValue
        Words += (
            StockKeyRow(Profile, "Sketch"),
            StockKeyRow(
                StockBoss.FeatureValue,
                "Extrusion",
                MakeSketchKeys((StockBoss.DriverValue,), UnitValue),
                (FieldInt(Profile.FieldsValue, "f08"),),
            ),
        )
    AngleDims = ReadPatAngle(GraphValue)
    if GraphValue.AxisValue is not None:
        Words += (
            PatKeyRow(GraphValue.AxisValue),
            PatKeyRow(GraphValue.PlaneValue, AngleDims),
        )
    Words += (PatKeyRow(GraphValue.PatternValue, ReadPatKeyDims(GraphValue)),)
    OrderedWords = tuple(sorted(Words, key=PatKeyOrder))
    return MakeKeywords(
        ReadNodeName(SystemValue.RootValue),
        Settings.HeaderValue.ModifiedAt,
        Configs,
        OrderedWords,
        CompactTags=GraphValue.AxisValue is None,
    )
