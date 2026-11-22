from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.RevolveOwner import (
    RevolveOwner,
)


# the cold selector identifies a real earlier stock without claiming an atom for the unbuilt result
@Dataclass(frozen=True, slots=True)
class ColdRevOwners:
    LinkValue: NativeLink
    StockValues: tuple[RevolveOwner, RevolveOwner]
    CutValue: RevolveOwner
    AtomIds: tuple[int, int]
    SelectedIndex: int
    WrapperValue: ArchiveNode
