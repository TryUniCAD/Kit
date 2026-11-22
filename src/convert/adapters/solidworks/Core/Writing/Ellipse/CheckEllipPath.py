from pathlib import Path as FilePath

from convert.adapters.base.WriteOptions import WriteOptions


# a file must occupy its real final path or the registry staging slot beside it
def CheckEllipPath(OutputPath: FilePath, Settings: WriteOptions) -> None:
    FinalValue = Settings.values.get("final_destination", OutputPath)
    if not isinstance(FinalValue, (str, FilePath)):
        raise ValueError("measured ellipse needs its actual final filesystem locator")
    FinalPath = FilePath(FinalValue).expanduser()
    if not FinalPath.is_absolute():
        raise ValueError("measured ellipse needs its actual final filesystem locator")
    FinalPath = FinalPath.resolve()
    StageParent = OutputPath.parent
    if OutputPath != FinalPath and not (
        OutputPath.name == FinalPath.name
        and StageParent.parent == FinalPath.parent
        and StageParent.name.startswith(f".{FinalPath.name}.kit-")
    ):
        raise ValueError("measured ellipse needs its actual final filesystem locator")
