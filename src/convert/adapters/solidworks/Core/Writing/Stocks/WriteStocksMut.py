from hashlib import sha256 as CalcSha

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.TransferContract import CapTransfer, TransferMode
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.Readback.IsStockRead import (
    IsStockRead,
)
from convert.adapters.solidworks.Core.Preparation.TwoStock.PrepareStockPart import (
    PrepStockPart,
)
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Stocks.StockTarget import (
    StockTarget,
)
from convert.adapters.solidworks.Core.Writing.Stocks.ReadStockMeas import ReadStockMeas
from convert.adapters.Staging.WriteWholeMut import WriteWholeMut
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument


# actual neutral emission must reproduce the full measured file before any destination write
def WriteStocksMut(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    OptionsValue: WriteOptions | None,
) -> WriteResult:
    Settings = CheckPartOpts(OptionsValue)
    Measurement = ReadStockMeas(Settings)
    OutputPath = StockTarget(TargetValue, Settings, Measurement.LocatorValue)
    Candidate = PrepStockPart(
        DocumentValue,
        OutputPath or TargetValue,
        Measurement.EpochValue,
        Settings,
    )
    Payload = Candidate.BytesValue
    if (
        len(Payload) != Measurement.SizeValue
        or CalcSha(Payload).hexdigest() != Measurement.CandidateSha
    ):
        raise ValueError(
            "regenerated selected stock part has no exact native measurement"
        )
    if OutputPath is None:
        WriteWholeMut(TargetValue, Payload)
    else:
        with OutputPath.open("wb" if Settings.overwrite else "xb") as OutputFile:
            if OutputFile.write(Payload) != len(Payload):
                raise OSError("short selected stock part write")
    return WriteResult(
        OutputPath,
        KPartFormatId,
        len(Payload),
        metadata=FreezeMapping(
            {
                KPartMeasureOpt: FreezeMapping(
                    {
                        "generated_sha256": Measurement.CandidateSha,
                        "native_result_sha256": Measurement.ResultSha,
                        "edit_record_sha256": Measurement.EditSha,
                        "reopen_record_sha256": Measurement.ReopenSha,
                    }
                )
            }
        ),
        transfers=(
            tuple(
                CapTransfer(CapabilityValue, TransferMode.KNative)
                for CapabilityValue in sorted(DocumentValue.capabilities)
            )
            if IsStockRead(DocumentValue)
            else ()
        ),
        vendor_loadable=True,
        application_usable=True,
    )
