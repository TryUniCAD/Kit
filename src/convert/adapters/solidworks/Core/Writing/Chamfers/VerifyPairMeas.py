from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.Writing.Chamfers.MatchPairCase import (
    MatchPairCase,
)
from convert.adapters.solidworks.Core.Writing.Chamfers.ReadPairBatch import (
    ReadPairBatch,
)
from convert.adapters.solidworks.Core.Writing.Measured.MeasOracle import KOraclePart
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from interchange.Core.Common import FreezeMapping


# when exact bytes and their native lifecycle agree the write can report measured acceptance
def VerifyPairMeas(
    Receipt: dict[str, object], Candidate: PartCandidate, WrittenAt: int
) -> Mapping[str, object]:
    Batch = ReadPairBatch(Receipt, WrittenAt)
    SlotValue = MatchPairCase(Batch, Candidate, WrittenAt)
    return FreezeMapping(
        {
            KPartMeasureOpt: FreezeMapping(
                {
                    "generated_sha256": Batch.Generated[SlotValue]["archive_sha256"],
                    "generation_sha256": Batch.GenerationHash,
                    "native_result_sha256": Batch.NativeHash,
                    "oracle_build": KOraclePart["build"],
                    "phase_record_sha256": Batch.PhaseHashes[SlotValue],
                }
            )
        }
    )
