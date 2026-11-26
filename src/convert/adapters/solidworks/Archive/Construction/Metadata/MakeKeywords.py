from convert.adapters.solidworks.Archive.Construction.Metadata.FrameKeywords import (
    FrameKeywords,
)
from xml.etree.ElementTree import Element, SubElement
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordConfig import (
    KeywordConfig,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import (
    KeywordFeature,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeyFeatMut import (
    MakeKeyFeatMut,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# keywords must derive their complete xml and framing from modeled configurations features and presentation values rather than a stock feature table
def MakeKeywords(
    NameValue: str,
    Timestamp: int,
    ConfigValues: tuple[KeywordConfig, ...],
    FeatureValues: tuple[KeywordFeature, ...],
    *,
    CompactTags: bool = False,
) -> bytes:
    _ = ReadStyleText(NameValue, "keyword document name")
    if type(CompactTags) is not bool:
        raise TypeError("keyword framing requires an explicit compact mode")
    if type(Timestamp) is not int or not 0 <= Timestamp <= 0xFFFFFFFF:
        raise ValueError("keyword timestamp must fit unsigned unix seconds")
    if (
        type(ConfigValues) is not tuple
        or not ConfigValues
        or any(type(ItemValue) is not KeywordConfig for ItemValue in ConfigValues)
    ):
        raise TypeError("keywords require explicit typed configuration rows")
    if (
        type(FeatureValues) is not tuple
        or not FeatureValues
        or any(type(ItemValue) is not KeywordFeature for ItemValue in FeatureValues)
    ):
        raise TypeError("keywords require explicit typed feature rows")
    if len({ItemValue.IdValue for ItemValue in ConfigValues}) != len(
        ConfigValues
    ) or len({ItemValue.IdValue for ItemValue in FeatureValues}) != len(FeatureValues):
        raise ValueError(
            "keyword configuration and feature identifiers must be unique in their independent namespaces"
        )
    FeatureIds = {ItemValue.IdValue for ItemValue in FeatureValues}
    if any(
        ChildValue not in FeatureIds
        for ItemValue in FeatureValues
        for ChildValue in ItemValue.ChildIds
    ):
        raise ValueError(
            "keyword child references must identify actual emitted features"
        )
    RootValue = Element("Keywords", {"id": str(Timestamp), "Name": NameValue})
    for ItemValue in ConfigValues:
        _ = SubElement(
            RootValue,
            "Configuration",
            {
                "id": str(ItemValue.IdValue),
                "Name": ItemValue.NameValue,
                "Type": "ConfigurationManager",
                "Material": ItemValue.MaterialValue,
            },
        )
    HasDegrees = any(
        DimValue.UnitValue == "degree"
        for ItemValue in FeatureValues
        for DimValue in ItemValue.DimensionValues
    )
    if not HasDegrees and any(
        ItemValue.TagValue == "Sketch"
        and ItemValue.KindValue is None
        and not ItemValue.DimensionValues
        for ItemValue in FeatureValues
    ):
        raise ValueError(
            "undimensioned sketch type omission requires its native revolve angle"
        )
    for FeatureValue in FeatureValues:
        MakeKeyFeatMut(RootValue, FeatureValue)
    return FrameKeywords(RootValue, HasDegrees or CompactTags)
