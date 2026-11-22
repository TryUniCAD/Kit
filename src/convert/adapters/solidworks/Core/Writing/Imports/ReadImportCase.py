from convert.adapters.solidworks.Core.Writing.Imports.CheckImportLife import (
    CheckImportLife,
)
from convert.adapters.solidworks.Core.Writing.Imports.ImportMeasure import ImportMeasure
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha


# publication keeps only checked immutable values from the authenticated case
def ReadImportCase(
    CaseValue: dict[str, object],
    EpochValue: int,
    ResultSha: str,
    NumericChecks: int,
) -> ImportMeasure:
    SizeValue = CaseValue.get("generated_bytes")
    if type(SizeValue) is not int or SizeValue < 1:
        raise ValueError("local solid measurement lacks a complete archive size")
    RebuildSha, ReopenSha = CheckImportLife(CaseValue, NumericChecks)
    return ImportMeasure(
        EpochValue,
        SizeValue,
        ReadMeasSha(CaseValue.get("native_input_sha256")),
        ResultSha,
        RebuildSha,
        ReopenSha,
    )
