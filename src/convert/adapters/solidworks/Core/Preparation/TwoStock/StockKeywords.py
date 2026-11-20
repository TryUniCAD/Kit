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
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import (
    MakeSketchKeys,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)
from convert.adapters.solidworks.Core.Preparation.TwoStock.TwoStockGraph import (
    TwoStockGraph,
)


# keyword references must address the same feature vertices and children as the resolved graph
def StockKeyRow(
    NodeValue: ArchiveNode,
    TagValue: str,
    Dimensions: tuple[KeywordDim, ...] = (),
    Children: tuple[int, ...] = (),
) -> KeywordFeature:
    return KeywordFeature(
        FieldInt(NodeValue.FieldsValue, "f08"),
        ReadNodeName(NodeValue),
        NodeValue.ClassValue.NameValue,
        TagValue,
        Dimensions,
        Children,
        None,
        None,
    )


# both stock drivers and their owning profiles must remain visible beside the depthless cut
def StockKeywords(
    GraphValue: TwoStockGraph, SettingsValue: PartBuildInput, NameValue: str
) -> bytes:
    SystemValue = GraphValue.SystemValue
    UnitValue = SettingsValue.DocumentUnits.LengthUnit
    RowsValue = tuple(
        StockKeyRow(NodeValue, "Feature") for NodeValue in SystemValue.FeatureValues
    )
    for StockValue in GraphValue.BossValues:
        Profile = StockValue.ProfileValue.ProfileValue
        RowsValue += (
            StockKeyRow(Profile, "Sketch"),
            StockKeyRow(
                StockValue.FeatureValue,
                "Extrusion",
                MakeSketchKeys((StockValue.DriverValue,), UnitValue),
                (FieldInt(Profile.FieldsValue, "f08"),),
            ),
        )
    RowsValue += MakeCutKeys(GraphValue.CutValue, (), UnitValue)
    Configs = tuple(
        KeywordConfig(
            FieldInt(NodeValue.FieldsValue, "f08"), ReadNodeName(NodeValue), ""
        )
        for NodeValue in SystemValue.ConfigValues
    )
    return MakeKeywords(
        NameValue, SettingsValue.HeaderValue.ModifiedAt, Configs, RowsValue
    )
