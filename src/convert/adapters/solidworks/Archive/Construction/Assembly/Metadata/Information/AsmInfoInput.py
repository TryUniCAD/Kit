from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.CheckPropText import (
    CheckPropText,
)


# core creation and save attribution can differ from binary header provenance and need independent authored ownership
@DataClass(frozen=True, slots=True)
class AsmInfoInput:
    CreatedAt: int
    SaveActor: str
    OffsetMinutes: int
    LocaleName: str

    # publication dates must use explicit supported preferences without consulting the host locale or clock
    def __post_init__(self) -> None:
        _ = CheckPropText(self.SaveActor)
        if type(self.CreatedAt) is not int or not 0 < self.CreatedAt <= 0xFFFFFFFF:
            raise ValueError(
                "assembly information requires a positive core creation event"
            )
        if (
            self.LocaleName != "en-US"
            or type(self.OffsetMinutes) is not int
            or not -720 <= self.OffsetMinutes <= 840
        ):
            raise ValueError(
                "assembly information needs explicit U.S. English local clock ownership"
            )
