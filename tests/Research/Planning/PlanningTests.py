from json import loads as DecodeJson
from pathlib import Path as FilePath
from shutil import copy2 as CopyFile
from sqlite3 import connect as OpenStore
from subprocess import run as RunProcess
from sys import executable as PythonExec


# isolated source copies prevent planning process checks from changing maintained records
def PreparePlan(TmpPath: FilePath) -> list[str]:
    RootPath = FilePath(__file__).resolve().parents[3]
    Manifest = DecodeJson(
        (RootPath / "Documentation/Planning/Generated/Manifest.json").read_text(
            encoding="utf-8"
        )
    )
    for RelPath in Manifest["SourceHashes"]:
        TargetPath = TmpPath / RelPath
        TargetPath.parent.mkdir(parents=True, exist_ok=True)
        CopyFile(RootPath / RelPath, TargetPath)
    return [
        PythonExec,
        str(RootPath / "re/automation/Planning/Build.py"),
        "--root",
        str(TmpPath),
    ]


# generated planning must detect drift across real register and catalogue inputs
def CheckPlanning(TmpPath: FilePath) -> None:
    Command = PreparePlan(TmpPath)
    Process = RunProcess(Command, capture_output=True, text=True, check=False)
    assert Process.returncode == 0, Process.stderr
    Coverage = DecodeJson(
        (TmpPath / "Documentation/Planning/Generated/Coverage.json").read_text(
            encoding="utf-8"
        )
    )
    with OpenStore(
        (TmpPath / "re/Fusion/PlannerCatalog/Data/Catalog.sqlite").as_uri()
        + "?mode=ro",
        uri=True,
    ) as StoreInfo:
        assert (
            Coverage["FusionApiTypes"]
            == StoreInfo.execute(
                "SELECT COUNT(*) FROM items WHERE kind = 'api_type'"
            ).fetchone()[0]
        )
        assert (
            Coverage["FusionNativeTypes"]
            == StoreInfo.execute(
                "SELECT COUNT(*) FROM items WHERE kind = 'native_type'"
            ).fetchone()[0]
        )
    Process = RunProcess(
        [*Command, "--check"], capture_output=True, text=True, check=False
    )
    assert Process.returncode == 0, Process.stderr
    ChartPath = TmpPath / "Documentation/Planning/Generated/Gantt.svg"
    assert ChartPath.write_text("stale chart", encoding="utf-8") > 0
    Process = RunProcess(
        [*Command, "--check"], capture_output=True, text=True, check=False
    )
    assert Process.returncode == 1
    assert "Gantt.svg" in Process.stderr


# register insertion must not detach existing claims schedules or assignee mappings
def CheckStableIds(TmpPath: FilePath) -> None:
    Command = PreparePlan(TmpPath)
    Process = RunProcess(Command, capture_output=True, text=True, check=False)
    assert Process.returncode == 0, Process.stderr
    GeneratedPath = TmpPath / "Documentation/Planning/Generated"
    TaskRows = [
        DecodeJson(SourceLine)
        for SourceLine in (GeneratedPath / "Tasks.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    OriginalIds = {
        (TaskRow["Source"], TaskRow["Id"]): TaskRow["ScopeId"] for TaskRow in TaskRows
    }
    RegisterPath = TmpPath / "Documentation/Reference/Research/AutomationSteps.md"
    SourceLines = RegisterPath.read_text(encoding="utf-8").splitlines()
    InsertAt = next(
        Index
        for Index, SourceLine in enumerate(SourceLines)
        if SourceLine.startswith("| A11c ")
    )
    SourceLines.insert(InsertAt, SourceLines[InsertAt].replace("A11c", "A99a", 1))
    assert RegisterPath.write_text("\n".join(SourceLines) + "\n", encoding="utf-8") > 0
    Process = RunProcess(Command, capture_output=True, text=True, check=False)
    assert Process.returncode == 0, Process.stderr
    UpdatedRows = [
        DecodeJson(SourceLine)
        for SourceLine in (GeneratedPath / "Tasks.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    UpdatedIds = {
        (TaskRow["Source"], TaskRow["Id"]): TaskRow["ScopeId"]
        for TaskRow in UpdatedRows
    }
    assert OriginalIds.items() <= UpdatedIds.items()
    assert len(UpdatedIds) == len(OriginalIds) + 1


# prose claims must remain visible even when no table row represents their scope
def CheckPlanClaims(TmpPath: FilePath) -> None:
    Command = PreparePlan(TmpPath)
    Process = RunProcess(Command, capture_output=True, text=True, check=False)
    assert Process.returncode == 0, Process.stderr
    GeneratedPath = TmpPath / "Documentation/Planning/Generated"
    Manifest = DecodeJson((GeneratedPath / "Manifest.json").read_text(encoding="utf-8"))
    ClaimRows = [
        DecodeJson(SourceLine)
        for SourceLine in (GeneratedPath / "Claims.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    BoardData = DecodeJson(
        (GeneratedPath / "BoardData.json").read_text(encoding="utf-8")
    )
    BoardIds = {ItemInfo["Id"] for ItemInfo in BoardData["Items"]}
    assert len(ClaimRows) == Manifest["ProseClaims"]
    assert any(
        TaskRow["TaskId"] == "A13a-FusionPreparedInputs" for TaskRow in ClaimRows
    )
    assert {TaskRow["Id"] for TaskRow in ClaimRows} <= BoardIds
    RegisterPath = TmpPath / "Documentation/Reference/Research/AutomationSteps.md"
    assert (
        RegisterPath.write_text(
            RegisterPath.read_text(encoding="utf-8")
            + "\n\n## A99a-ProcessCoverage: planning process coverage\n\n"
            + "Status is planned for this independent process coverage claim\n",
            encoding="utf-8",
        )
        > 0
    )
    Process = RunProcess(Command, capture_output=True, text=True, check=False)
    assert Process.returncode == 0, Process.stderr
    BoardData = DecodeJson(
        (GeneratedPath / "BoardData.json").read_text(encoding="utf-8")
    )
    AddedClaims = [
        ItemInfo
        for ItemInfo in BoardData["Items"]
        if ItemInfo.get("TaskId") == "A99a-ProcessCoverage"
    ]
    assert len(AddedClaims) == 1
    assert AddedClaims[0]["Status"] == "planned"
    assert AddedClaims[0]["Kind"] == "Research claim"
    Process = RunProcess(
        [*Command, "--check"], capture_output=True, text=True, check=False
    )
    assert Process.returncode == 0, Process.stderr


# malformed prerequisite graphs must fail before publishing misleading scheduled output
def CheckPlanCycle(TmpPath: FilePath) -> None:
    Command = PreparePlan(TmpPath)
    LinkPath = TmpPath / "Documentation/Planning/Links.json"
    assert (
        LinkPath.write_text(
            LinkPath.read_text(encoding="utf-8").replace('"B01": []', '"B01": ["B01"]'),
            encoding="utf-8",
        )
        > 0
    )
    Process = RunProcess(Command, capture_output=True, text=True, check=False)
    assert Process.returncode != 0
    assert "Dependency cycle" in Process.stderr
    assert not (TmpPath / "Documentation/Planning/Generated/Tasks.md").exists()
