from collections.abc import Mapping
from hashlib import sha256 as CalcSha

from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from interchange.Core.Common import FreezeMapping


# the paired plain control provides evidence of the edit effect only for the independently measured equation output
def MatchEqMeas(Receipt: dict[str, object], Payload: bytes) -> Mapping[str, object]:
    Cases = ReadMeasMap(Receipt["cases"])
    Report = ReadMeasMap(Cases["Reference"])
    Oracle = ReadMeasMap(Receipt["oracle_identity"])
    Digest = CalcSha(Payload).hexdigest()
    if Digest != ReadMeasSha(Report["generated_sha256"]):
        raise ValueError(
            "complete native candidate differs from the measured width-depth output"
        )
    return FreezeMapping(
        {
            KPartMeasureOpt: FreezeMapping(
                {
                    "generated_sha256": Digest,
                    "oracle_build": Oracle["file_version"],
                    "native_result_sha256": ReadMeasSha(
                        Receipt["full_native_result_sha256"]
                    ),
                    "saved_reopen_sha256": ReadMeasSha(Report["saved_sha256"]),
                }
            )
        }
    )
