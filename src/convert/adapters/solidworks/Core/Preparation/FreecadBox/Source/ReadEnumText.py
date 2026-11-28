from collections.abc import Mapping

from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceFields import (
    ReadBoxString,
    RequireBox,
)


# named source enums need the actual selected caption rather than a presumed default index
def ReadEnumText(Properties: Mapping[str, object], NameValue: str) -> str:
    RecordValue = NativeRecord(Properties[NameValue])
    Attributes = NativeRecord(RecordValue["attributes"])
    RequireBox(
        RecordValue["tag"] == "Property"
        and Attributes["type"] == "App::PropertyEnumeration",
        "FreeCAD named enumeration has another type",
    )
    Index, Items = NativeRows(RecordValue["children"])
    IndexValues = NativeRecord(Index["attributes"])
    RequireBox(
        Index["tag"] == "Integer"
        and IndexValues["CustomEnum"] == "true"
        and Items["tag"] == "CustomEnumList",
        "FreeCAD named enumeration has another layout",
    )
    Selected = int(ReadBoxString(IndexValues["value"]))
    Choices = NativeRows(Items["children"])
    Expected = int(ReadBoxString(NativeRecord(Items["attributes"])["count"]))
    RequireBox(
        Expected == len(Choices)
        and 0 <= Selected < len(Choices)
        and all(RowValue["tag"] == "Enum" for RowValue in Choices),
        "FreeCAD named enumeration contains an invalid selector",
    )
    Captions = tuple(
        ReadBoxString(NativeRecord(RowValue["attributes"])["value"])
        for RowValue in Choices
    )
    return Captions[Selected]
