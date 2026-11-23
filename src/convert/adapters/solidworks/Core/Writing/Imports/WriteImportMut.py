from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.TransferContract import CapTransfer, TransferMode
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Core.Writing.Imports.ImportMeasure import ImportMeasure
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.PublishMeasMut import (
    PublishMeasMut,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadPartMeas import KOraclePart
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumDocument import Capability, Severity
from interchange.Records.RecordDiagnostic import Diagnostic

# source geometry and its selected configuration both survive as native objects
KImportTransfers = (
    CapTransfer(Capability.KBrep, TransferMode.KNative),
    CapTransfer(Capability.KConfigurations, TransferMode.KNative),
)

# measured import usability does not imply editable feature history for the generated body
KHistoryLoss = Diagnostic(
    code="sldprt.parametric_history_unavailable",
    message="The native imported solid has no editable parametric history",
    severity=Severity.WARNING,
    attributes=FreezeMapping({"capability": Capability.KParamHistory.value}),
)


# native import publication reports only the proven geometry transfers and actual history loss
def WriteImportMut(
    TargetValue: KTargetType,
    OutputPath: FilePath | None,
    SettingsValue: WriteOptions,
    Payload: bytes,
    Measurement: ImportMeasure,
    Transfers: tuple[CapTransfer, ...],
) -> WriteResult:
    Evidence = FreezeMapping(
        {
            KPartMeasureOpt: FreezeMapping(
                {
                    "generated_sha256": Measurement.CandidateSha,
                    "oracle_build": KOraclePart["build"],
                    "native_result_sha256": Measurement.ResultSha,
                    "rebuild_record_sha256": Measurement.RebuildSha,
                    "reopen_record_sha256": Measurement.ReopenSha,
                }
            ),
        }
    )
    ResultValue = PublishMeasMut(
        TargetValue, OutputPath, SettingsValue, Payload, Evidence, Transfers
    )
    return ReplaceValue(ResultValue, diagnostics=(KHistoryLoss,))
