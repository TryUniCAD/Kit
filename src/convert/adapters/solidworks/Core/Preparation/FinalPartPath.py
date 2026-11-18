from os import fspath as PathTextValue
from pathlib import Path as FilePath, PureWindowsPath
from convert.adapters.base.ContractTypes import IsBinaryTarget, KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Core.Preparation.RequirePartPath import (
    RequirePartPath,
)


# staged writers must encode the final requested identity while unbound streams and unmapped host paths remain explicitly outside the proven profile
def FinalPartPath(
    TargetValue: KTargetType, OptionsValue: WriteOptions, SavedAt: int
) -> SelfFileInput:
    IsPath = isinstance(TargetValue, (str, FilePath))
    if not IsPath and not IsBinaryTarget(TargetValue):
        raise TypeError("native part preparation needs a path or binary destination")
    FinalValue = OptionsValue.values.get("final_destination")
    if FinalValue is None:
        if not isinstance(TargetValue, (str, FilePath)):
            raise ValueError(
                "unnamed native streams require an explicit final destination"
            )
        FinalValue = TargetValue
    if not isinstance(FinalValue, (str, FilePath)):
        raise TypeError("final destination must be path text or a filesystem path")
    FinalText = PathTextValue(FinalValue)
    InputValue = RequirePartPath(FinalText, SavedAt)
    if isinstance(TargetValue, (str, FilePath)) and (
        PureWindowsPath(PathTextValue(TargetValue)).name.casefold()
        != PureWindowsPath(FinalText).name.casefold()
    ):
        raise ValueError("staged and final native part filenames must agree")
    return InputValue
