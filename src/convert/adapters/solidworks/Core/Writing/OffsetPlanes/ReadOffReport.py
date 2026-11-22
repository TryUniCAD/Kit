from hashlib import sha256 as CalcSha
from json import loads as LoadJson

from convert.adapters.solidworks.Core.Writing.Measured.MeasOracle import KOraclePart
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha

# the disclosed authority pins the measured front top and right outputs
KOffDisclosed = "69d26121c617641841dd29bd43867f082ae59d32a68cf5ace03903e11781cd3a"

# the original authority pins the guest held out outputs and their windows control
KOffOriginal = "79210ac088a95b3c6d0913b8a056e678e8dbe14e9a861f178455ea0426f6e80c"


# original locked receipts bind the actual native build and paired lifecycles of their accepted outputs
def OriginalHashes(ReportValue: dict[str, object]) -> frozenset[str]:
    Oracle = ReadMeasMap(ReportValue.get("oracle"))
    if (
        ReportValue.get("schema")
        != "kit.sw2026.offset-plane-original-native-acceptance.v1"
        or ReportValue.get("native_acceptance") is not True
        or Oracle.get("build") != KOraclePart["build"]
        or Oracle.get("exe_sha256") != KOraclePart["sha256"]
    ):
        raise ValueError("offset measurement requires exact original native acceptance")
    Original = ReadMeasRows(ReportValue.get("originals"), Limit=2)
    Windows = ReadMeasMap(ReportValue.get("windows_disclosed_qualification"))
    if len(Original) != 2 or not all(
        RowValue.get("passed") is True for RowValue in (*Original, Windows)
    ):
        raise ValueError(
            "offset measurement requires complete passing native lifecycles"
        )
    return frozenset(
        ReadMeasSha(RowValue.get("generated_sha256"))
        for RowValue in (*Original, Windows)
    )


# a disclosed measurement is usable only after its exact authored files have passed the same rebuild and edit lifecycle
def DisclosedHashes(ReportValue: dict[str, object]) -> frozenset[str]:
    if (
        ReportValue.get("schema")
        != "kit.sw2026.original-offset-plane-method-preparation-receipt.v1"
        or ReportValue.get("disclosed_native_processes") != 12
        or ReportValue.get("disclosed_numeric_comparisons") != 243
    ):
        raise ValueError(
            "offset measurement requires the exact disclosed native cohort"
        )
    RowsValue = ReadMeasRows(ReportValue.get("disclosed_native_cases"), Limit=3)
    if len(RowsValue) != 3 or not all(
        RowValue.get("new_guarded_output_reproduced") is True
        and RowValue.get("numeric_checks") == 81
        for RowValue in RowsValue
    ):
        raise ValueError("offset measurement requires all three disclosed native cases")
    return frozenset(
        ReadMeasSha(RowValue.get("generated_sha256")) for RowValue in RowsValue
    )


# evidence authorizes whole regenerated outputs without supplying archive fields
def ReadOffReport(
    Receipt: dict[str, object],
) -> tuple[str, frozenset[str]]:
    TextValue = Receipt.get("native_report")
    if (
        set(Receipt) != {"native_report"}
        or type(TextValue) is not str
        or len(TextValue) > 64_000
    ):
        raise ValueError("offset publication requires its exact native report text")
    Payload = TextValue.encode("utf-8")
    ReportHash = CalcSha(Payload).hexdigest()
    if ReportHash not in (KOffDisclosed, KOffOriginal):
        raise ValueError("offset publication requires authenticated offline evidence")
    ReportValue = ReadMeasMap(LoadJson(Payload))
    if ReportHash == KOffOriginal:
        return ReportHash, OriginalHashes(ReportValue)
    return ReportHash, DisclosedHashes(ReportValue)
