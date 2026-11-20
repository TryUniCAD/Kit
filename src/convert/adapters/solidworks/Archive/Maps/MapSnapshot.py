from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Maps.MapEntry import MapEntry

# native map growth reserves the upper boundary before allocating another slot
KCounterLimit = 0x3FFFFFFE


# linked streams need frozen membership while retaining the same object identities
@DataClass(frozen=True, slots=True)
class MapSnapshot:
    CounterValue: int
    EntriesValue: tuple[MapEntry, ...]

    # malformed map seeds would silently renumber every subsequent class and object
    def __post_init__(self) -> None:
        if type(self.CounterValue) is not int or type(self.EntriesValue) is not tuple:
            raise TypeError("archive map snapshot has invalid counter or entry types")
        if not 1 <= self.CounterValue <= KCounterLimit:
            raise ValueError("archive map counter exceeds its native domain")
        IndexValues: set[int] = set()
        for EntryValue in self.EntriesValue:
            if type(EntryValue) is not MapEntry:
                raise TypeError("archive snapshot entries must be typed map entries")
            if EntryValue.IndexValue >= self.CounterValue:
                raise ValueError("archive map slot reaches or exceeds its next counter")
            if EntryValue.IndexValue in IndexValues:
                raise ValueError("archive map snapshot contains a duplicate slot")
            IndexValues.add(EntryValue.IndexValue)
