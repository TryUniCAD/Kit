from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.CliResearch.Defaults.PresetFiles import PresetFiles
from tests.CliResearch.Defaults.ShortcutCli import ShortcutCli


# unresolved account home paths must keep the normal structured error contract without starting research
@TestMark.parametrize("FieldName", ("root", "output_root", "catalogue"))
def CheckHomeError(TmpPath: FilePath, FieldName: str) -> None:
    ConfigPath, _ = PresetFiles(TmpPath)
    Record = LoadJson(ConfigPath.read_bytes())
    Preset = Record["formats"]["solidworks"]
    if FieldName == "catalogue":
        Preset["options"]["--catalogue"] = "~kitmissinguserc25a43e8/catalogue.json"
    else:
        Preset[FieldName] = "~kitmissinguserc25a43e8"
    _ = ConfigPath.write_text(DumpJson(Record), encoding="utf-8")
    Reply = ShortcutCli(TmpPath, ConfigPath, "run", "solidworks")
    assert Reply.returncode == 1
    assert LoadJson(Reply.stderr)["error"] == "ValueError"
    assert "Traceback" not in Reply.stderr and not (TmpPath / "run outputs").exists()
