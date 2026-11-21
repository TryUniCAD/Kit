from collections.abc import Mapping

from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceFields import (
    ReadBoxString,
    RequireBox,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# source properties require their exact declared owner and one expected child
def ReadPropChild(
    RecordValue: object, KindValue: str, TagValue: str
) -> Mapping[str, object]:
    PropValue = NativeRecord(RecordValue)
    Attributes = NativeRecord(PropValue["attributes"])
    RequireBox(
        PropValue["tag"] == "Property"
        and Attributes["type"] == "App::Property" + KindValue,
        f"FreeCAD property has a different type for {Attributes['name']}",
    )
    Children = NativeRows(PropValue["children"])
    RequireBox(
        len(Children) == 1 and Children[0]["tag"] == TagValue,
        "FreeCAD property shape differs from the documented object",
    )
    return Children[0]


# each literal is read through its declared source property and value node
def ReadPropText(
    Properties: Mapping[str, object], NameValue: str, KindValue: str, TagValue: str
) -> str:
    Child = ReadPropChild(Properties[NameValue], KindValue, TagValue)
    return ReadBoxString(NativeRecord(Child["attributes"])["value"])


# a neutral default must match the value on its actual source owner
def RequireProp(
    Properties: Mapping[str, object],
    NameValue: str,
    KindValue: str,
    TagValue: str,
    Expected: str,
) -> None:
    RequireBox(
        ReadPropText(Properties, NameValue, KindValue, TagValue) == Expected,
        f"FreeCAD property {NameValue} is outside the admitted box policy",
    )


# zero declared entries cannot carry hidden source expressions or external links
def RequireEmpty(
    Properties: Mapping[str, object], NameValue: str, KindValue: str, TagValue: str
) -> None:
    Child = ReadPropChild(Properties[NameValue], KindValue, TagValue)
    RequireBox(
        NativeRecord(Child["attributes"])["count"] == "0" and not Child.get("children"),
        f"FreeCAD property {NameValue} contains unsupported defined entries",
    )
