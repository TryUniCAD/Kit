from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.base.WritePolicy import GetFormatKey
from interchange.document.Models.DocumentModel import CadDocument

# unavailable text status belongs to the native solidworks part decoder
KNativePart = "solidworks.sldprt"


# publishing the part without its unavailable text would hide the original inspection cause
def CheckPartText(DocumentValue: CadDocument) -> None:
    if GetFormatKey(DocumentValue.source.format_id) != KNativePart:
        return
    InfoValue = DocumentValue.metadata.get("solidworks.part_text_properties")
    if not isinstance(InfoValue, Mapping):
        return
    StatusValue = CastValue(Mapping[str, object], InfoValue)
    if StatusValue.get("status") != "unsupported":
        return
    MessageValue = "SOLIDWORKS part text properties are unavailable for writing"
    CauseValue = StatusValue.get("diagnostic")
    if isinstance(CauseValue, str) and CauseValue:
        MessageValue += f" ({CauseValue})"
    raise ValueError(MessageValue)
