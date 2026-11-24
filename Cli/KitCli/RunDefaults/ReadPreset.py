from pathlib import Path as FilePath
from typing import cast as CastValue

from KitCli.RunDefaults.RunPreset import RunPreset
from KitCli.RunDefaults.ReadOptions import ReadOptions


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
    Options = ReadOptions(Record["options"])
    return RunPreset(Paths["root"], Paths["output_root"], Options)
