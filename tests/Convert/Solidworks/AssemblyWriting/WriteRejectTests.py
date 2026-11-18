from pathlib import Path as FilePath
from os import name as KHostName

from tests.Convert.Solidworks.AssemblyWriting.RunPublicWrite import RunPublicWrite

# public rejection coverage must preserve existing targets and close unsupported bundle and model options
KRejectCases = (
    "child-collision",
    "case-collision",
    "directory-collision",
    "dangling-child",
    "root-collision",
    "overwrite-rejected",
    "overwrite-empty",
    "stream-rejected",
    "missing-mapping",
    "wrong-mapping",
    "relative-mapping",
    "wrong-format",
    "unqualified-option",
    "unsupported-mate",
    "unqualified-child",
    "commit-failure",
)


# a refused graph or handled publication failure must leave every caller owned entry identical and no staged bundle behind
def TestWriteReject(TmpPath: FilePath) -> None:
    for ModeValue in KRejectCases:
        if ModeValue == "missing-mapping" and KHostName == "nt":
            continue
        ReportValue = RunPublicWrite(ModeValue, 3, TmpPath / ModeValue)
        assert ReportValue["passed"] is True
        assert ReportValue["runtime_input_file_reads"] == 0
        assert ReportValue["before"] == ReportValue["after"]
        assert ReportValue["error"] is not None


# a peer owns a companion created after the normal assembly writer scans the output directory
def TestPeerWrite(TmpPath: FilePath) -> None:
    ReportValue = RunPublicWrite("race-protection", 3, TmpPath / "peer")
    assert ReportValue["passed"] is True
    assert ReportValue["concurrent_companion_preserved"] is True
    assert ReportValue["runtime_input_file_reads"] == 0
