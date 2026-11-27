from json import loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.CliResearch.Defaults.PresetFiles import PresetFiles
from tests.CliResearch.Defaults.ShortcutCli import ShortcutCli


# default user configuration discovery must work without an override variable or a shell startup script
@TestMark.parametrize("FormatName", ("solidworks", "fusion"))
def CheckHomePath(TmpPath: FilePath, FormatName: str) -> None:
    ConfigPath, _ = PresetFiles(TmpPath)
    HomeConfig = TmpPath / ".kit/RunDefaults.json"
    HomeConfig.parent.mkdir()
    _ = HomeConfig.write_bytes(ConfigPath.read_bytes())
    Reply = ShortcutCli(TmpPath, ConfigPath, "run", FormatName, UseHome=True)
    assert Reply.returncode == 7, Reply.stderr
    assert LoadJson(Reply.stdout)["catalogue_content"] == {"selected": "saved preset"}
