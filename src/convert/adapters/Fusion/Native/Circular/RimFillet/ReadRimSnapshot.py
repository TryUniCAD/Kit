from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry
from convert.Formats.Fusion.BrepCodec.Models.SnapshotModel import SnapshotModel
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Snapshots.EmitTypedSnap import (
    EmitTypedSnap,
)
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel


# both complete typed snapshot representations must preserve every source owned field and framing value
def ReadRimSnapshot(Model: DocumentModel) -> GeometryState:
    if len(Model.Snapshots) != 1:
        raise ValueError("Native rim requires exactly one saved snapshot")
    Snapshot = Model.Snapshots[0].Snapshot
    if isinstance(Snapshot, GeometryState):
        return Snapshot
    if isinstance(Snapshot, SnapshotModel):
        return ReadGeometry(EmitTypedSnap(Snapshot))
    raise ValueError("Native rim snapshot has an unqualified representation")
