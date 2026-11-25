from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha

# exact executable identities bind standalone part measurements to independently verified native builds
KPartOracleBuilds = (
    {
        "build": "34.5.2.0604",
        "product": "SOLIDWORKS 2026 SP05.2",
        "sha256": "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe",
    },
    {
        "build": "34.4.1.1011",
        "product": "SOLIDWORKS 2026 SP04.1",
        "sha256": "200ac2597814daaead89c1de698a45341850fa2fe0d8c094debb316009e7ea7f",
    },
)


# the reported authoring time reconstructs the already measured bytes without deriving intent from the receipt
def ReadPartMeas(OptionsValue: WriteOptions) -> tuple[int, dict[str, object]]:
    SourceValue = OptionsValue.values.get(KPartMeasureOpt)
    if SourceValue is None:
        raise ValueError(
            "SOLIDWORKS part publication requires an offline native measurement receipt"
        )
    Envelope = ReadMeasMap(SourceValue)
    TimeValue = Envelope.get("written_at")
    if (
        set(Envelope) != {"written_at", "receipt"}
        or type(TimeValue) is not int
        or not 0 <= TimeValue <= 0xFFFFFFFF
    ):
        raise ValueError(
            "native measurement requires its exact archive creation epoch and receipt"
        )
    Receipt = ReadMeasMap(Envelope["receipt"])
    if (
        Receipt.get("schema") != "kit.sw2026.sdk-standalone-default-part-evidence.v1"
        or ReadMeasMap(Receipt.get("oracle")) not in KPartOracleBuilds
        or Receipt.get("passed") is not True
        or Receipt.get("controls_healthy") is not True
        or type(Receipt.get("runtime_input_file_reads")) is not int
        or Receipt["runtime_input_file_reads"] != 0
    ):
        raise ValueError(
            "native measurement requires the exact passing SOLIDWORKS 2026 oracle report for a qualified build"
        )
    _ = ReadMeasSha(Receipt.get("native_result_sha256"))
    _ = ReadMeasSha(Receipt.get("packet_sha256"))
    return TimeValue, Receipt
