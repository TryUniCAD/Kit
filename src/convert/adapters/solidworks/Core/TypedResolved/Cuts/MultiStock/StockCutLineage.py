from dataclasses import dataclass as MakeDataClass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.StockCutAtoms import (
    StockCutAtoms,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from interchange.geometry.Models.Transform import Transform


# lineage retains actual graph identities for future timeline and body binding
@MakeDataClass(frozen=True, slots=True)
class StockCutLineage:
    StockValues: tuple[ExtrudeOwner, ExtrudeOwner]
    CutValue: ExtrudeOwner
    AtomsValue: StockCutAtoms
    WrapperValue: ArchiveNode
    ProfileFrames: tuple[Transform, Transform, Transform]
