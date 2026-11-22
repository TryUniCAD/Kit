from hashlib import sha256 as CalcSha
from json import loads as JsonLoads

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Writing.Measured.PatNativePins import (
    KPatternPacket,
    KPatternResult,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadPartMeas import (
    KOraclePart,
    ReadMeasInput,
)


# verification reads only caller supplied evidence and the complete digests of the disclosed native batch
def ReadPinnedJson(Value: object, Expected: str) -> dict[str, object]:
    if type(Value) is str:
        Value = Value.encode("utf-8")
    if type(Value) is not bytes or CalcSha(Value).hexdigest() != Expected:
        raise ValueError(
            "linear pattern requires its exact disclosed native measurement"
        )
    return ReadMeasMap(JsonLoads(Value))


# admit the measured packet and native result as independent evidence after verifying their shared authority
def ReadPatMeas(
    OptionsValue: WriteOptions,
) -> tuple[int, dict[str, object], dict[str, object]]:
    TimeValue, Receipt = ReadMeasInput(OptionsValue)
    if set(Receipt) != {"packet", "result"}:
        raise ValueError(
            "linear pattern receipt requires its exact native packet and result"
        )
    Packet = ReadPinnedJson(Receipt["packet"], KPatternPacket)
    Result = ReadPinnedJson(Receipt["result"], KPatternResult)
    FilesValue = ReadMeasMap(Packet.get("files"))
    if (
        Packet.get("schema") != "kit.sw2026.generated-raised-pattern-native.v1"
        or Result.get("schema")
        != "kit.sw2026.generated-raised-pattern-native-result.v1"
        or Packet.get("native_build") != KOraclePart["build"]
        or Result.get("build") != KOraclePart["build"]
        or Packet.get("oracle_sha256") != KOraclePart["sha256"]
        or Result.get("oracle_sha256") != KOraclePart["sha256"]
        or Result.get("packet_sha256") != KPatternPacket
        or Result.get("build_sha256") != FilesValue.get("Build.json")
        or Result.get("passed") is not True
        or Result.get("distinct_processes") != 6
    ):
        raise ValueError("linear pattern native measurement authority differs")
    return TimeValue, FilesValue, Result
