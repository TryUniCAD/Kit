from hashlib import sha256 as CalcSha

from convert.adapters.solidworks.Core.Writing.Imports.CheckImportLife import (
    CheckImportLife,
)
from convert.adapters.solidworks.Core.Writing.Imports.ImportMeasure import ImportMeasure
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha

# these measured scopes correspond to the two qualified neutral body profiles
KImportCases = (("RectangularBare", 116), ("ConcaveOwned", 164))


# scan only authorized completed lifecycles and bind the result to the full archive
def MatchImportMeas(
    Payload: bytes, EpochValue: int, Receipt: dict[str, object]
) -> ImportMeasure:
    CasesValue = ReadMeasMap(Receipt.get("cases"))
    SizeValue = len(Payload)
    CandidateSha = CalcSha(Payload).hexdigest()
    for RoleValue, NumericChecks in KImportCases:
        CaseValue = ReadMeasMap(CasesValue.get(RoleValue))
        if (
            CaseValue.get("generated_bytes") == SizeValue
            and ReadMeasSha(CaseValue.get("native_input_sha256")) == CandidateSha
        ):
            RebuildSha, ReopenSha = CheckImportLife(CaseValue, NumericChecks)
            return ImportMeasure(
                EpochValue,
                SizeValue,
                CandidateSha,
                ReadMeasSha(Receipt.get("native_raw_sha256")),
                RebuildSha,
                ReopenSha,
            )
    raise ValueError("regenerated local solid has no exact native measurement")
