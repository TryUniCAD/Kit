from convert.adapters.solidworks.Archive.Maps.MapEntry import MapEntry
from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
from convert.adapters.solidworks.Archive.Maps.PutEntryMut import PutEntryMut
from convert.adapters.solidworks.Archive.Objects.ExternalClass import ExternalClass
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# classes and objects share one counter across inherited archive graph state
class ArchiveMaps:

    # each stream needs independent membership while seeded nodes retain their identity
    def __init__(self, BaseValue: int, SeedValue: MapSnapshot | None = None) -> None:
        if SeedValue is None:
            SeedValue = MapSnapshot(BaseValue, ())
        if type(SeedValue) is not MapSnapshot or type(BaseValue) is not int:
            raise TypeError("archive map seed and base have invalid types")
        if BaseValue != SeedValue.CounterValue:
            raise ValueError("archive map seed counter differs from the stream base")
        self.BaseValue = BaseValue
        self.CounterValue = SeedValue.CounterValue
        self.EntryMap: dict[int, MapEntry] = {}
        self.ClassLookup: dict[RuntimeClass | ExternalClass, int] = {}
        self.ObjectLookup: dict[int, int] = {}
        for EntryValue in SeedValue.EntriesValue:
            PutEntryMut(self, EntryValue)

    # membership snapshots must not borrow a later stream counter or map mutation
    def Snapshot(self) -> MapSnapshot:
        return MapSnapshot(self.CounterValue, tuple(self.EntryMap.values()))
