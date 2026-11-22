from hashlib import sha256 as CalcSha
from json import dumps as JsonDumps, loads as JsonLoads

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Writing.Imports.ImportMeasure import ImportMeasure
from convert.adapters.solidworks.Core.Writing.Imports.ReadImportCase import (
    ReadImportCase,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasInput import (
    ReadMeasInput,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from convert.adapters.solidworks.Core.Writing.Measured.ReadPartMeas import KOraclePart

# only this disclosed native report already measures the exact standalone archives
KImportReceiptSha = "40d77a01a37e8d85517fbfa642a208bdcd3b29378d426021b643cbd909e1a6c4"

# each geometry profile has its own native lifecycle comparison
KImportCases = (("RectangularBare", 116), ("ConcaveOwned", 164))


# native eligibility is computed from the identical bytes authenticated for each case
def ReadImportMeas(
    SettingsValue: WriteOptions,
) -> tuple[int, tuple[ImportMeasure, ...], WriteOptions]:
    EpochValue, Receipt, NativeSettings = ReadMeasInput(SettingsValue)
    try:
        Evidence = (
            JsonDumps(Receipt, indent=2, sort_keys=True, allow_nan=False) + "\n"
        ).encode()
    except (TypeError, ValueError, RecursionError) as ErrorValue:
        raise ValueError(
            "local solid needs bounded JSON measurement evidence"
        ) from ErrorValue
    if CalcSha(Evidence).hexdigest() != KImportReceiptSha:
        raise ValueError(
            "local solid output requires its exact controlled native receipt"
        )
    Receipt = ReadMeasMap(JsonLoads(Evidence))
    if (
        Receipt.get("schema")
        != "kit.sw2026.generated-imported-local-parts-completed.v1"
        or Receipt.get("oracle_file_version") != KOraclePart["build"]
        or Receipt.get("oracle_sha256") != KOraclePart["sha256"]
        or Receipt.get("controls_healthy") is not True
        or Receipt.get("fresh_native_processes") != 11
        or Receipt.get("runtime_input_file_reads") != 0
    ):
        raise ValueError(
            "local solid output requires its exact controlled native receipt"
        )
    Controls = ReadMeasMap(Receipt.get("controls"))
    if ReadMeasSha(Controls.get("ControlBefore")) == ReadMeasSha(
        Controls.get("ControlAfter")
    ):
        raise ValueError("local solid measurement needs separate controls")
    CasesValue = ReadMeasMap(Receipt.get("cases"))
    ResultSha = ReadMeasSha(Receipt.get("native_raw_sha256"))
    Measurements = tuple(
        ReadImportCase(
            ReadMeasMap(CasesValue.get(RoleValue)),
            ResultSha,
            NumericChecks,
        )
        for RoleValue, NumericChecks in KImportCases
    )
    return EpochValue, Measurements, NativeSettings
