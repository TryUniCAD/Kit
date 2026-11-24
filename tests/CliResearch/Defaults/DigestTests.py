from hashlib import sha256 as HashBytes
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.CliResearch.Defaults.PresetFiles import PresetFiles
from tests.CliResearch.Defaults.ShortcutCli import ShortcutCli


# explicit catalogue selection must replace the saved file and its pin while preserving explicit replacement pins
@TestMark.parametrize("FormatName", ("solidworks", "fusion"))
@TestMark.parametrize("GenericPath", (True, False))
@TestMark.parametrize("SupplyPin", (True, False))
def CheckPinChange(
    TmpPath: FilePath, FormatName: str, GenericPath: bool, SupplyPin: bool
) -> None:
    ConfigPath, _ = PresetFiles(TmpPath)
    Record = LoadJson(ConfigPath.read_bytes())
    Options = Record["formats"][FormatName]["options"]
    PinFlag = f"--{FormatName}-sha256"
    Options[PinFlag] = HashBytes(
        FilePath(Options["--catalogue"]).read_bytes()
    ).hexdigest()
    _ = ConfigPath.write_text(DumpJson(Record), encoding="utf-8")
    Replacement = TmpPath / "replacement.json"
    _ = Replacement.write_text('{"selected":"replacement"}', encoding="utf-8")
    NewDigest = HashBytes(Replacement.read_bytes()).hexdigest()
    PathFlag = "--catalogue" if GenericPath else f"--{FormatName}-catalogue"
    PinArgs = (PinFlag, NewDigest) if SupplyPin else ()
    Reply = ShortcutCli(
        TmpPath, ConfigPath, "run", FormatName, PathFlag, Replacement.name, *PinArgs
    )
    assert Reply.returncode == 7, Reply.stderr
    Result = LoadJson(Reply.stdout)
    assert Result["catalogue_content"] == {"selected": "replacement"}
    assert Result[FormatName + "_sha256"] == (NewDigest if SupplyPin else None)


# a caller supplied incorrect digest must still refuse before publishing its destination
@TestMark.parametrize("FormatName", ("solidworks", "fusion"))
def CheckGivenPin(TmpPath: FilePath, FormatName: str) -> None:
    ConfigPath, Checkout = PresetFiles(TmpPath)
    OutputPath = TmpPath / "rejected"
    Reply = ShortcutCli(
        TmpPath,
        ConfigPath,
        "run",
        FormatName,
        "--catalogue",
        str(Checkout / "catalogue with spaces.json"),
        f"--{FormatName}-sha256",
        "0" * 64,
        "--directory",
        str(OutputPath),
    )
    assert Reply.returncode == 2 and "SHA-256 does not match" in Reply.stderr
    assert not OutputPath.exists()
