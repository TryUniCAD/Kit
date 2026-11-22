from dataclasses import dataclass as DataClass
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTime import (
    FeatureTime,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Archive.Construction.System.SystemClasses import (
    KSystemFolders,
)


# system graph names ordering plane selection and creation epoch must be explicit authored inputs before allocation begins
@DataClass(frozen=True, slots=True)
class SystemInput:
    FolderValues: tuple[tuple[str, str], ...]
    PlaneNames: tuple[tuple[str, str], ...]
    CabinetName: str
    OriginName: str
    OriginAxis: str
    CreatedAt: int
    PlaneFlags: bool

    # exact input validation prevents unsupported folder variants or ambiguous geometry from silently entering the selected fresh part profile
    def __post_init__(self) -> None:
        if (
            type(self.FolderValues) is not tuple
            or len(self.FolderValues) != 12
            or any(
                type(RowValue) is not tuple or len(RowValue) != 2
                for RowValue in self.FolderValues
            )
        ):
            raise ValueError(
                "fresh system folders require twelve explicit class and name pairs"
            )
        if {RowValue[0] for RowValue in self.FolderValues} != set(KSystemFolders):
            raise ValueError(
                "system folder inputs do not cover the classified fresh part profile"
            )
        if (
            type(self.PlaneNames) is not tuple
            or len(self.PlaneNames) != 3
            or any(
                type(RowValue) is not tuple or len(RowValue) != 2
                for RowValue in self.PlaneNames
            )
        ):
            raise ValueError("principal planes require explicit axis and name pairs")
        if {RowValue[0] for RowValue in self.PlaneNames} != {
            "x",
            "y",
            "z",
        } or self.OriginAxis not in ("x", "y", "z"):
            raise ValueError(
                "principal planes and origin support require canonical positive axes"
            )
        NamesValue = tuple(
            RowValue[1] for RowValue in self.FolderValues + self.PlaneNames
        ) + (self.CabinetName, self.OriginName)
        if any(
            not ReadStyleText(NameValue, "system feature name")
            for NameValue in NamesValue
        ) or len(set(NamesValue)) != len(NamesValue):
            raise ValueError(
                "system feature names must be distinct nonempty authored text"
            )
        if type(self.PlaneFlags) is not bool:
            raise TypeError("plane construction flags require an explicit boolean")
        _ = FeatureTime(self.CreatedAt)
