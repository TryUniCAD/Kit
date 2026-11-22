from pathlib import Path as FilePath


# every planned bundle filename is checked with the same windows case policy before generating output
def CheckFreshFiles(TargetValue: FilePath, NamesValue: tuple[str, ...]) -> None:
    NameValues = {
        TargetValue.name.casefold(),
        *(Value.casefold() for Value in NamesValue),
    }
    if not TargetValue.parent.is_dir():
        return
    for PathValue in TargetValue.parent.iterdir():
        if PathValue.name.casefold() in NameValues:
            raise FileExistsError(PathValue)
