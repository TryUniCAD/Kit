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
from convert.adapters.solidworks.Container.Format import (
    KAsmSuffix,
    KPartSuffix,
)


# generated native identity must use an explicit absolute target path and save event without resolving or reading any filesystem state
@DataClass(frozen=True, slots=True)
class SelfFileInput:
    PathName: str
    SavedAt: int

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
        if not NameValue or Extension.casefold() not in (
            KPartSuffix,
            KAsmSuffix,
            ".slddrw",
        ):
            raise ValueError(
                "native self path must identify a part assembly or drawing"
            )
        if type(self.SavedAt) is not int or not 0 <= self.SavedAt <= 0xFFFFFFFF:
            raise ValueError("native save event must fit unsigned unix seconds")
