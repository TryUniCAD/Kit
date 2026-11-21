from pathlib import Path as FilePath
from os import name as KHostName

from tests.Convert.Solidworks.AssemblyWriting.RunPublicWrite import RunPublicWrite


# default and explicit format selection must publish each owned occurrence profile through the genuine public sdk path
def TestNativePairs(TmpPath: FilePath) -> None:
    for CountValue in (2, 3):
        for ModeValue in ("fresh", "explicit"):
            OutputPath = TmpPath / f"{ModeValue}{CountValue}"
            ReportValue = RunPublicWrite(ModeValue, CountValue, OutputPath)
            assert ReportValue["passed"] is True
            assert ReportValue["runtime_input_file_reads"] == 0
            assert ReportValue["native_processes_started"] == 0
            assert ReportValue["writer_native_flags"] is True
    if KHostName == "nt":
        ReportValue = RunPublicWrite("direct", 3, TmpPath / "DirectWindows")
        assert ReportValue["passed"] is True
        assert ReportValue["runtime_input_file_reads"] == 0
