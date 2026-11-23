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
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordRef import (
    KeywordRef,
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
    FeatureValues: tuple[KeywordFeature | KeywordRef, ...],
    *,
    CompactTags: bool = False,
    NativeRows: bool = False,
) -> bytes:
    _ = ReadStyleText(NameValue, "keyword document name")
    if any(type(ValueInput) is not bool for ValueInput in (CompactTags, NativeRows)):
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
        or any(
            type(ItemValue) not in (KeywordFeature, KeywordRef)
            for ItemValue in FeatureValues
        )
    ):
        raise TypeError("keywords require explicit typed feature rows")
    if len({ItemValue.IdValue for ItemValue in ConfigValues}) != len(
        ConfigValues
    ) or len({ItemValue.IdValue for ItemValue in FeatureValues}) != len(FeatureValues):
        raise ValueError(
            "keyword configuration and feature identifiers must be unique in their independent namespaces"
        )
    OwnerValues = tuple(
        ItemValue for ItemValue in FeatureValues if type(ItemValue) is KeywordFeature
    )
    FeatureIds = {ItemValue.IdValue for ItemValue in OwnerValues}
    if any(
        ChildValue not in FeatureIds
        for ItemValue in OwnerValues
        for ChildValue in ItemValue.ChildIds
    ):
        raise ValueError(
            "keyword child references must identify actual emitted features"
        )
    RootValue = Element("Keywords", {"id": str(Timestamp), "Name": NameValue})
    for ItemValue in ConfigValues:
        PutKeyCfgMut(RootValue, ItemValue)
    HasDegrees = any(
        DimValue.UnitValue == "degree"
        for ItemValue in OwnerValues
        for DimValue in ItemValue.DimensionValues
    )
    if (
        not NativeRows
        and not HasDegrees
        and any(
            ItemValue.TagValue == "Sketch"
            and ItemValue.KindValue is None
            and not ItemValue.DimensionValues
            for ItemValue in OwnerValues
        )
    ):
        raise ValueError(
            "undimensioned sketch type omission requires its native revolve angle"
        )
    for FeatureValue in FeatureValues:
        if isinstance(FeatureValue, KeywordFeature):
            MakeKeyFeatMut(RootValue, FeatureValue, NativeRows=NativeRows)
        else:
            PutKeyRefMut(RootValue, FeatureValue)
    return FrameKeywords(RootValue, HasDegrees or CompactTags)


# configuration material has its own optional attribute on the native manager row
def PutKeyCfgMut(RootValue: Element, ConfigValue: KeywordConfig) -> None:
    AttrsValue = {
        "id": str(ConfigValue.IdValue),
        "Name": ConfigValue.NameValue,
        "Type": "ConfigurationManager",
    }
    if ConfigValue.MaterialValue is not None:
        AttrsValue["Material"] = ConfigValue.MaterialValue
    _ = SubElement(RootValue, "Configuration", AttrsValue)


# the native occurrence type is a declared suffix on the actual file stem
def PutKeyRefMut(RootValue: Element, RefValue: KeywordRef) -> None:
    _ = SubElement(
        RootValue,
        "Reference",
        {
            "id": str(RefValue.IdValue),
            "Name": RefValue.NameValue,
            "Type": RefValue.FileStem + "-",
        },
    )
