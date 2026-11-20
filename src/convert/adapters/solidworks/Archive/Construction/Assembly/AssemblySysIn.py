from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Construction.Assembly.System.AsmVocabulary import (
    KAsmFolders,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTime import (
    FeatureTime,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import (
    LightInput,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.NotesInput import (
    NotesInput,
)


# ordinary assembly system labels must be explicit while native folder allocation and principal plane order remain independently documented rules
@DataClass(frozen=True, slots=True)
class AssemblySysIn:
    FolderNames: tuple[tuple[str, str], ...]
    PlaneNames: tuple[tuple[str, str], ...]
    CabinetName: str
    OriginName: str
    MateGroupName: str
    CreatedAt: int
    LightValues: tuple[LightInput, ...] = ()
    NotesValue: NotesInput | None = None

    # incomplete or ambiguous names must reject before any native persistent feature identifier can be consumed
    def __post_init__(self) -> None:
        for RowsValue, Expected in (
            (self.FolderNames, set(KAsmFolders)),
            (self.PlaneNames, {"x", "y", "z"}),
        ):
            if type(RowsValue) is not tuple or any(
                type(RowValue) is not tuple or len(RowValue) != 2
                for RowValue in RowsValue
            ):
                raise TypeError(
                    "assembly system names require ordered class and text pairs"
                )
            if (
                len(RowsValue) != len(Expected)
                or {RowValue[0] for RowValue in RowsValue} != Expected
            ):
                raise ValueError(
                    "assembly system names do not cover the classified native roles"
                )
        NamesValue = tuple(
            RowValue[1] for RowValue in self.FolderNames + self.PlaneNames
        ) + (self.CabinetName, self.OriginName, self.MateGroupName)
        if any(
            not ReadStyleText(NameValue, "assembly system name")
            for NameValue in NamesValue
        ) or len(set(NamesValue)) != len(NamesValue):
            raise ValueError(
                "assembly system feature names must be distinct nonempty authored text"
            )
        if type(self.LightValues) is not tuple or any(
            type(LightValue) is not LightInput for LightValue in self.LightValues
        ):
            raise TypeError("assembly lighting requires ordered typed light inputs")
        LightNames = {LightValue.NameValue for LightValue in self.LightValues}
        if len(LightNames) != len(self.LightValues) or LightNames.intersection(
            NamesValue
        ):
            raise ValueError("assembly light names must be distinct system captions")
        if self.NotesValue is not None:
            if type(self.NotesValue) is not NotesInput:
                raise TypeError("assembly notes require typed empty pair input")
            if not {self.NotesValue.HeadName, self.NotesValue.EndName}.isdisjoint(
                (*NamesValue, *LightNames)
            ):
                raise ValueError("assembly note captions must be distinct system names")
        _ = FeatureTime(self.CreatedAt)
