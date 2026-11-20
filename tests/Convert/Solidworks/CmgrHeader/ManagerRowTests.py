from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath

from tests.Convert.Solidworks.CmgrHeader.MakeMgrWire import MakeMgrInput, MakeMgrWire
from tests.Convert.Solidworks.CmgrHeader.RunMgrWire import RunMgrWire


# embedded rows contribute one count and reuse the original mapped child identity
def TestDirRows(TmpPath: FilePath) -> None:
    AuthoredPath = TmpPath / "Manager.json"
    WirePath = TmpPath / "Manager.bin"
    ReportPath = TmpPath / "Report.json"
    _ = AuthoredPath.write_text(DumpJson(MakeMgrInput()), encoding="utf-8")
    Written = RunMgrWire("write", AuthoredPath, WirePath)
    assert Written.returncode == 0, Written.stdout + Written.stderr
    assert WirePath.read_bytes() == MakeMgrWire()
    Outcome = RunMgrWire("read", WirePath, ReportPath)
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = LoadJson(ReportPath.read_text(encoding="utf-8"))
    assert ReportValue["root_index"] == 2
    assert ReportValue["entry_indices"] == [1, 2, 3, 4]
    assert ReportValue["next_index"] == 5
    assert ReportValue["row_count"] == 2
    assert ReportValue["row_indices"] == [4, 4]
    assert ReportValue["saved_at"] == 3_001_234_567
    assert ReportValue["sort_word"] == -21
    assert ReportValue["schemas"] == {
        "dmConfigMgrHeader_c": 1,
        "suObList": 1,
        "dmConfigHeader_c": 1,
    }
