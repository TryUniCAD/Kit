from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from convert.adapters.freecad.Native import NativeObject


# the dependency starts with the real pad profile and the unique saved length formula
def ReadPadExpr(PadValue: NativeObject) -> tuple[str, str] | None:
    if PadValue.type_id != "PartDesign::Pad":
        return None
    Profile = PadValue.properties.get("Profile")
    Engine = PadValue.properties.get("ExpressionEngine")
    if (
        Profile is None
        or Profile.get("type") != "App::PropertyLinkSub"
        or len(Profile) != 1
        or Engine is None
        or Engine.get("type") != "App::PropertyExpressionEngine"
        or len(Engine) != 1
    ):
        return None
    LinkValue, GroupValue = Profile[0], Engine[0]
    if (
        LinkValue.tag != "LinkSub"
        or set(LinkValue.attrib) != {"count", "value"}
        or LinkValue.get("count") != "0"
        or len(LinkValue)
        or GroupValue.tag != "ExpressionEngine"
        or GroupValue.get("count") != str(len(GroupValue))
        or any(RowValue.tag != "Expression" for RowValue in GroupValue)
    ):
        return None
    LengthRows = tuple(
        RowValue
        for RowValue in GroupValue
        if RowValue.get("path", "").lstrip(".") == "Length"
    )
    if len(LengthRows) != 1 or LengthRows[0].get("path") not in {"Length", ".Length"}:
        return None
    ProfileName = LinkValue.get("value")
    Source = LengthRows[0].get("expression")
    return (ProfileName, Source) if ProfileName and Source else None
