from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from interchange.geometry.Models.Transform import Transform


# reconstruction must retain the linked provisional owners without assuming a saved result
@DataClass(frozen=True, slots=True)
class ColdStockOwners:
    LinkValue: NativeLink
    StockValues: tuple[ExtrudeOwner, ExtrudeOwner]
    CutValue: ExtrudeOwner
    ProfileFrames: tuple[Transform, Transform, Transform]
    SelectedIndex: int
    SelectedAtomId: int
    StockAtoms: tuple[ArchiveNode, ArchiveNode]
    WrapperValue: ArchiveNode
