from collections.abc import Mapping
from hashlib import sha256 as CalcSha

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.Writing.Circle.CheckCircTrail import (
    CheckCircTrail,
)
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from convert.adapters.solidworks.Core.Writing.Measured.ReadPartMeas import KOraclePart
from interchange.Core.Common import FreezeMapping


# measurement must bind all stream facts as well as the complete output archive
def CheckCircFiles(CaseValue: dict[str, object], Streams: Mapping[str, bytes]) -> None:
    RowsValue = ReadMeasMap(CaseValue.get("streams"))
    if set(RowsValue) != set(Streams):
        raise ValueError("circle measurement does not cover all generated streams")
    for NameValue, Payload in Streams.items():
        RowValue = ReadMeasMap(RowsValue[NameValue])
        if (
            RowValue.get("byte_identity") is not True
            or RowValue.get("bytes") != len(Payload)
            or ReadMeasSha(RowValue.get("sha256")) != CalcSha(Payload).hexdigest()
        ):
            raise ValueError("circle report has a different typed stream")


# only the exact regenerated measured circle candidate can acquire publication status
def MatchCircMeas(
    Receipt: dict[str, object], Candidate: PartCandidate
) -> Mapping[str, object]:
    PlanValue = Candidate.PlanValue
    if not isinstance(PlanValue, CirclePlan):
        raise ValueError("circle measurement requires the actual circle preparation")
    Digest = CalcSha(Candidate.BytesValue).hexdigest()
    RowsValue = tuple(
        RowValue
        for RowValue in ReadMeasRows(Receipt.get("cases"), 32)
        if RowValue.get("candidate_sha256") == Digest
    )
    if len(RowsValue) != 1:
        raise ValueError("regenerated circle has no unique exact native measurement")
    (CaseValue,) = RowsValue
    if CaseValue.get("name") != PlanValue.NameValue or CaseValue.get("mode") != (
        "diameter" if PlanValue.IsDiameter else "radius"
    ):
        raise ValueError("circle report describes a different named driver or model")
    CheckCircFiles(CaseValue, Candidate.StreamsValue)
    Edited, Reopen = CheckCircTrail(CaseValue, Digest, PlanValue)
    return FreezeMapping(
        {
            KPartMeasureOpt: FreezeMapping(
                {
                    "generated_sha256": Digest,
                    "oracle_build": KOraclePart["build"],
                    "native_result_sha256": ReadMeasSha(
                        Receipt.get("raw_result_sha256")
                    ),
                    "edit_record_sha256": Edited,
                    "reopen_record_sha256": Reopen,
                }
            )
        }
    )
