from collections.abc import Mapping
from pathlib import Path as FilePath
from typing import cast as CastValue

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WritePolicy import GetFormatKey
from convert.adapters.registry.RegistryWriteApi import WriteLookup
from interchange.document.Models.DocumentModel import CadDocument

# only the native part reader owns the explicit optional text refusal status
KNativePart = "solidworks.sldprt"


# a strict conversion must refuse missing source text before the selected writer can publish output
def CheckSourceText(
    DocumentValue: CadDocument,
    SourceFormat: str,
    TargetValue: KTargetType,
    DestFormat: str | None,
    LookupValue: WriteLookup,
) -> None:
    if GetFormatKey(SourceFormat) != KNativePart:
        return
    InfoValue = DocumentValue.metadata.get("solidworks.part_text_properties")
    if (
        not isinstance(InfoValue, Mapping)
        or CastValue(Mapping[str, object], InfoValue).get("status") != "unsupported"
    ):
        return
    WriterValue = (
        LookupValue.GetWriter(DestFormat)
        if DestFormat
        else LookupValue.PickWriter(DocumentValue, TargetValue)
    )
    TargetFormat = GetFormatKey(WriterValue.info.FormatId)
    if (
        TargetFormat == KNativePart
        and GetFormatKey(DestFormat or TargetFormat) == KNativePart
        and (
            not isinstance(TargetValue, (str, FilePath))
            or FilePath(TargetValue).suffix.casefold() in WriterValue.info.PartExts
        )
    ):
        return
    raise ValueError(
        "SOLIDWORKS part text properties are unavailable for strict cross-format conversion"
    )
