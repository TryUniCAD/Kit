from dataclasses import dataclass as DataClass
from ntpath import (
    isabs as IsAbsolute,
    splitdrive as SplitDrive,
    splitext as SplitExt,
    basename as BaseName,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Container.Format import KAsmSuffix, KPartSuffix


# generated native identity must use an explicit absolute target path and save event without resolving or reading any filesystem state
@DataClass(frozen=True, slots=True)
class SelfFileInput:
    PathName: str
    SavedAt: int
    IsAssembly: bool = False

    # malformed target identity must fail before a header can publish a relative mismatched or untruthful reference
    def __post_init__(self) -> None:
        if (
            not ReadStyleText(self.PathName, "native self path")
            or not IsAbsolute(self.PathName)
            or not SplitDrive(self.PathName)[0]
        ):
            raise ValueError(
                "native self identity requires an explicit absolute windows target path"
            )
        NameValue, Extension = SplitExt(BaseName(self.PathName))
        Expected = KAsmSuffix if self.IsAssembly else KPartSuffix
        if not NameValue or Extension.casefold() != Expected:
            raise ValueError(
                "native self path extension must match its SOLIDWORKS model kind"
            )
        if type(self.SavedAt) is not int or not 0 <= self.SavedAt <= 0xFFFFFFFF:
            raise ValueError("native save event must fit unsigned unix seconds")
