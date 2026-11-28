from hashlib import sha256 as CalcSha
from json import dumps as JsonDumps

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasInput import (
    ReadMeasInput,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from convert.adapters.solidworks.Core.Writing.Stocks.CheckStockLife import (
    CheckStockLife,
)
from convert.adapters.solidworks.Core.Writing.Stocks.StockMeasure import (
    StockMeasure,
)

# stock evidence must match the original measured oracle
KStockOracle = {
    "build": "34.5.2.0604",
    "product": "SOLIDWORKS 2026 SP05.2",
    "sha256": "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe",
}

# the exact disclosed receipt grants publication only to its independently measured output
KStockReceiptSha = "d672ec1f8d427844410a7e2d809bfbcf0d130ecaf1df1bb78cefdd1f5f64e187"

# the recorded creation event participates in the whole generated archive fingerprint
KStockEpoch = 1765500071

# the measured native use binds the observed physical and encoded standalone locator
KStockLocator = r"C:\KitSdkCandidates\GeneratedTwoStockGraph01.SLDPRT"


# caller supplied json must match independently verified evidence before it authorizes a write
def ReadStockMeas(OptionsValue: WriteOptions) -> StockMeasure:
    EpochValue, Receipt = ReadMeasInput(OptionsValue)
    try:
        Canonical = (
            JsonDumps(Receipt, indent=2, sort_keys=True, allow_nan=False) + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as ErrorValue:
        raise ValueError(
            "stock measurement needs bounded JSON evidence"
        ) from ErrorValue
    if EpochValue != KStockEpoch or CalcSha(Canonical).hexdigest() != KStockReceiptSha:
        raise ValueError(
            "selected stock output requires its exact controlled native receipt"
        )
    Summary = ReadMeasMap(Receipt.get("summary"))
    if (
        Receipt.get("schema") != "kit.sw2026.disclosed-two-stock-native-observation.v1"
        or Summary.get("oracle_build") != KStockOracle["build"]
        or Summary.get("oracle_sha256") != KStockOracle["sha256"]
        or Summary.get("controls_passed") is not True
        or Summary.get("generated_native_lifecycle_passed") is not True
    ):
        raise ValueError(
            "stock measurement requires its exact build and native lifecycle"
        )
    PlanValue = ReadMeasMap(Receipt.get("plan"))
    SizeValue = PlanValue.get("candidate_bytes")
    CandidateSha = ReadMeasSha(Summary.get("candidate_sha256"))
    if (
        type(SizeValue) is not int
        or SizeValue <= 0
        or PlanValue.get("candidate_sha256") != CandidateSha
        or PlanValue.get("generation_runtime_access_attempts") != 0
    ):
        raise ValueError(
            "stock measurement does not bind the complete generated archive"
        )
    EditSha, ReopenSha = CheckStockLife(Receipt, Summary)
    return StockMeasure(
        EpochValue,
        KStockLocator,
        SizeValue,
        CandidateSha,
        ReadMeasSha(Receipt.get("guest_summary_sha256")),
        EditSha,
        ReopenSha,
    )
