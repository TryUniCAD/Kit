from collections.abc import Mapping
from hashlib import sha256 as CalcSha

from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.Measured.PatNativePins import (
    KPatternPacket,
    KPatternResult,
)
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from interchange.Core.Common import FreezeMapping


# the complete generated candidate must exactly match one independently measured cold archive
def MatchPatMeas(
    FilesValue: dict[str, object], Result: dict[str, object], Payload: bytes
) -> Mapping[str, object]:
    Digest = CalcSha(Payload).hexdigest()
    NamesValue = tuple(
        NameValue.removesuffix(".SLDPRT")
        for NameValue, Value in FilesValue.items()
        if NameValue.endswith(".SLDPRT") and Value == Digest
    )
    PhaseRows = ReadMeasMap(Result.get("phases"))
    Controls = ReadMeasMap(Result.get("controls"))
    if (
        len(NamesValue) != 1
        or set(Controls) != {"before", "after"}
        or not all(
            ReadMeasMap(Value).get("passed") is True for Value in Controls.values()
        )
    ):
        raise ValueError(
            "no exact native linear pattern measurement for generated output"
        )
    (Label,) = NamesValue
    EditPhase = ReadMeasMap(PhaseRows.get(Label + "-edit"))
    ReopenPhase = ReadMeasMap(PhaseRows.get(Label + "-reopen"))
    if not all(
        Value.get("passed") is True
        and Value.get("first_failure") is None
        and ReadMeasMap(Value.get("open")) == {"opened": True, "error": 0, "warning": 0}
        for Value in (EditPhase, ReopenPhase)
    ):
        raise ValueError("linear pattern measurement lacks the clean native lifecycle")
    return FreezeMapping(
        {
            KPartMeasureOpt: FreezeMapping(
                {
                    "generated_sha256": Digest,
                    "oracle_build": Result["build"],
                    "packet_sha256": KPatternPacket,
                    "native_result_sha256": KPatternResult,
                    "edit_record_sha256": ReadMeasSha(EditPhase.get("record_sha256")),
                    "reopen_record_sha256": ReadMeasSha(
                        ReopenPhase.get("record_sha256")
                    ),
                }
            )
        }
    )
