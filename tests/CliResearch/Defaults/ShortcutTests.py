from json import loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.CliResearch.Defaults.PresetFiles import PresetFiles
from tests.CliResearch.Defaults.ShortcutCli import ShortcutCli


# both configured formats must cross the installed cli and research process boundary with fresh output paths
@TestMark.parametrize("FormatName", ("solidworks", "fusion"))
def CheckShortcut(TmpPath: FilePath, FormatName: str) -> None:
    ConfigPath, _ = PresetFiles(TmpPath)
    Paths: list[str] = []
    for _ in range(2):
        Reply = ShortcutCli(TmpPath, ConfigPath, "run", FormatName)
        assert Reply.returncode == 7, Reply.stderr
        Result = LoadJson(Reply.stdout)
        assert Result["catalogue"] == "catalogue with spaces.json"
        assert Result["workers"] == "18" and Result["author_samples"] is True
        assert Result["batch_format"] == FormatName
        OutputPath = FilePath(Result["directory"])
        assert OutputPath.parent == TmpPath / "run outputs" and OutputPath.is_dir()
        Paths.append(str(OutputPath))
    assert Paths[0] != Paths[1]


# explicit caller values must replace configured options without duplicate flags or shared destinations
@TestMark.parametrize("WorkerArgs", (("--workers", "3"), ("--workers=3",)))
def CheckOverrides(TmpPath: FilePath, WorkerArgs: tuple[str, ...]) -> None:
    ConfigPath, _ = PresetFiles(TmpPath)
    OutputPath = TmpPath / "chosen output"
    Reply = ShortcutCli(
        TmpPath,
        ConfigPath,
        "run",
        "solidworks",
        *WorkerArgs,
        "--catalogue",
        "other.json",
        "--directory",
        str(OutputPath),
    )
    assert Reply.returncode == 7, Reply.stderr
    Result = LoadJson(Reply.stdout)
    assert Result["workers"] == "3" and Result["catalogue"] == "other.json"
    assert Result["directory"] == str(OutputPath)


# inspection and control operations must never inherit catalogue authoring or native readiness settings
@TestMark.parametrize("Operation", ("--input", "--pause", "--resume"))
def CheckOperations(TmpPath: FilePath, Operation: str) -> None:
    ConfigPath, _ = PresetFiles(TmpPath)
    OperationArgs = (
        (Operation, "part.SLDPRT") if Operation == "--input" else (Operation,)
    )
    Reply = ShortcutCli(TmpPath, ConfigPath, "run", "solidworks", *OperationArgs)
    assert Reply.returncode == 7, Reply.stderr
    Result = LoadJson(Reply.stdout)
    assert Result["catalogue"] is None and Result["workers"] is None
    assert Result["author_samples"] is False and Result["directory"] is None
