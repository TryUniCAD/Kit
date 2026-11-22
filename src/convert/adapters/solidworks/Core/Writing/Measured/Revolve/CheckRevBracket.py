from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasNum import ReadMeasNum
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.ReadRevMass import (
    ReadRevMass,
)
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.RevEvidence import (
    RevEvidence,
)
from convert.adapters.solidworks.Core.Writing.Measured.Revolve.RevProcessBirth import (
    RevProcessBirth,
)


# bracket controls must be the unchanged job control on either side of every fresh candidate phase
def CheckRevBracket(Evidence: RevEvidence) -> None:
    Before, After = ReadMeasRows(Evidence.Report.get("controls"), 2)
    SourceSha = ReadMeasSha(Evidence.Job.get("control_sha256"))
    for RoleName, RowValue in (("control_before", Before), ("control_after", After)):
        if (
            RowValue.get("kind") != RoleName
            or RowValue.get("path") != Evidence.Job.get("control")
            or RowValue.get("sha256") != SourceSha
            or any(RowValue.get(Field) is not True for Field in ("healthy", "opened", "rebuilt"))
            or any(RowValue.get(Field) != 0 for Field in ("open_errors", "open_warnings", "whats_wrong"))
            or ReadMeasNum(RowValue.get("bodies")) != 1
        ):
            raise ValueError("measured revolve lacks a healthy native bracket control")
        _ = ReadRevMass(RowValue.get("mass"))
    Births = tuple(
        RevProcessBirth(RowValue)
        for RowValue in (
            Before,
            *ReadMeasRows(Evidence.Report.get("cases"), 2),
            *ReadMeasRows(Evidence.Report.get("derivative_reopens"), 2),
            After,
        )
    )
    if len(set(Births)) != 6 or any(not Births[0][1] < Birth[1] < Births[-1][1] for Birth in Births[1:-1]):
        raise ValueError("measured revolve requires distinct bracketed native launches")
