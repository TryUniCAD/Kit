from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.Fusion.Measurement.FusionMeasOpt import KFusionMeasOpt
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)


# conversion evidence needs a stable public representation without claiming target application acceptance
def WriteReport(Result: WriteResult) -> dict[str, object]:
    return {
        "path": str(Result.OutputPath) if Result.OutputPath is not None else None,
        "bytes_written": Result.ByteCount,
        "application_usable": Result.IsAppUsable,
        "vendor_loadable": Result.IsVendorLoadable,
        "dropped": sorted(Value.value for Value in Result.DroppedCaps),
        "requirements": Result.Requirements,
        "transfers": [
            {
                "capability": Value.CapabilityData.value,
                "mode": Value.TransferModeData.value,
                "carrier_reason": (
                    Value.CarrierCause.value if Value.CarrierCause is not None else None
                ),
            }
            for Value in Result.Transfers
        ],
        "diagnostics": [
            {
                "code": Value.ErrorCode,
                "message": Value.MessageText,
                "severity": Value.Level.value,
                "entity_id": Value.EntityId,
            }
            for Value in Result.Diagnostics
        ],
        "acceptance": GetAcceptance(Result),
    }


# report the oracle only after the writer binds its receipt to the entire output
def GetAcceptance(Result: WriteResult) -> str:
    if Result.IsVendorLoadable and Result.IsAppUsable:
        if KPartMeasureOpt in Result.metadata:
            return "Exact output matches the caller supplied offline SOLIDWORKS native measurement"
        if KFusionMeasOpt in Result.metadata:
            return "Exact output matches the caller supplied offline Fusion native measurement"
    return "Writer evidence only; target application open, edit, and rebuild remain unverified"
