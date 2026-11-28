from collections.abc import Mapping
from hashlib import sha256 as CalcSha

from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.MeasOracle import KOraclePart
from convert.adapters.solidworks.Core.Writing.RevolveEnds.RevEndCase import RevEndCase
from interchange.Core.Common import FreezeMapping


# the native result can qualify only the complete regenerated archive
def MatchRevEndMeas(
    CaseValue: RevEndCase, Payload: bytes, ResultSha: str
) -> Mapping[str, object]:
    Digest = CalcSha(Payload).hexdigest()
    if Digest != CaseValue.CandidateSha:
        raise ValueError(
            "regenerated SOLIDWORKS revolve has no matching native measurement"
        )
    return FreezeMapping(
        {
            KPartMeasureOpt: FreezeMapping(
                {
                    "generated_sha256": Digest,
                    "oracle_build": KOraclePart["build"],
                    "native_result_sha256": ResultSha,
                    "edit_record_sha256": CaseValue.EditSha,
                    "reopen_record_sha256": CaseValue.ReopenSha,
                }
            )
        }
    )
