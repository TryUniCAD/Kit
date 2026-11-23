from collections.abc import Mapping
from hashlib import sha256 as CalcSha

from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.Writing.Chamfers.ReadHeldPair import (
    KHeldPairReportSha,
)
from convert.adapters.solidworks.Core.Writing.Measured.MeasOracle import KOraclePart
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from interchange.Core.Common import FreezeMapping


# only the full archive identity qualifies the protected candidate and its embedded locator
def MatchHeldPair(
    Proof: dict[str, object], Candidate: PartCandidate
) -> Mapping[str, object]:
    Digest = CalcSha(Candidate.BytesValue).hexdigest()
    Slots = ReadMeasRows(Proof.get("candidates"), 2)
    Matches = tuple(
        SlotValue for SlotValue in Slots if SlotValue.get("candidate_sha256") == Digest
    )
    if len(Matches) != 1:
        raise ValueError("distance chamfer has no unique exact held-out native measurement")
    Phases = ReadMeasRows(Matches[0].get("phases"), 2)
    return FreezeMapping(
        {
            KPartMeasureOpt: FreezeMapping(
                {
                    "generated_sha256": Digest,
                    "generation_sha256": ReadMeasSha(Proof.get("generation_sha256")),
                    "native_result_sha256": ReadMeasSha(Proof.get("private_result_sha256")),
                    "oracle_build": KOraclePart["build"],
                    "authority_sha256": KHeldPairReportSha,
                    "phase_record_sha256": tuple(
                        ReadMeasSha(Phase.get("record_sha256")) for Phase in Phases
                    ),
                }
            )
        }
    )
