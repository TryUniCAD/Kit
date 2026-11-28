from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.base.SourceEvidenceKey import KSourceEvidence
from interchange.serialization.EncodeData import ToData
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)


# conversion evidence needs a stable public representation without claiming target application acceptance
def WriteReport(Result: WriteResult) -> dict[str, object]:
    Evidence = Result.MetadataMap.get(KSourceEvidence)
    return {
        **({"source_evidence": ToData(Evidence)} if Evidence is not None else {}),
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
        "acceptance": (
            "Exact output matches the caller supplied offline SOLIDWORKS native measurement"
            if KPartMeasureOpt in Result.metadata
            and Result.IsVendorLoadable
            and Result.IsAppUsable
            else "Writer evidence only; target application open, edit, and rebuild remain unverified"
        ),
    }
