from __future__ import annotations

from interchange.serialization.DecodeEnum import DecodeEnum
from interchange.serialization.DecodeTagged import DecodeTagged, KTagNames
from interchange.serialization.DecodeTyped import DecodeTyped
from interchange.serialization.WireData import KWireData


# the root check already covers every nested value so recursion must not walk each subtree again
def DecodeChecked(DataValue: KWireData) -> object:
    if isinstance(DataValue, list):
        return [DecodeChecked(ItemValue) for ItemValue in DataValue]
    if not isinstance(DataValue, dict):
        return DataValue
    if len(DataValue) == 1 and next(iter(DataValue)) in KTagNames:
        return DecodeTagged(DataValue, DecodeChecked)
    if "$enum" in DataValue:
        return DecodeEnum(DataValue, DecodeChecked)
    if "$type" not in DataValue:
        return {
            KeyValue: DecodeChecked(ItemValue)
            for KeyValue, ItemValue in DataValue.items()
        }
    return DecodeTyped(DataValue, DecodeChecked)
