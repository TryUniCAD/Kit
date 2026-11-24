from pathlib import Path as FilePath
from re import fullmatch as FullMatch
from typing import cast as CastValue

from KitCli.RunDefaults.RunPreset import RunPreset


# explicit private settings must reject ambiguous paths and argument shapes before research dispatch
def ReadPreset(Value: object) -> RunPreset:
    if not isinstance(Value, dict):
        raise ValueError("Run defaults require a format object")
    Record = CastValue(dict[str, object], Value)
    if set(Record) != {"root", "output_root", "options"}:
        raise ValueError("Run defaults require root, output_root and options")
    Paths: dict[str, str] = {}
    for Field in ("root", "output_root"):
        RawPath = Record[Field]
        if (
            not isinstance(RawPath, str)
            or not FilePath(RawPath).expanduser().is_absolute()
        ):
            raise ValueError("Run defaults paths must be absolute")
        Paths[Field] = str(FilePath(RawPath).expanduser())
    RawOptions = Record["options"]
    if not isinstance(RawOptions, dict):
        raise ValueError("Run defaults options must be an object")
    Options: dict[str, str | bool] = {}
    for Option, Setting in CastValue(dict[object, object], RawOptions).items():
        if (
            not isinstance(Option, str)
            or FullMatch(r"--[a-z]+(?:-[a-z]+)*", Option) is None
        ):
            raise ValueError("Run defaults option names must be full long flags")
        if Option in {
            "--root",
            "--directory",
            "--input",
            "--pause",
            "--resume",
            "--help",
        }:
            raise ValueError(
                "Run defaults cannot configure root or operation flags as options"
            )
        if not isinstance(Setting, (str, bool)):
            raise ValueError("Run defaults option values must be strings or booleans")
        if isinstance(Setting, str) and (
            not Setting or len(Setting) > 4096 or not Setting.isprintable()
        ):
            raise ValueError("Run defaults values must contain printable bounded text")
        Options[Option] = Setting
    return RunPreset(Paths["root"], Paths["output_root"], Options)
