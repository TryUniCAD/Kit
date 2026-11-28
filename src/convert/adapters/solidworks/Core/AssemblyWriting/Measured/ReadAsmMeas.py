from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.AssemblyWriting.Measured.CheckAsmPhases import (
    CheckAsmPhases,
)
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from convert.adapters.solidworks.Core.Writing.Measured.ReadPartMeas import KOraclePart


# the assembly receipt has its own bundle lifecycle and supplies the exact measured creation epoch
def ReadAsmMeas(OptionsValue: WriteOptions) -> tuple[int, dict[str, object]]:
    SourceValue = OptionsValue.values.get(KPartMeasureOpt)
    if SourceValue is None:
        raise ValueError(
            "SOLIDWORKS assembly publication requires an offline native measurement receipt"
        )
    Envelope = ReadMeasMap(SourceValue)
    WrittenAt = Envelope.get("written_at")
    if (
        set(Envelope) != {"written_at", "receipt"}
        or type(WrittenAt) is not int
        or not 0 <= WrittenAt <= 0xFFFFFFFF
    ):
        raise ValueError(
            "native assembly measurement requires its exact creation epoch"
        )
    Receipt = ReadMeasMap(Envelope["receipt"])
    if (
        Receipt.get("schema") != "kit.sw2026.rigid-nested-measurement.v1"
        or ReadMeasMap(Receipt.get("oracle")) != KOraclePart
        or Receipt.get("passed") is not True
        or Receipt.get("controls_healthy") is not True
        or type(Receipt.get("written_at")) is not int
        or Receipt["written_at"] != WrittenAt
    ):
        raise ValueError(
            "native assembly measurement requires the matching passing SOLIDWORKS 2026 SP05.2 report"
        )
    for NameValue in ("packet_sha256", "fixture_sha256", "native_result_sha256"):
        _ = ReadMeasSha(Receipt.get(NameValue))
    CheckAsmPhases(Receipt)
    return WrittenAt, Receipt
