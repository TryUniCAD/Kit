from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.CliResearch.Defaults.PresetFiles import PresetFiles
from tests.CliResearch.Defaults.ShortcutCli import ShortcutCli


# malformed private defaults must fail before any research destination or application can be started
@TestMark.parametrize(
    "InvalidText",
    ("{", "[]", '{"schema_version":2,"formats":{}}', " " * 65537),
    ids=("syntax", "array", "schema", "oversize"),
)
def CheckBadConfig(TmpPath: FilePath, InvalidText: str) -> None:
    ConfigPath, _ = PresetFiles(TmpPath)
    _ = ConfigPath.write_text(InvalidText, encoding="utf-8")
    Reply = ShortcutCli(TmpPath, ConfigPath, "run", "solidworks")
    assert Reply.returncode == 1 and LoadJson(Reply.stderr)["error"] in {
        "ValueError",
        "JSONDecodeError",
    }
    assert not (TmpPath / "run outputs").exists()


# explicit research roots and unrelated commands must remain usable even when private presets are invalid
def CheckBypass(TmpPath: FilePath) -> None:
    ConfigPath, Checkout = PresetFiles(TmpPath)
    _ = ConfigPath.write_text("{", encoding="utf-8")
    Reply = ShortcutCli(
        TmpPath,
        ConfigPath,
        "run",
        "--root",
        str(Checkout),
        "solidworks",
        "--workers",
        "9",
    )
    assert Reply.returncode == 7, Reply.stderr
    assert LoadJson(Reply.stdout)["workers"] == "9"
    Version = ShortcutCli(TmpPath, ConfigPath, "--version")
    assert Version.returncode == 0


# relative trusted roots and operation flags cannot be admitted through a saved catalogue preset
@TestMark.parametrize(
    "Change",
    (
        {"root": "relative"},
        {"options": {"--root": "other"}},
        {"options": {"--workers": 18}},
    ),
)
def CheckBadPreset(TmpPath: FilePath, Change: dict[str, object]) -> None:
    ConfigPath, _ = PresetFiles(TmpPath)
    Record = LoadJson(ConfigPath.read_bytes())
    Record["formats"]["solidworks"].update(Change)
    _ = ConfigPath.write_text(DumpJson(Record), encoding="utf-8")
    Reply = ShortcutCli(TmpPath, ConfigPath, "run", "solidworks")
    assert Reply.returncode == 1 and LoadJson(Reply.stderr)["error"] == "ValueError"
    assert not (TmpPath / "run outputs").exists()


# saved catalogue files must not change with the callers directory under any supported catalogue spelling
@TestMark.parametrize(
    "Option", ("--catalogue", "--solidworks-catalogue", "--fusion-catalogue")
)
def CheckRelCatalog(TmpPath: FilePath, Option: str) -> None:
    ConfigPath, _ = PresetFiles(TmpPath)
    Record = LoadJson(ConfigPath.read_bytes())
    Record["formats"]["solidworks"]["options"] = {Option: "relative.json"}
    _ = ConfigPath.write_text(DumpJson(Record), encoding="utf-8")
    Reply = ShortcutCli(TmpPath, ConfigPath, "run", "solidworks")
    assert (
        Reply.returncode == 1
        and "Saved catalogue paths must be absolute" in Reply.stderr
    )
    assert not (TmpPath / "run outputs").exists()
