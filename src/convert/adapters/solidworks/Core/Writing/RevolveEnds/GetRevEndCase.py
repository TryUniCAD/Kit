from pathlib import PureWindowsPath

from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasMap import ReadMeasMap
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasRows import ReadMeasRows
from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasSha import ReadMeasSha
from convert.adapters.solidworks.Core.Writing.RevolveEnds.CheckEndBracket import (
    CheckEndBracket,
)
from convert.adapters.solidworks.Core.Writing.RevolveEnds.ReadRevEndLife import (
    ReadRevEndLife,
)
from convert.adapters.solidworks.Core.Writing.RevolveEnds.RevEndCase import RevEndCase
from convert.adapters.solidworks.Core.Writing.RevolveEnds.RevEndReports import (
    RevEndReports,
)


# the modeled name must select the same candidate across all three exact reports
def GetRevEndCase(Reports: RevEndReports, NameValue: str, SideValue: str) -> RevEndCase:
    FilesValue = ReadMeasMap(Reports.JobValue.get("files"))
    if NameValue not in FilesValue:
        raise ValueError("measured revolve ends need the exact inspected model name")
    JobCase = ReadMeasMap(FilesValue[NameValue])
    Locator = JobCase.get("candidate")
    if type(Locator) is not str:
        raise ValueError("measured revolve ends need the exact inspected self locator")
    NativePath = PureWindowsPath(Locator)
    if NativePath.name != f"{NameValue}.SLDPRT" or (
        NativePath.drive.casefold() != r"\\mac\home"
    ):
        raise ValueError("measured revolve ends need the exact inspected self locator")
    CandidateSha = ReadMeasSha(JobCase.get("candidate_sha256"))
    GenCase = ReadMeasMap(
        ReadMeasMap(Reports.GenerationValue.get("cases")).get(NameValue)
    )
    Matches = tuple(
        NativeRow
        for NativeRow in ReadMeasRows(Reports.ResultValue.get("cases"), 4)
        if NativeRow.get("name") == NameValue
        and NativeRow.get("candidate_sha256") == CandidateSha
    )
    if GenCase.get("archive_sha256") != CandidateSha or len(Matches) != 1:
        raise ValueError("measured revolve end candidate digests differ")
    Controls = CheckEndBracket(Reports.ResultValue)
    EditSha, ReopenSha = ReadRevEndLife(Matches[0], SideValue)
    if len({*Controls, EditSha, ReopenSha}) != 4:
        raise ValueError("measured revolve end phases must be distinct")
    return RevEndCase(Locator, CandidateSha, EditSha, ReopenSha)
