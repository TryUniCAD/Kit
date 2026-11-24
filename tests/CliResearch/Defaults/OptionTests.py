from hashlib import sha256 as HashBytes
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.CliResearch.Defaults.PresetFiles import PresetFiles
from tests.CliResearch.Defaults.ShortcutCli import ShortcutCli


# catalogue aliases must replace each other in both directions before the receiver admits the selected file
@TestMark.parametrize("FormatName", ("solidworks", "fusion"))
@TestMark.parametrize("PresetGeneric", (True, False))
def CheckAliases(TmpPath: FilePath, FormatName: str, PresetGeneric: bool) -> None:
    ConfigPath, _ = PresetFiles(TmpPath)
    Record = LoadJson(ConfigPath.read_bytes())
    Specific = f"--{FormatName}-catalogue"
    Options = Record["formats"][FormatName]["options"]
    if not PresetGeneric:
        Options[Specific] = Options.pop("--catalogue")
    _ = ConfigPath.write_text(DumpJson(Record), encoding="utf-8")
    _ = (TmpPath / "override.json").write_text(
        '{"selected":"explicit"}', encoding="utf-8"
    )
    Explicit = Specific if PresetGeneric else "--catalogue"
    Reply = ShortcutCli(
        TmpPath, ConfigPath, "run", FormatName, Explicit, "override.json"
    )
    assert Reply.returncode == 7, Reply.stderr
    assert LoadJson(Reply.stdout)["catalogue_content"] == {"selected": "explicit"}


# incompatible advice must reach the authoring refusal instead of silently disabling configured native sample creation
def CheckAuthFlag(TmpPath: FilePath) -> None:
    ConfigPath, _ = PresetFiles(TmpPath)
    Reply = ShortcutCli(
        TmpPath,
        ConfigPath,
        "run",
        "solidworks",
        "--advisor",
        "codex",
        "--auth",
        "login",
    )
    assert Reply.returncode == 2, Reply.stderr
    assert "authoring rejects decoder advice with grid three-values" in Reply.stderr
    assert not (TmpPath / "run outputs").exists()


# catalogue digest pin options must survive saved defaults for each supported format
@TestMark.parametrize("FormatName", ("solidworks", "fusion"))
def CheckDigestFlag(TmpPath: FilePath, FormatName: str) -> None:
    ConfigPath, _ = PresetFiles(TmpPath)
    Record = LoadJson(ConfigPath.read_bytes())
    Options = Record["formats"][FormatName]["options"]
    Digest = HashBytes(FilePath(Options["--catalogue"]).read_bytes()).hexdigest()
    Options[f"--{FormatName}-sha256"] = Digest
    _ = ConfigPath.write_text(DumpJson(Record), encoding="utf-8")
    Reply = ShortcutCli(TmpPath, ConfigPath, "run", FormatName)
    assert Reply.returncode == 7, Reply.stderr
    assert LoadJson(Reply.stdout)[FormatName + "_sha256"] == Digest
