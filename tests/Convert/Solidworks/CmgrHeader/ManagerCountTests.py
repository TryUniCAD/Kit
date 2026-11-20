from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath

from tests.Convert.Solidworks.CmgrHeader.MakeMgrWire import (
    KCountThreshold,
    MakeMgrInput,
    MakeMgrWire,
)
from tests.Convert.Solidworks.CmgrHeader.RunMgrWire import RunMgrWire


# a real extended count still stores each distinct body and class once
def TestCountRows(TmpPath: FilePath) -> None:
    AuthoredPath = TmpPath / "Manager.json"
    WirePath = TmpPath / "Manager.bin"
    ReportPath = TmpPath / "Report.json"
    _ = AuthoredPath.write_text(
        DumpJson(MakeMgrInput(IsExtended=True)), encoding="utf-8"
    )
    Written = RunMgrWire("write", AuthoredPath, WirePath)
    assert Written.returncode == 0, Written.stdout + Written.stderr
    assert WirePath.read_bytes() == MakeMgrWire(IsExtended=True)
    Outcome = RunMgrWire("read", WirePath, ReportPath)
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    ReportValue = LoadJson(ReportPath.read_text(encoding="utf-8"))
    assert ReportValue["entry_indices"] == [1, 2, 3, 4, 5]
    assert ReportValue["next_index"] == 6
    assert ReportValue["row_count"] == KCountThreshold
    assert ReportValue["row_indices"] == [4, 5] + [4] * (KCountThreshold - 2)
    assert ReportValue["schemas"]["dmConfigHeader_c"] == 2
