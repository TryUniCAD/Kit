from hashlib import sha256 as CalcSha

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
from convert.adapters.solidworks.Core.Preparation.TwoStock.PrepareStockPart import (
    PrepareStockPart,
)
from convert.adapters.solidworks.Core.Writing.Measured.MeasOracle import KOraclePart
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.PublishMeasMut import (
    PublishMeasMut,
)
from convert.adapters.solidworks.Core.Writing.Stocks.ReadStockMeas import ReadStockMeas
from convert.adapters.solidworks.Core.Writing.Stocks.StockTarget import StockTarget
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument


# measured publication depends on the complete neutral regeneration matching every archived byte
def WriteStocksMut(
    DocumentValue: CadDocument,
    TargetValue: KTargetType,
    OptionsValue: WriteOptions | None,
) -> WriteResult:
    Settings = CheckPartOpts(OptionsValue)
    Measurement, PreparedOptions = ReadStockMeas(
        Settings, DocumentValue.metadata.get("name")
    )
    OutputPath = StockTarget(TargetValue, PreparedOptions, Measurement.LocatorValue)
    Payload = PrepareStockPart(
        DocumentValue,
        OutputPath or TargetValue,
        Measurement.EpochValue,
        PreparedOptions,
    ).BytesValue
    if (
        len(Payload) != Measurement.SizeValue
        or CalcSha(Payload).hexdigest() != Measurement.CandidateSha
    ):
        raise ValueError(
            "regenerated selected stock part has no exact native measurement"
        )
    Evidence = FreezeMapping(
        {
            KPartMeasureOpt: FreezeMapping(
                {
                    "generated_sha256": Measurement.CandidateSha,
                    "oracle_build": KOraclePart["build"],
                    "native_result_sha256": Measurement.ResultSha,
                    "edit_record_sha256": Measurement.EditSha,
                    "reopen_record_sha256": Measurement.ReopenSha,
                }
            )
        }
    )
    return PublishMeasMut(TargetValue, OutputPath, Settings, Payload, Evidence)
