from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Sweeps.SweepPart import SweepPart
from convert.adapters.solidworks.Core.Writing.Measured.MeasOracle import KOraclePart
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
from convert.adapters.solidworks.Core.Writing.Sweeps.VerifyHeldSweep import VerifyHeldSweep
from convert.adapters.solidworks.Core.Writing.Measured.SnapshotReport import (
    SnapshotReport,
)
from interchange.Core.Common import FreezeMapping

# the disclosed controller measured the two exact native sweep archives
KSwDisclosedReportSha = "fc098693d77e0e41e5652eed80fe705b528db9cb9f6ac527fb379784087d83d0"


# only the exact regenerated sweep and its controlled native history qualify public output
def VerifySweepMeas(
    Receipt: dict[str, object], Candidate: SweepPart, WrittenAt: int
) -> Mapping[str, object]:
    if set(Receipt) == {"native_report"}:
        return VerifyHeldSweep(Receipt, Candidate)
    Proof, ProofSha = SnapshotReport(Receipt)
    Phases = CheckSwBatch(Proof)
    CaseValue = MatchSweepCase(Proof, Candidate, WrittenAt)
    PhaseHashes = CheckSwPhases(Phases, CaseValue)
    CheckSwEdits(CaseValue, Candidate)
    SourceHashes = ReadSwHashes(CaseValue.get("independent_source_sha256"))
    ObserverHashes = ReadSwHashes(CaseValue.get("independent_observer_sha256"))
    if ProofSha != KSwDisclosedReportSha:
        raise ValueError("sweep publication requires authenticated offline evidence")
    return FreezeMapping(
        {
            KPartMeasureOpt: FreezeMapping(
                {
                    "generated_sha256": CaseValue["archive_sha256"],
                    "native_result_sha256": ReadMeasSha(
                        Proof.get("native_result_sha256")
                    ),
                    "oracle_build": KOraclePart["build"],
                    "phase_record_sha256": PhaseHashes,
                    "independent_source_sha256": SourceHashes,
                    "independent_observer_sha256": ObserverHashes,
                }
            )
        }
    )
