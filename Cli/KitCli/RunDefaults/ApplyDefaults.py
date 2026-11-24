from pathlib import Path as FilePath
from uuid import uuid4 as NewIdentity

from KitCli.RunDefaults.LoadPreset import LoadPreset


# explicit command arguments must retain precedence while configured catalogue runs get fresh destinations
def ApplyDefaults(Arguments: list[str]) -> list[str]:
    if (
        len(Arguments) < 2
        or Arguments[0] != "run"
        or Arguments[1] not in {"solidworks", "fusion"}
    ):
        return Arguments
    FormatName = Arguments[1]
    Preset = LoadPreset(FormatName)
    if Preset is None:
        return Arguments
    ExtraArgs = Arguments[2:]
    Names = {Value.split("=", 1)[0] for Value in ExtraArgs if Value.startswith("-")}
    Prefix = ["run", "--root", Preset.RootPath, FormatName]
    if Names & {"--input", "--pause", "--resume", "--help", "-h"}:
        return [*Prefix, *ExtraArgs]
    CatalogueFlags = {"--catalogue", f"--{FormatName}-catalogue"}
    for Option, Setting in Preset.Options.items():
        if Option in Names or Setting is False:
            continue
        if Option in CatalogueFlags and Names & CatalogueFlags:
            continue
        ExtraArgs.append(Option)
        if isinstance(Setting, str):
            ExtraArgs.append(Setting)
    if "--directory" not in Names:
        OutputPath = FilePath(Preset.OutputRoot) / (
            FormatName + "-" + NewIdentity().hex
        )
        ExtraArgs.extend(("--directory", str(OutputPath)))
    return [*Prefix, *ExtraArgs]
