from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Models.SnapshotModel import SnapshotModel
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.PrismSnapshot import (
    PrismSnapshot,
)


@MakeDataClass(frozen=True, slots=True)
class DocumentSnap:
    Name: str
    Snapshot: SnapshotModel | PrismSnapshot
