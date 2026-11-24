from pathlib import Path as FilePath
from re import fullmatch as FullMatch
from typing import cast as CastValue


# saved catalogue arguments need stable file identities and must not silently choose another operation
def ReadOptions(Value: object) -> dict[str, str | bool]:
    if not isinstance(Value, dict):
        raise ValueError("Run defaults options must be an object")
    Options: dict[str, str | bool] = {}
    for Option, Setting in CastValue(dict[object, object], Value).items():
        if (
            not isinstance(Option, str)
            or FullMatch(r"--[a-z][a-z0-9]*(?:-[a-z][a-z0-9]*)*", Option) is None
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
        if Option in {"--catalogue", "--solidworks-catalogue", "--fusion-catalogue"}:
            if (
                not isinstance(Setting, str)
                or not FilePath(Setting).expanduser().is_absolute()
            ):
                raise ValueError("Saved catalogue paths must be absolute")
            Setting = str(FilePath(Setting).expanduser())
        Options[Option] = Setting
    return Options
