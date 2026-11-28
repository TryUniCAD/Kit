from json import loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Assembly.PlanarMateInput import MakeMateInput
from tests.Convert.Solidworks.Research.Assembly.RunMateBundle import RunMateBundle
from tests.Convert.Solidworks.Research.Config.AssertCfgRead import AssertCfgRead
from tests.Convert.Solidworks.Research.Config.AssertCfgReport import AssertCfgReport
from tests.Convert.Solidworks.Research.Config.CheckCfgCompat import CheckCfgCompat
from tests.Convert.Solidworks.Research.Config.RunConfigTool import RunConfigTool


# generated part and assembly graphs must verify real framing aliases edits and compatibility through processes
def TestConfigGraph(TmpPath: FilePath) -> None:
    ParentPath, ChildPath = RunMateBundle(
        MakeMateInput("typedconfig"), TmpPath / "pair"
    )
    ReportPath = TmpPath / "SdkConfig.json"
    Outcome = RunConfigTool(
        "CheckSdkConfig.py",
        (ParentPath, ChildPath),
        ReportPath,
        ("--malformed", "--modeled-edits"),
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    AssertCfgReport(CastValue(dict[str, object], LoadJson(ReportPath.read_bytes())))
    BridgePath = TmpPath / "BridgeConfig.json"
    Bridge = RunConfigTool("CheckConfigBridge.py", (ParentPath, ChildPath), BridgePath)
    assert Bridge.returncode == 0, Bridge.stdout + Bridge.stderr
    Report = CastValue(dict[str, object], LoadJson(BridgePath.read_bytes()))
    assert Report["passed"] is True and Report["public_full_linked_graph"] is False
    for RowValue in CastValue(list[dict[str, object]], Report["files"]):
        assert (
            RowValue["all_fields_aliases_positions_equal"]
            is RowValue["byte_identity_passed"]
            is True
        )
    AssertCfgRead(ChildPath)
    CheckCfgCompat(ChildPath)
