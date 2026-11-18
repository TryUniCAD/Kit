from pathlib import Path as FilePath


# owned companion publication must refuse ordinary windows filename collisions before construction or any staged output is emitted
def CheckFreshAsm(TargetValue: FilePath, ChildName: str) -> None:
    NameValues = {
        TargetValue.name.casefold(),
        (ChildName + ".SLDPRT").casefold(),
    }
    if not TargetValue.parent.is_dir():
        return
    for PathValue in TargetValue.parent.iterdir():
        if PathValue.name.casefold() in NameValues:
            raise FileExistsError(PathValue)
