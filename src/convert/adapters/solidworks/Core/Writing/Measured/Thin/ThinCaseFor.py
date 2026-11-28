from pathlib import PureWindowsPath

from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha


# the authored model basename selects its sole exact job row before the real destination is verified
def ThinCaseFor(
    Report: dict[str, object], JobValue: dict[str, object], NameValue: str
) -> tuple[str, str, dict[str, object]]:
    Matches = tuple(
        RowValue
        for RowValue in ReadMeasRows(Report.get("cases"), 4)
        if RowValue.get("case") == NameValue
    )
    RootValue = JobValue.get("logical_root")
    if len(Matches) != 1 or type(RootValue) is not str:
        raise ValueError(
            "measured thin revolve requires one inspected model with its exact name"
        )
    (RowValue,) = Matches
    RootPath = PureWindowsPath(RootValue)
    NamePath = PureWindowsPath(NameValue)
    if (
        RootPath.drive.casefold() != "c:"
        or not RootPath.is_absolute()
        or NamePath.name != NameValue
    ):
        raise ValueError(
            "measured thin revolve requires its original Windows self locator"
        )
    Candidate = "Candidates/" + NameValue + ".SLDPRT"
    FileValues = ReadMeasMap(JobValue.get("files"))
    Digest = ReadMeasSha(RowValue.get("candidate_sha256"))
    if (
        RowValue.get("passed") is not True
        or Digest != FileValues.get(Candidate)
        or ReadMeasSha(RowValue.get("source_sha256"))
        != FileValues.get("Sources/" + NameValue + ".SLDPRT")
    ):
        raise ValueError("thin revolve job differs from its exact native case")
    return str(RootPath / Candidate), Digest, RowValue
