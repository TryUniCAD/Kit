from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.CliResearch.Defaults.PresetFiles import PresetFiles
from tests.CliResearch.Defaults.ShortcutCli import ShortcutCli


# caller supplied pins must reach the independent receiver unchanged rather than being stripped by defaults
@TestMark.parametrize("FormatName", ("solidworks", "fusion"))
def CheckPinForward(TmpPath: FilePath, FormatName: str) -> None:
    ConfigPath, Checkout = PresetFiles(TmpPath)
    Reply = ShortcutCli(
        TmpPath,
        ConfigPath,
        "run",
        FormatName,
        "--catalogue",
        str(Checkout / "catalogue with spaces.json"),
        f"--{FormatName}-sha256",
        "0" * 64,
    )
    assert Reply.returncode == 2 and "SHA-256 does not match" in Reply.stderr
    assert not (TmpPath / "run outputs").exists()
