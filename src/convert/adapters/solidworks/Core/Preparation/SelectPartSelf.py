from ntpath import join as JoinPath, splitdrive as SplitDrive
from pathlib import PurePosixPath, PureWindowsPath
from typing import cast as CastValue
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Container.Format import KPartSuffix
from convert.adapters.solidworks.Core.Preparation.RequirePartPath import (
    RequirePartPath,
)

# only the explicitly authored namespace with absent locator evidence may support standalone host preparation without claiming a real drive mapping
KNeutralRoot = r"C:\KitSdkCandidates"


# standalone host output may retain its authored neutral self locator while exact basename ownership prevents unsupported renaming and linked reference inference
def SelectPartSelf(
    FinalText: str, NameValue: str, RecipeValue: SelfFileInput
) -> SelfFileInput:
    if type(CastValue(object, RecipeValue)) is not SelfFileInput:
        raise TypeError("native self selection requires an explicit typed recipe")
    if SplitDrive(FinalText)[0]:
        return RequirePartPath(FinalText, RecipeValue.SavedAt)
    PathValue = PurePosixPath(FinalText)
    if not PathValue.is_absolute() or any(
        Value in (".", "..") for Value in FinalText.split("/")
    ):
        raise ValueError("standalone host output requires an absolute ordinary path")
    if PathValue.stem != NameValue or PathValue.suffix.casefold() != KPartSuffix:
        raise ValueError(
            "standalone host output must retain the exact neutral basename"
        )
    RecipePath = PureWindowsPath(RecipeValue.PathName)
    if (
        RecipeValue.PathName != JoinPath(KNeutralRoot, RecipePath.name)
        or RecipePath.stem != NameValue
        or RecipePath.suffix.casefold() != KPartSuffix
    ):
        raise ValueError(
            "standalone host output requires the measured authored locator"
        )
    NativeValue = RequirePartPath(
        JoinPath(str(RecipePath.parent), PathValue.name), RecipeValue.SavedAt
    )
    if PureWindowsPath(NativeValue.PathName).name != PathValue.name:
        raise ValueError("host basename cannot introduce native directory components")
    return NativeValue
