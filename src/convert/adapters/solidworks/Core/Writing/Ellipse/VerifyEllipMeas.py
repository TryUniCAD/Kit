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
from convert.adapters.solidworks.Core.Writing.Measured.ReadPartMeas import KOraclePart
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from interchange.Core.Common import FreezeMapping


# result evidence exists only for the exact compiled candidate and its complete native lifecycle
def VerifyEllipMeas(
    Receipt: dict[str, object], Candidate: EllipsePart, WrittenAt: int
) -> Mapping[str, object]:
    Phases = CheckEllipBatch(Receipt)
    CaseValue = MatchEllipCase(Receipt, Candidate, WrittenAt)
    EditHash, ReopenHash = CheckEllipSlot(Phases, CaseValue, Candidate.PlanValue)
    return FreezeMapping(
        {
            KPartMeasureOpt: FreezeMapping(
                {
                    "generated_sha256": CaseValue["archive_sha256"],
                    "native_result_sha256": ReadMeasSha(
                        Receipt.get("native_result_sha256")
                    ),
                    "oracle_build": KOraclePart["build"],
                    "edit_record_sha256": EditHash,
                    "reopen_record_sha256": ReopenHash,
                }
            )
        }
    )
