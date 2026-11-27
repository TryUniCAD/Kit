from json import loads as DecodeJson
from pathlib import Path as FilePath
from shutil import copy2 as CopyFile
from subprocess import run as RunProcess
from sys import executable as PythonExec
from sqlite3 import connect as OpenStore


# generated planning must detect drift across real register and catalogue inputs
def CheckPlanning(TmpPath: FilePath) -> None:
    RootPath = FilePath(__file__).resolve().parents[3]
    SourceRoot = RootPath / "Documentation/Planning"
    Manifest = DecodeJson((SourceRoot / "Generated/Manifest.json").read_text())
    for RelPath in Manifest["SourceHashes"]:
        TargetPath = TmpPath / RelPath
        TargetPath.parent.mkdir(parents=True, exist_ok=True)
        CopyFile(RootPath / RelPath, TargetPath)
    Command = [
        PythonExec,
        str(RootPath / "re/automation/Planning/Build.py"),
        "--root",
        str(TmpPath),
    ]
    Process = RunProcess(Command, capture_output=True, text=True, check=False)
    assert Process.returncode == 0, Process.stderr
    Coverage = DecodeJson(
        (TmpPath / "Documentation/Planning/Generated/Coverage.json").read_text()
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
    GeneratedPath = TmpPath / "Documentation/Planning/Generated"
    TaskRows = [
        DecodeJson(Line)
        for Line in (GeneratedPath / "Tasks.jsonl").read_text().splitlines()
    ]
    OriginalIds = {(Row["Source"], Row["Id"]): Row["ScopeId"] for Row in TaskRows}
    ClaimRows = [
        DecodeJson(Line)
        for Line in (GeneratedPath / "Claims.jsonl").read_text().splitlines()
    ]
    BoardData = DecodeJson((GeneratedPath / "BoardData.json").read_text())
    BoardIds = {Item["Id"] for Item in BoardData["Items"]}
    assert len(ClaimRows) == Manifest["ProseClaims"]
    assert any(Row["TaskId"] == "A13a-FusionPreparedInputs" for Row in ClaimRows)
    assert {Row["Id"] for Row in ClaimRows} <= BoardIds
    RegisterPath = TmpPath / "Documentation/Reference/Research/AutomationSteps.md"
    SourceLines = RegisterPath.read_text().splitlines()
    InsertAt = next(
        Index for Index, Line in enumerate(SourceLines) if Line.startswith("| A11c ")
    )
    SourceLines.insert(InsertAt, SourceLines[InsertAt].replace("A11c", "A99a", 1))
    assert (
        RegisterPath.write_text(
            "\n".join(SourceLines)
            + "\n\n## A99a-ProcessCoverage: planning process coverage\n\n"
            + "Status is planned for this independent process coverage claim\n"
        )
        > 0
    )
    Process = RunProcess(Command, capture_output=True, text=True, check=False)
    assert Process.returncode == 0, Process.stderr
    UpdatedRows = [
        DecodeJson(Line)
        for Line in (GeneratedPath / "Tasks.jsonl").read_text().splitlines()
    ]
    UpdatedIds = {(Row["Source"], Row["Id"]): Row["ScopeId"] for Row in UpdatedRows}
    assert OriginalIds.items() <= UpdatedIds.items()
    assert len(UpdatedIds) == len(OriginalIds) + 1
    BoardData = DecodeJson((GeneratedPath / "BoardData.json").read_text())
    AddedClaims = [
        Item
        for Item in BoardData["Items"]
        if Item.get("TaskId") == "A99a-ProcessCoverage"
    ]
    assert len(AddedClaims) == 1
    assert AddedClaims[0]["Status"] == "planned"
    assert AddedClaims[0]["Kind"] == "Research claim"
    Process = RunProcess(
        [*Command, "--check"], capture_output=True, text=True, check=False
    )
    assert Process.returncode == 0, Process.stderr
    ChartPath = TmpPath / "Documentation/Planning/Generated/Gantt.svg"
    assert ChartPath.write_text("stale chart") > 0
    Process = RunProcess(
        [*Command, "--check"], capture_output=True, text=True, check=False
    )
    assert Process.returncode == 1
    assert "Gantt.svg" in Process.stderr


# malformed prerequisite graphs must fail before publishing misleading scheduled output
def CheckPlanCycle(TmpPath: FilePath) -> None:
    RootPath = FilePath(__file__).resolve().parents[3]
    Manifest = DecodeJson(
        (RootPath / "Documentation/Planning/Generated/Manifest.json").read_text()
    )
    for RelPath in Manifest["SourceHashes"]:
        TargetPath = TmpPath / RelPath
        TargetPath.parent.mkdir(parents=True, exist_ok=True)
        CopyFile(RootPath / RelPath, TargetPath)
    LinkPath = TmpPath / "Documentation/Planning/Links.json"
    assert (
        LinkPath.write_text(LinkPath.read_text().replace('"B01": []', '"B01": ["B01"]'))
        > 0
    )
    Process = RunProcess(
        [
            PythonExec,
            str(RootPath / "re/automation/Planning/Build.py"),
            "--root",
            str(TmpPath),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert Process.returncode != 0
    assert "Dependency cycle" in Process.stderr
    assert not (TmpPath / "Documentation/Planning/Generated/Tasks.md").exists()
