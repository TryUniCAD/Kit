from collections.abc import Mapping
from hashlib import sha256 as CalcSha
from json import dumps as DumpJson

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
from interchange.Core.Common import FreezeMapping

# this authenticates the disclosed normalized receipt and never contributes construction values
KEllipReportSha = "e590ced10e6286c0637ea9b1bf9b8f44d041ef1b9aab454d61af0d99ec2066e3"


# canonical serialization matches the exact verified disclosed offline authority
def CheckEllipAuth(Receipt: dict[str, object]) -> None:
    Canonical = DumpJson(Receipt, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if CalcSha(Canonical.encode()).hexdigest() != KEllipReportSha:
        raise ValueError("ellipse readback requires authenticated offline evidence")


# result evidence exists only for the exact compiled candidate and its complete native lifecycle
def VerifyEllipMeas(
    Receipt: dict[str, object],
    Candidate: EllipsePart,
    WrittenAt: int,
    *,
    RequireAuth: bool = False,
) -> Mapping[str, object]:
    Phases = CheckEllipBatch(Receipt)
    CaseValue = MatchEllipCase(Receipt, Candidate, WrittenAt)
    EditHash, ReopenHash = CheckEllipSlot(
        Phases, CaseValue, Candidate.PlanValue.DepthValue
    )
    if RequireAuth:
        CheckEllipAuth(Receipt)
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
                    **({"authority_sha256": KEllipReportSha} if RequireAuth else {}),
                }
            )
        }
    )
