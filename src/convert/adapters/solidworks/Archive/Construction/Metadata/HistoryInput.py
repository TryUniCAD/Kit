from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# history provenance must be authored explicitly and never impersonate a vendor save or infer build and license facts from geometry
@DataClass(frozen=True, slots=True)
class HistoryInput:
    CreatedAt: int
    CommentText: str
    BuildCode: int
    LicenseOrigin: int
    LanguageId: int
    CjkSaved: bool

    # unsupported provenance domains must fail before any metadata graph can be emitted as a truthful fresh history
    def __post_init__(self) -> None:
        if type(self.CreatedAt) is not int or not 0 <= self.CreatedAt <= 0xFFFFFFFF:
            raise ValueError("history creation time must fit unsigned unix seconds")
        _ = ReadStyleText(self.CommentText, "history comment")
        if type(self.BuildCode) is not int or not 1 <= self.BuildCode <= 0xFFFFFF:
            raise ValueError(
                "history requires explicit nonnative low twenty four bit build provenance"
            )
        if type(self.LicenseOrigin) is not int or self.LicenseOrigin not in (
            0,
            10,
            20,
            30,
            40,
            50,
        ):
            raise ValueError(
                "history license provenance is outside recovered categories"
            )
        if (
            type(self.LanguageId) is not int
            or not 0 <= self.LanguageId <= 0xFFFF
            or type(self.CjkSaved) is not bool
        ):
            raise ValueError(
                "history language and saved state must use explicit native domains"
            )
        if self.LanguageId & 0x3FF in (4, 17, 18) and not self.CjkSaved:
            raise ValueError(
                "history language requires its truthful cjk saved provenance"
            )
