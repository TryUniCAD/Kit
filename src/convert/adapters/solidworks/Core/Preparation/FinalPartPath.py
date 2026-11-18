from os import fspath as PathTextValue
from pathlib import Path as FilePath, PureWindowsPath
from convert.adapters.base.ContractTypes import IsBinaryTarget, KTargetType
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Core.Preparation.SelectPartSelf import (
    SelectPartSelf,
)


# staged writers must retain final filename ownership while native self selection keeps standalone host locators distinct from linked file identities
def FinalPartPath(
    TargetValue: KTargetType,
    OptionsValue: WriteOptions,
    RecipeValue: SelfFileInput,
    NameValue: str,
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
    InputValue = SelectPartSelf(FinalText, NameValue, RecipeValue)
    if isinstance(TargetValue, (str, FilePath)) and (
        PureWindowsPath(PathTextValue(TargetValue)).name.casefold()
        != PureWindowsPath(FinalText).name.casefold()
    ):
        raise ValueError("staged and final native part filenames must agree")
    return InputValue
