from json import loads as DecodeJson
from pathlib import Path as FilePath
from shutil import copy2 as CopyFile
from subprocess import run as RunProcess
from sys import executable as PythonExec


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
