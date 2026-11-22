from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Writing.Circle.CheckCircBatch import (
    CheckCircBatch,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasInput import (
    ReadMeasInput,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from convert.adapters.solidworks.Core.Writing.Measured.ReadPartMeas import KOraclePart


# the disclosed circular lifecycle has its own measured report contract
def ReadCircMeas(OptionsValue: WriteOptions) -> tuple[int, dict[str, object]]:
    WrittenAt, Receipt = ReadMeasInput(OptionsValue)
    OracleValue = ReadMeasMap(Receipt.get("oracle"))
    if (
        Receipt.get("schema") != "kit.sw2026.sdk-circle-native-disclosed.v1"
        or set(OracleValue) != {"version", "exe_sha256"}
        or OracleValue["version"] != KOraclePart["build"]
        or OracleValue["exe_sha256"] != KOraclePart["sha256"]
        or Receipt.get("passed") is not True
        or Receipt.get("disclosed_lifecycle_passed") is not True
        or Receipt.get("initial_bodies_before_explicit_rebuild") is not True
        or type(Receipt.get("runtime_input_file_reads")) is not int
        or Receipt["runtime_input_file_reads"] != 0
    ):
        raise ValueError(
            "circle measurement requires its passing native batch and oracle"
        )
    _ = ReadMeasSha(Receipt.get("raw_result_sha256"))
    _ = ReadMeasSha(Receipt.get("packet_sha256"))
    _ = ReadMeasSha(Receipt.get("postflight_sha256"))
    CheckCircBatch(Receipt)
    return WrittenAt, Receipt
