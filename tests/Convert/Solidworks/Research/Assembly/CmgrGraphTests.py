from json import loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from convert import open_document as OpenDocument
from tests.Convert.Solidworks.Research.Assembly.AssertCmgrBad import AssertCmgrBad
from tests.Convert.Solidworks.Research.Assembly.CheckCmgrRead import CheckCmgrRead
from tests.Convert.Solidworks.Research.Assembly.CheckCmgrExtra import CheckCmgrExtra
from tests.Convert.Solidworks.Research.Assembly.PlanarMateInput import MakeMateInput
from tests.Convert.Solidworks.Research.Assembly.RunCmgrCheck import RunCmgrCheck
from tests.Convert.Solidworks.Research.Assembly.RunMateBundle import RunMateBundle


# the normal sdk must project configuration metadata from its complete shared manager grammar
def AssertCmgrInfo(InputPath: FilePath, ConfigName: str) -> None:
    Document = OpenDocument(InputPath, include_brep=False, include_tessellation=False)
    InfoValue = CastValue(
        dict[str, object], Document.metadata["solidworks.typed_configuration_manager"]
    )
    assert InfoValue["status"] == "complete" and InfoValue["full_linked_graph"] is False
    assert InfoValue["archive_version"] == 19000 and InfoValue["map_base"] == 1
    (ConfigRow,) = CastValue(tuple[dict[str, object], ...], InfoValue["configurations"])
    assert ConfigRow["name"] == ConfigName
    assert ConfigRow["selected_by_f360"] is ConfigRow["selected_by_f368"] is True
    UsageValue = CastValue(dict[str, object], InfoValue["usage"])
    assert UsageValue["completed"] is True and UsageValue["used_schemas"]
    assert not UsageValue["missing_schemas"] and not UsageValue["provisional_schemas"]


# guarded authored pairs verify manager bytes aliases metadata and malformed rejection through real processes
def TestCmgrGraph(TmpPath: FilePath) -> None:
    Request = MakeMateInput("typedmanager")
    Bundle = CastValue(dict[str, object], Request["bundle"])
    Assembly = CastValue(dict[str, object], Bundle["assembly"])
    Child = CastValue(dict[str, object], Bundle["child"])
    Document = CastValue(dict[str, object], Child["document"])
    Assembly["configuration_name"], Document["configuration_name"] = (
        "typed primary α",
        "typed child β",
    )
    ParentPath, ChildPath = RunMateBundle(Request, TmpPath / "pair")
    ReportPath = TmpPath / "CmgrReport.json"
    Outcome = RunCmgrCheck((ParentPath, ChildPath), ReportPath)
    assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
    Report = CastValue(dict[str, object], LoadJson(ReportPath.read_bytes()))
    assert Report["passed"] is True and Report["public_full_linked_graph"] is False
    for RowValue in CastValue(list[dict[str, object]], Report["files"]):
        assert RowValue["byte_identity_passed"] is True and RowValue["map_base"] == 1
        assert RowValue["sha256"] == RowValue["output_sha256"]
        for Direction in ("load", "store"):
            UsageValue = CastValue(dict[str, object], RowValue[Direction])
            assert UsageValue["completed"] is True and UsageValue["used_schemas"]
            assert (
                UsageValue["missing_schemas"] == UsageValue["provisional_schemas"] == []
            )
    AssemblyPath = CheckCmgrRead(
        TmpPath, CastValue(str, Assembly["configuration_name"])
    )
    AssertCmgrInfo(ChildPath, CastValue(str, Document["configuration_name"]))
    AssertCmgrBad(AssemblyPath)
    CheckCmgrExtra(AssemblyPath)
