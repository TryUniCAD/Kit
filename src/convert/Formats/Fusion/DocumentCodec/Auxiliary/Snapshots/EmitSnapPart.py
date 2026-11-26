from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.EmitPrismSnap import (
    EmitPrismSnap,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.PrismSnapshot import (
    PrismSnapshot,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Snapshots.EmitTypedSnap import (
    EmitTypedSnap,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Snapshots.SnapshotName import (
    SnapshotName,
)
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSnap import DocumentSnap


# the snapshot part operation needs a consistent construction rule so supporting records retain their owning document relationships
def EmitSnapPart(Value: DocumentSnap) -> ContainerPart:
    SnapshotName(Value.Name)
    Snapshot = Value.Snapshot
    if isinstance(Snapshot, GeometryState):
        return ContainerPart(Value.Name, EmitGeometry(Snapshot))
    if isinstance(Snapshot, PrismSnapshot):
        return ContainerPart(Value.Name, EmitPrismSnap(Snapshot))
    return ContainerPart(Value.Name, EmitTypedSnap(Snapshot))
