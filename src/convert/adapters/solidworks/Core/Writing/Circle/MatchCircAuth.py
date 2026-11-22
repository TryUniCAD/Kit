from collections.abc import Mapping
from hashlib import sha256 as CalcSha

from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from convert.adapters.solidworks.Core.Writing.Measured.ReadPartMeas import KOraclePart
from interchange.Core.Common import FreezeMapping


# each authenticated source report names its one measured generated candidate
def ReadCircCase(
    Schema: str, Report: dict[str, object], NameValue: str
) -> tuple[str, str]:
    Cases = tuple(
        RowValue
        for RowValue in ReadMeasRows(Report.get("cases"), 4)
        if RowValue.get("name") == NameValue
    )
    if len(Cases) != 1:
        raise ValueError("circle measurement requires one exact named native case")
    (CaseValue,) = Cases
    if Schema == "kit.sw2026.sdk-circle-native-disclosed.v1":
        Candidate = CaseValue.get("candidate_sha256")
        ResultValue = Report.get("raw_result_sha256")
    elif Schema == "kit.sw2026.sdk-circle-ends-disclosed.v1":
        Candidate = CaseValue.get("artifact_sha256")
        ResultValue = Report.get("native_result_sha256")
    elif Schema == "kit.sw2026.sdk-circle-original-native-receipt.v1":
        Generated = ReadMeasMap(ReadMeasMap(CaseValue.get("lanes")).get("generated"))
        Candidate = Generated.get("input_sha256")
        ResultValue = ReadMeasMap(Report.get("native")).get("result_sha256")
    elif Schema == "kit.sw2026.sdk-paired-end-conditions-native.v1":
        Candidate = ReadMeasMap(Report.get("generated")).get(NameValue)
        ResultValue = Report.get("native_result_sha256")
    else:
        raise ValueError("unknown authenticated circle measurement schema")
    return ReadMeasSha(Candidate), ReadMeasSha(ResultValue)


# match the complete generated archive to the exact measured case before attesting output
def MatchCircAuth(
    Schema: str,
    ReportSha: str,
    Report: dict[str, object],
    NameValue: str,
    Payload: bytes,
) -> Mapping[str, object]:
    Expected, ResultSha = ReadCircCase(Schema, Report, NameValue)
    Digest = CalcSha(Payload).hexdigest()
    if Expected != Digest:
        raise ValueError("regenerated circle has no matching exact native measurement")
    return FreezeMapping(
        {
            KPartMeasureOpt: FreezeMapping(
                {
                    "generated_sha256": Digest,
                    "oracle_build": KOraclePart["build"],
                    "native_result_sha256": ResultSha,
                    "authority_sha256": ReportSha,
                }
            )
        }
    )
