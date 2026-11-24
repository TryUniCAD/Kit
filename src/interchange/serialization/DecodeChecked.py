from __future__ import annotations

from interchange.serialization.DecodeEnum import DecodeEnum
from interchange.serialization.DecodeRecord import DecodeRecord
from interchange.serialization.DecodeTagged import DecodeTagged
from interchange.serialization.DecodeTagged import KTagNames
from interchange.serialization.DecodeTyped import DecodeTyped
from interchange.serialization.WireData import KWireData


# the root check already covers every nested value so recursion must not walk each subtree again
def DecodeChecked(DataValue: KWireData) -> object:
    if isinstance(DataValue, list):
        return [DecodeChecked(ItemValue) for ItemValue in DataValue]
    if not isinstance(DataValue, dict):
        return DataValue
    if len(DataValue) == 1 and next(iter(DataValue)) in KTagNames:
        TagName = next(iter(DataValue))
        TagValue = DataValue[TagName]
        if TagName == "$bytes":
            return DecodeTagged(TagName, TagValue)
        if not isinstance(TagValue, list):
            raise ValueError(f"{TagName} value must be a list")
        return DecodeTagged(
            TagName, [DecodeChecked(ItemValue) for ItemValue in TagValue]
        )
    if "$enum" in DataValue:
        return DecodeEnum(DataValue, DecodeChecked)
    if "$type" not in DataValue:
        return {
            KeyValue: DecodeChecked(ItemValue)
            for KeyValue, ItemValue in DataValue.items()
        }
    return DecodeRecord(DataValue, DecodeTyped(DataValue), DecodeChecked)
