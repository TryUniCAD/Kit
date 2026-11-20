from dataclasses import dataclass as MakeDataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the untouched solid must remain distinguishable from the consumed stock and cut result
@MakeDataClass(frozen=True, slots=True)
class StockCutAtoms:
    SelectedIndex: int
    ConsumedAtom: ArchiveNode
    UntouchedAtom: ArchiveNode
    ResultAtom: ArchiveNode
