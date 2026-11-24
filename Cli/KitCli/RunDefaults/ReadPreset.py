from typing import cast as CastValue

from KitCli.RunDefaults.RunPreset import RunPreset
from KitCli.RunDefaults.ReadOptions import ReadOptions
from KitCli.RunDefaults.PresetPath import PresetPath


# explicit private settings must reject ambiguous paths and argument shapes before research dispatch
def ReadPreset(Value: object) -> RunPreset:
    if not isinstance(Value, dict):
        raise ValueError("Run defaults require a format object")
    Record = CastValue(dict[str, object], Value)
    if set(Record) != {"root", "output_root", "options"}:
        raise ValueError("Run defaults require root, output_root and options")
    Paths: dict[str, str] = {}
    for Field in ("root", "output_root"):
        Paths[Field] = PresetPath(Record[Field])
    Options = ReadOptions(Record["options"])
    return RunPreset(Paths["root"], Paths["output_root"], Options)
