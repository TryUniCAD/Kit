from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Ellipse.EllipsePart import (
    EllipsePart,
)
from convert.adapters.solidworks.Core.Writing.Ellipse.CheckEllipBatch import (
    CheckEllipBatch,
)
from convert.adapters.solidworks.Core.Writing.Ellipse.CheckEllipSlot import (
    CheckEllipSlot,
)
from convert.adapters.solidworks.Core.Writing.Ellipse.MatchEllipCase import (
    MatchEllipCase,
)
from convert.adapters.solidworks.Core.Writing.Measured.MeasOracle import KOraclePart
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from convert.adapters.solidworks.Core.Writing.Measured.SnapshotReport import (
    SnapshotReport,
)
from interchange.Core.Common import FreezeMapping

# this authenticates the disclosed normalized receipt and never contributes construction values
KEllipReportSha = "e590ced10e6286c0637ea9b1bf9b8f44d041ef1b9aab454d61af0d99ec2066e3"


# result evidence exists only for the exact compiled candidate and its complete native lifecycle
def VerifyEllipMeas(
    Receipt: dict[str, object],
    Candidate: EllipsePart,
    WrittenAt: int,
) -> Mapping[str, object]:
    Proof, ProofSha = SnapshotReport(Receipt)
    Phases = CheckEllipBatch(Proof)
    CaseValue = MatchEllipCase(Proof, Candidate, WrittenAt)
    EditHash, ReopenHash = CheckEllipSlot(
        Phases, CaseValue, Candidate.PlanValue.DepthValue
    )
    if ProofSha != KEllipReportSha:
        raise ValueError("ellipse publication requires authenticated offline evidence")
    return FreezeMapping(
        {
            KPartMeasureOpt: FreezeMapping(
                {
                    "generated_sha256": CaseValue["archive_sha256"],
                    "native_result_sha256": ReadMeasSha(
                        Proof.get("native_result_sha256")
                    ),
                    "oracle_build": KOraclePart["build"],
                    "edit_record_sha256": EditHash,
                    "reopen_record_sha256": ReopenHash,
                    "authority_sha256": ProofSha,
                }
            )
        }
    )
