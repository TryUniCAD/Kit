from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasInput import (
    ReadMeasInput,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha

# this identity is the exact offline oracle build measured for the standalone part recipe
KOraclePart = {
    "build": "34.5.2.0604",
    "product": "SOLIDWORKS 2026 SP05.2",
    "sha256": "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe",
}


# the reported authoring time reconstructs the already measured bytes without deriving intent from the receipt
def ReadPartMeas(OptionsValue: WriteOptions) -> tuple[int, dict[str, object]]:
    TimeValue, Receipt = ReadMeasInput(OptionsValue)
    if (
        Receipt.get("schema") != "kit.sw2026.sdk-standalone-default-part-evidence.v1"
        or ReadMeasMap(Receipt.get("oracle")) != KOraclePart
        or Receipt.get("passed") is not True
        or Receipt.get("controls_healthy") is not True
        or type(Receipt.get("runtime_input_file_reads")) is not int
        or Receipt["runtime_input_file_reads"] != 0
    ):
        raise ValueError(
            "native measurement requires the exact passing SOLIDWORKS 2026 SP05.2 oracle report"
        )
    _ = ReadMeasSha(Receipt.get("native_result_sha256"))
    _ = ReadMeasSha(Receipt.get("packet_sha256"))
    return TimeValue, Receipt
