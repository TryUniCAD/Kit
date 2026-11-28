from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import (
    KeywordDim,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# keyword feature rows must retain actual graph identity explicit type vocabulary dimensions and bounded child references
@DataClass(frozen=True, slots=True)
class KeywordFeature:
    IdValue: int
    NameValue: str
    KindValue: str | None
    TagValue: str
    DimensionValues: tuple[KeywordDim, ...]
    ChildIds: tuple[int, ...]
    Dissectable: bool | None
    RootValue: bool | None

    # unsupported tags opaque dimensions and ambiguous child grammars must reject before the feature graph becomes an xml carrier
    def __post_init__(self) -> None:
        SheetMetalMaster = (
            self.IdValue == -1
            and self.TagValue == "Feature"
            and self.KindValue == "Sheet-Metal Master"
            and self.NameValue == ""
            and self.DimensionValues == ()
            and self.ChildIds == ()
            and self.Dissectable is None
            and self.RootValue is None
        )
        if type(self.IdValue) is not int or not (
            SheetMetalMaster or 1 <= self.IdValue <= 0x7FFFFFFF
        ):
            raise ValueError("keyword feature id must be a positive signed integer")
        _ = ReadStyleText(self.NameValue, "keyword feature name")
        if self.KindValue is not None:
            _ = ReadStyleText(self.KindValue, "keyword feature kind")
        if self.TagValue not in ("Feature", "Sketch", "Extrusion"):
            raise ValueError("unsupported keyword feature tag")
        if type(self.DimensionValues) is not tuple or any(
            type(ItemValue) is not KeywordDim for ItemValue in self.DimensionValues
        ):
            raise TypeError("keyword dimensions require explicit typed rows")
        if len({ItemValue.NameValue for ItemValue in self.DimensionValues}) != len(
            self.DimensionValues
        ):
            raise ValueError(
                "keyword dimension names must be distinct within their feature"
            )
        if (
            type(self.ChildIds) is not tuple
            or len(self.ChildIds) > 1
            or any(
                type(IdValue) is not int or not 1 <= IdValue <= 0x7FFFFFFF
                for IdValue in self.ChildIds
            )
        ):
            raise ValueError(
                "keyword child references require the recovered single child grammar"
            )
        if any(
            ValueInput is not None and type(ValueInput) is not bool
            for ValueInput in (self.Dissectable, self.RootValue)
        ):
            raise TypeError(
                "keyword dissection settings require explicit booleans or absence"
            )
