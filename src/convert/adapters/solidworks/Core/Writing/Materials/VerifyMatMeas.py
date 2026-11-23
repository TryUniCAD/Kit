from collections.abc import Mapping
from hashlib import sha256 as CalcSha
from json import loads as LoadJson

from convert.adapters.solidworks.Core.Writing.Measured.MeasOracle import KOraclePart
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from interchange.Core.Common import FreezeMapping

# the report digest binds the original held out lifecycles without contributing archive fields
KPhysicalMatReportSha = (
    "aad91110c0f3237576c813e2c61a0d7301b7ab0295275c637ee0d7979f770f55"
)


# a regenerated archive qualifies only at the complete digest accepted by the controlled native lifecycle
def VerifyMatMeas(Receipt: dict[str, object], Payload: bytes) -> Mapping[str, object]:
    TextValue = Receipt.get("native_report")
    if (
        set(Receipt) != {"native_report"}
        or type(TextValue) is not str
        or len(TextValue) > 20_000
        or CalcSha(TextValue.encode("utf-8")).hexdigest() != KPhysicalMatReportSha
    ):
        raise ValueError("assigned material requires authenticated native measurement")
    Report = ReadMeasMap(LoadJson(TextValue))
    Controls = ReadMeasMap(Report.get("controls"))
    if (
        Report.get("schema") != "kit.sw2026.assigned-material-physical-authority.v1"
        or Report.get("oracle_build") != KOraclePart["build"]
        or Report.get("oracle_sha256") != KOraclePart["sha256"]
        or Report.get("native_processes") != 6
        or Report.get("native_states") != 12
        or Report.get("native_numeric_checks") != 120
        or set(Controls) != {"before", "after"}
    ):
        raise ValueError("assigned material measurement lacks its controlled lifecycle")
    for DigestValue in Controls.values():
        _ = ReadMeasSha(DigestValue)
    Digest = CalcSha(Payload).hexdigest()
    Matches = tuple(
        RowValue
        for RowValue in ReadMeasRows(Report.get("cases"), 2)
        if ReadMeasSha(RowValue.get("archive_sha256")) == Digest
    )
    if len(Matches) != 1:
        raise ValueError(
            "regenerated assigned-material part has no exact native measurement"
        )
    (CaseValue,) = Matches
    if CaseValue.get("native_states") != 6 or CaseValue.get("numeric_checks") != 60:
        raise ValueError(
            "assigned material measurement lacks the independent comparisons"
        )
    return FreezeMapping(
        {
            KPartMeasureOpt: FreezeMapping(
                {
                    "generated_sha256": Digest,
                    "native_result_sha256": ReadMeasSha(
                        Report.get("native_result_sha256")
                    ),
                    "native_edit_sha256": ReadMeasSha(
                        CaseValue.get("native_edit_sha256")
                    ),
                    "native_reopen_sha256": ReadMeasSha(
                        CaseValue.get("native_reopen_sha256")
                    ),
                    "native_build": KOraclePart["build"],
                    "scope": "origin-owned-physical-material",
                }
            )
        }
    )
