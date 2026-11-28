from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# an explicit source index has its own title epoch and material label apart from the part archive
@DataClass(frozen=True, slots=True)
class ImportKeyInput:
    TitleValue: str
    SavedAt: int
    MaterialValue: str | None

    # scoped native metadata requires a real title and validates any supplied material label
    def __post_init__(self) -> None:
        if (
            not ReadStyleText(self.TitleValue, "import keyword title").strip()
            or self.MaterialValue is not None
            and not ReadStyleText(
                self.MaterialValue, "import keyword material label"
            ).strip()
        ):
            raise ValueError("native import keyword labels must be nonempty")
        if type(self.SavedAt) is not int or not 0 <= self.SavedAt <= 0xFFFFFFFF:
            raise ValueError(
                "native import keyword timestamp must fit unsigned seconds"
            )
