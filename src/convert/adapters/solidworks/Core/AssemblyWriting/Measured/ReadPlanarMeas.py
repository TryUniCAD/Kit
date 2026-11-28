from hashlib import sha256 as CalcSha
from json import dumps as DumpJson, loads as LoadJson

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.AssemblyWriting.Measured.CheckAsmPhases import (
    CheckAsmPhases,
)
from convert.adapters.solidworks.Core.AssemblyWriting.Measured.CheckPairRows import (
    CheckPairRows,
)
from convert.adapters.solidworks.Core.AssemblyWriting.Measured.ReadHeldPerp import (
    KHeldPerpSchema,
    ReadHeldPerp,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasInput import ReadMeasInput
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from convert.adapters.solidworks.Core.Writing.Measured.MeasOracle import KOraclePart

# this approves the canonical disclosed report without using its bytes in the serializer
KPlanarProofSha = "8b2f23136767969ab3eb1e3c7d8eab593092fe8cb333973dd1fd6a88633aa8ee"

# this binds the earlier normal perpendicular pair and its independent control phases
KPerpProofSha = "8288e79ac85a8a9d7d0d080e227745faffe50fb92032947b812aa95bef30b1bf"


# the disclosed flat bundles use the same controlled lifecycle and complete member contract
def CheckPlanarRcpt(Receipt: dict[str, object], EpochValue: int) -> None:
    CheckAsmPhases(Receipt)
    if (
        Receipt.keys()
        != {
            "schema",
            "oracle",
            "passed",
            "controls_healthy",
            "written_at",
            "root",
            "namespace",
            "members",
            "phases",
            "packet_sha256",
            "fixture_sha256",
            "native_result_sha256",
        }
        or Receipt.get("schema") != "kit.sw2026.planar-assembly-measurement.v1"
        or ReadMeasMap(Receipt.get("oracle")) != KOraclePart
        or Receipt.get("passed") is not True
        or Receipt.get("controls_healthy") is not True
        or Receipt.get("written_at") != EpochValue
    ):
        raise ValueError("planar evidence requires the passing exact-build lifecycle")
    CheckPairRows(Receipt)
    for FieldName in ("packet_sha256", "fixture_sha256", "native_result_sha256"):
        _ = ReadMeasSha(Receipt.get(FieldName))


# caller measurements establish a scoped native lifecycle and never provide archive values
def ReadPlanarMeas(
    Settings: WriteOptions, *, Perpendicular: bool = False
) -> tuple[int, dict[str, object]]:
    EpochValue, SourceValue, _ = ReadMeasInput(Settings)
    if Perpendicular and SourceValue.get("schema") == KHeldPerpSchema:
        return EpochValue, ReadHeldPerp(SourceValue)
    Encoded = DumpJson(
        {"written_at": EpochValue, "receipt": SourceValue},
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        ensure_ascii=False,
    ).encode("utf-8")
    Expected = KPerpProofSha if Perpendicular else KPlanarProofSha
    if CalcSha(Encoded).hexdigest() != Expected:
        raise ValueError("planar publication requires authenticated offline evidence")
    Receipt = ReadMeasMap(ReadMeasMap(LoadJson(Encoded))["receipt"])
    CheckPlanarRcpt(Receipt, EpochValue)
    return EpochValue, Receipt
