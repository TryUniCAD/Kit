from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.base.WritePolicy import GetFormatKey
from interchange.document.Models.DocumentModel import CadDocument

# only the native part reader owns the explicit optional text refusal status
KNativePart = "solidworks.sldprt"

# serialized neutral snapshots can retain explicit inspection status from a prior source
KNeutralJson = "interchange.json"


# unsupported native text must retain its inspection cause when a write is refused
def CheckSourceText(
    DocumentValue: CadDocument,
    ReaderFormat: str | None,
    WriterFormat: str,
    ReaderOpts: ReadOptions | None,
) -> None:
    if GetFormatKey(DocumentValue.source.format_id) != KNativePart:
        return
    InfoValue = DocumentValue.metadata.get("solidworks.part_text_properties")
    if not isinstance(InfoValue, Mapping):
        return
    StatusValue = CastValue(Mapping[str, object], InfoValue)
    if StatusValue.get("status") != "unsupported":
        return
    if (
        ReaderFormat is not None
        and GetFormatKey(ReaderFormat) == GetFormatKey(WriterFormat) == KNeutralJson
        and (
            ReaderOpts is None
            or (
                ReaderOpts.include_brep
                and ReaderOpts.include_tessellation
                and ReaderOpts.configuration is None
            )
        )
    ):
        return
    MessageValue = "SOLIDWORKS part text properties are unavailable for writing"
    CauseValue = StatusValue.get("diagnostic")
    if isinstance(CauseValue, str) and CauseValue:
        MessageValue += f" ({CauseValue})"
    raise ValueError(MessageValue)
