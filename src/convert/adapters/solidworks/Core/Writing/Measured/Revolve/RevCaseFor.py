from pathlib import PureWindowsPath

from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.RevEvidence import (
    RevEvidence,
)


# the authored model basename selects its sole exact job row before the real destination is verified
def RevCaseFor(Evidence: RevEvidence, NameValue: str) -> tuple[str, str]:
    Matches = tuple(
        RowValue
        for RowValue in ReadMeasRows(Evidence.Job.get("cases"), 2)
        if ReadMeasMap(RowValue.get("model")).get("name") == NameValue
    )
    if len(Matches) != 1:
        raise ValueError("measured revolve requires one inspected model with its exact name")
    (RowValue,) = Matches
    Locator = RowValue.get("source")
    if (
        type(Locator) is not str
        or PureWindowsPath(Locator).stem != NameValue
        or PureWindowsPath(Locator).drive.casefold() != r"\\mac\home"
    ):
        raise ValueError("measured revolve requires its inspected Mac Home self locator")
    return Locator, ReadMeasSha(RowValue.get("sha256"))
