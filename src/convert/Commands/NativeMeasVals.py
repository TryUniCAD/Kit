from json import loads as LoadJson
from pathlib import Path as FilePath

from convert.adapters.Fusion.Measurement.FusionMeasOpt import KFusionMeasOpt
from convert.adapters.Fusion.Bridge.WriterInfo import KWriterInfo as KFusionInfo
from convert.adapters.solidworks.Container.Format import KPartFormatId

from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)

# receipt files contain bounded text metadata read before the writer receives any input
KReceiptLimit = 1024 * 1024


# the cli loads only the caller selected report and leaves all writer access in memory
def NativeMeasVals(
    ReceiptPath: FilePath | None,
    TargetPath: FilePath,
    FormatId: str,
) -> dict[str, object]:
    Values: dict[str, object] = {"require_native_transfers": True}
    if ReceiptPath is None:
        return Values
    if FormatId not in (KPartFormatId, KFusionInfo.FormatId):
        raise ValueError(
            "native measurement requires a SOLIDWORKS or Fusion part writer"
        )
    ReceiptKey = KPartMeasureOpt if FormatId == KPartFormatId else KFusionMeasOpt
    try:
        ReceiptPath = ReceiptPath.expanduser()
    except RuntimeError as ErrorInfo:
        raise ValueError(
            "native measurement receipt home directory is unavailable"
        ) from ErrorInfo
    if ReceiptPath.resolve() == TargetPath.resolve():
        raise ValueError("native measurement and output must use separate paths")
    with ReceiptPath.open("rb") as ReceiptFile:
        Payload = ReceiptFile.read(KReceiptLimit + 1)
    if len(Payload) > KReceiptLimit:
        raise ValueError("native measurement receipt exceeds the CLI input limit")
    Values[ReceiptKey] = LoadJson(Payload)
    return Values
