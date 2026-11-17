from json import loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Assembly.PlanarMateInput import MakeMateInput
from tests.Convert.Solidworks.Research.Assembly.RunMateBundle import RunMateBundle
from tests.Convert.Solidworks.Research.Resolved.AssertResolRows import AssertResolRows
from tests.Convert.Solidworks.Research.Resolved.CheckResolTail import CheckResolTail
from tests.Convert.Solidworks.Research.Resolved.RunResolvedTool import RunResolvedTool


# generated neutral models must preserve linked graph fields maps and compatibility through real processes
def TestResolved(TmpPath: FilePath) -> None:
    ParentPath, ChildPath = RunMateBundle(
        MakeMateInput("typedresolved"), TmpPath / "pair"
    )
    ReportPath = TmpPath / "SdkResolved.json"
    Outcome = RunResolvedTool(
        "CheckSdkResolved.py",
        (ParentPath, ChildPath),
        ReportPath,
        ("--malformed", "--modeled-edits"),
    )
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    AssertResolRows(CastValue(dict[str, object], LoadJson(ReportPath.read_bytes())))
    BridgePath = TmpPath / "BridgeResolved.json"
    Bridge = RunResolvedTool(
        "CheckResolvedBridge.py", (ParentPath, ChildPath), BridgePath
    )
    assert Bridge.returncode == 0, Bridge.stdout + Bridge.stderr
    Report = CastValue(dict[str, object], LoadJson(BridgePath.read_bytes()))
    assert Report["passed"] is True and Report["public_full_linked_graph"] is False
    for RowValue in CastValue(list[dict[str, object]], Report["files"]):
        assert (
            RowValue["all_fields_aliases_positions_equal"]
            is RowValue["byte_identity_passed"]
            is True
        )
    CheckResolTail(ChildPath)
