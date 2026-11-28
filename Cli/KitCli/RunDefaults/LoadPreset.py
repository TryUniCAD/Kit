from json import loads as LoadJson
from os import environ as KEnvironment
from os.path import abspath as AbsolutePath, expanduser as ExpandUser
from pathlib import Path as FilePath
from typing import cast as CastValue

from convert.Security.LexicalBoundary import ResolveLexical
from KitCli.RunDefaults.ReadPreset import ReadPreset
from KitCli.RunDefaults.RunPreset import RunPreset


# saved user configuration makes catalogue shortcuts independent of shell profiles and working directories
def LoadPreset(FormatName: str) -> RunPreset | None:
    ConfigValue = KEnvironment.get("KIT_RUN_DEFAULTS")
    HomePath = FilePath.home()
    ConfigPath = HomePath / ".kit" / "RunDefaults.json"
    if ConfigValue:
        try:
            ConfigPath = ResolveLexical(AbsolutePath(ExpandUser(ConfigValue)), HomePath)
        except ValueError as Error:
            raise ValueError(
                "KIT_RUN_DEFAULTS must name a file inside the user home"
            ) from Error
    if ConfigValue is None and not ConfigPath.exists():
        return None
    with ConfigPath.open("rb") as ConfigFile:
        Content = ConfigFile.read(65537)
    if len(Content) > 65536:
        raise ValueError("Run defaults must not exceed 64 KiB")
    Value: object = LoadJson(Content)
    if not isinstance(Value, dict):
        raise ValueError("Run defaults require a versioned JSON object")
    Record = CastValue(dict[str, object], Value)
    if (
        set(Record) != {"schema_version", "formats"}
        or type(Record["schema_version"]) is not int
        or Record["schema_version"] != 1
    ):
        raise ValueError("Run defaults require schema_version 1 and formats")
    Formats = Record["formats"]
    if not isinstance(Formats, dict):
        raise ValueError("Run defaults formats must be an object")
    Preset = CastValue(dict[str, object], Formats).get(FormatName)
    return None if Preset is None else ReadPreset(Preset)
