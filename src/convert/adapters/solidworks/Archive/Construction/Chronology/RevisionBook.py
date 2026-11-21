from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Chronology.RevisionLog import (
    RevisionLog,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# source attribution tables retain semantic names while event indices are derived at construction
@DataClass(frozen=True, slots=True)
class RevisionBook:
    UsersValue: tuple[str, ...]
    CompaniesValue: tuple[str, ...]
    LogsValue: tuple[RevisionLog, ...]

    # ambiguous attribution or unrepresented events must fail before a partial header is constructed
    def __post_init__(self) -> None:
        for TableValue in (self.UsersValue, self.CompaniesValue):
            if type(TableValue) is not tuple or not 0 < len(TableValue) <= 0x10000:
                raise ValueError(
                    "revision attribution requires an ordered nonempty table"
                )
            for TextValue in TableValue:
                _ = ReadStyleText(TextValue, "revision attribution")
            if len(set(TableValue)) != len(TableValue):
                raise ValueError("revision attribution names must be unambiguous")
        if (
            type(self.LogsValue) is not tuple
            or not self.LogsValue
            or any(type(LogValue) is not RevisionLog for LogValue in self.LogsValue)
        ):
            raise ValueError("revision book requires actual ordered log intentions")
        for LogValue in self.LogsValue:
            for EventValue in LogValue.EventsValue:
                if (
                    EventValue.UserName not in self.UsersValue
                    or EventValue.CompanyName not in self.CompaniesValue
                ):
                    raise ValueError(
                        "revision event attribution has no actual table owner"
                    )
