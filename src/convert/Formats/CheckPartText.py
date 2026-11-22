from collections.abc import Mapping
from typing import cast as CastValue

from interchange.document.Models.DocumentModel import CadDocument


# publishing the part without its unavailable text would hide the original inspection cause
def CheckPartText(DocumentValue: CadDocument) -> None:
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
