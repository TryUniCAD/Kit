from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.Writing.Chamfers.MatchAngleCase import (
    MatchAngleCase,
)
from convert.adapters.solidworks.Core.Writing.Chamfers.ReadAngleBatch import (
    KAngleNativeSha,
    KAngleTrialSha,
    ReadAngleBatch,
)
from convert.adapters.solidworks.Core.Writing.Measured.MeasOracle import KOraclePart
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from interchange.Core.Common import FreezeMapping


# publication evidence binds the actual whole archive to its successful edit and reopen
def VerifyAngleMeas(
    Receipt: dict[str, object], Candidate: PartCandidate, WrittenAt: int
) -> Mapping[str, object]:
    Trial, Native = ReadAngleBatch(Receipt)
    SlotValue, Digest = MatchAngleCase(Trial, Candidate, WrittenAt)
    Phases = tuple(
        Phase
        for Phase in ReadMeasRows(Native.get("phases"), 6)
        if Phase.get("slot") == SlotValue
    )
    if tuple(Phase.get("role") for Phase in Phases) != ("edit", "reopen") or any(
        Phase.get("phase_passed") is not True for Phase in Phases
    ):
        raise ValueError("angle-distance chamfer lacks its measured native phases")
    return FreezeMapping(
        {
            KPartMeasureOpt: FreezeMapping(
                {
                    "generated_sha256": Digest,
                    "generation_sha256": KAngleTrialSha,
                    "native_result_sha256": KAngleNativeSha,
                    "oracle_build": KOraclePart["build"],
                    "phase_record_sha256": tuple(
                        ReadMeasSha(Phase.get("receipt_sha256")) for Phase in Phases
                    ),
                }
            )
        }
    )
