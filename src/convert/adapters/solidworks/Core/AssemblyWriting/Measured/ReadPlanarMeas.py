from hashlib import sha256 as CalcSha
from json import dumps as DumpJson

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.AssemblyWriting.Measured.CheckAsmPhases import (
    CheckAsmPhases,
)
from convert.adapters.solidworks.Core.AssemblyWriting.Measured.CheckPairRows import (
    CheckPairRows,
)
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from convert.adapters.solidworks.Core.Writing.Measured.ReadPartMeas import KOraclePart

# this approves the canonical disclosed report without using its bytes in the serializer
KPlanarProofSha = "8b2f23136767969ab3eb1e3c7d8eab593092fe8cb333973dd1fd6a88633aa8ee"


# caller measurements must establish the exact known lifecycle before supplying a writer epoch
def ReadPlanarMeas(Settings: WriteOptions) -> tuple[int, dict[str, object]]:
    Value = Settings.values.get(KPartMeasureOpt)
    if Value is None:
        raise ValueError(
            "SOLIDWORKS planar publication requires an offline native measurement receipt"
        )
    Envelope = ReadMeasMap(Value)
    EpochValue = Envelope.get("written_at")
    if (
        Envelope.keys() != {"written_at", "receipt"}
        or type(EpochValue) is not int
        or not 0 <= EpochValue <= 0xFFFFFFFF
    ):
        raise ValueError("planar evidence requires its exact measured epoch")
    Receipt = ReadMeasMap(Envelope["receipt"])
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
    Encoded = DumpJson(
        Envelope,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        ensure_ascii=False,
    ).encode("utf-8")
    if CalcSha(Encoded).hexdigest() != KPlanarProofSha:
        raise ValueError("planar publication requires authenticated offline evidence")
    return EpochValue, Receipt
