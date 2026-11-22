from pathlib import Path as FilePath

from convert.adapters.base.TransferContract import CapTransfer, TransferMode
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Writing.Imports.ImportMeasure import ImportMeasure
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import KPartMeasureOpt
from convert.adapters.solidworks.Core.Writing.Measured.ReadPartMeas import KOraclePart
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumDocument import Capability, Severity
from interchange.Records.RecordDiagnostic import Diagnostic

# source geometry and its selected configuration both survive as native objects
KImportTransfers = (
    CapTransfer(Capability.KBrep, TransferMode.KNative),
    CapTransfer(Capability.KConfigurations, TransferMode.KNative),
)


# the result keeps measured geometry usability distinct from editable feature history
def ImportResult(
    OutputPath: FilePath | None, Measurement: ImportMeasure,
) -> WriteResult:
    return WriteResult(
        OutputPath,
        KPartFormatId,
        Measurement.SizeValue,
        diagnostics=(
            Diagnostic(
                code="sldprt.parametric_history_unavailable",
                message="The native imported solid has no editable parametric history",
                severity=Severity.WARNING,
                attributes=FreezeMapping({"capability": Capability.KParamHistory.value}),
            ),
        ),
        metadata=FreezeMapping({
            KPartMeasureOpt: FreezeMapping({
                "generated_sha256": Measurement.CandidateSha,
                "oracle_build": KOraclePart["build"],
                "native_result_sha256": Measurement.ResultSha,
                "rebuild_record_sha256": Measurement.RebuildSha,
                "reopen_record_sha256": Measurement.ReopenSha,
            }),
        }),
        transfers=KImportTransfers,
        vendor_loadable=True,
        application_usable=True,
    )
