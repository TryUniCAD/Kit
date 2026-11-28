from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Sweeps.SweepPart import SweepPart
from convert.adapters.solidworks.Core.Writing.Measured.ReadPartMeas import (
    KOracleSpFive,
)
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from convert.adapters.solidworks.Core.Writing.Sweeps.CheckSwBatch import CheckSwBatch
from convert.adapters.solidworks.Core.Writing.Sweeps.CheckSwEdits import CheckSwEdits
from convert.adapters.solidworks.Core.Writing.Sweeps.CheckSwPhases import CheckSwPhases
from convert.adapters.solidworks.Core.Writing.Sweeps.MatchSweepCase import (
    MatchSweepCase,
)
from convert.adapters.solidworks.Core.Writing.Sweeps.ReadSwHashes import ReadSwHashes
from interchange.Core.Common import FreezeMapping


# only the exact regenerated sweep and its controlled native history qualify public output
def VerifySweepMeas(
    Receipt: dict[str, object], Candidate: SweepPart, WrittenAt: int
) -> Mapping[str, object]:
    Phases = CheckSwBatch(Receipt)
    CaseValue = MatchSweepCase(Receipt, Candidate, WrittenAt)
    PhaseHashes = CheckSwPhases(Phases, CaseValue)
    CheckSwEdits(CaseValue, Candidate)
    return FreezeMapping(
        {
            KPartMeasureOpt: FreezeMapping(
                {
                    "generated_sha256": CaseValue["archive_sha256"],
                    "native_result_sha256": ReadMeasSha(
                        Receipt.get("native_result_sha256")
                    ),
                    "oracle_build": KOracleSpFive["build"],
                    "phase_record_sha256": PhaseHashes,
                    "independent_source_sha256": ReadSwHashes(
                        CaseValue.get("independent_source_sha256")
                    ),
                    "independent_observer_sha256": ReadSwHashes(
                        CaseValue.get("independent_observer_sha256")
                    ),
                }
            )
        }
    )
