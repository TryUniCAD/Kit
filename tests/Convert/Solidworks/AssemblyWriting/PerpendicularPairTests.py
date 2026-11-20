from pathlib import Path as FilePath

from tests.Convert.Solidworks.AssemblyWriting.RunPublicWrite import RunPublicWrite


# the strict registry must publish the exact same pair through both formats and refuse invalid starting geometry
def TestPerpPair(TmpPath: FilePath) -> None:
    Default = RunPublicWrite("perpendicular", 2, TmpPath / "Default")
    Explicit = RunPublicWrite("perpendicular-explicit", 2, TmpPath / "Explicit")
    Invalid = RunPublicWrite("perpendicular-invalid", 2, TmpPath / "Invalid")
    assert Default["after"] == Explicit["after"]
    for ReportValue in (Default, Explicit, Invalid):
        assert ReportValue["passed"] is True
        assert ReportValue["runtime_input_file_reads"] == 0
        assert ReportValue["native_processes_started"] == 0
    assert Default["writer_native_flags"] is True
    assert Explicit["writer_native_flags"] is True
    assert Invalid["writer_native_flags"] is False
    assert Invalid["before"] == Invalid["after"] == {}
