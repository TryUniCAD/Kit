from convert.formats.Fusion.BrepCodec.ReadSnapshot import ReadSnapshot
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry
from convert.formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.ReadPrismSnap import (
    ReadPrismSnap,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Snapshots.SnapshotName import (
    SnapshotName,
)
from convert.formats.Fusion.DocumentCodec.Model.DocumentSnap import DocumentSnap


def ReadSnapPart(Value: ContainerPart) -> DocumentSnap:
    SnapshotName(Value.Name)
    if (
        type(Value.Payload) is not bytes
        or not 0 < len(Value.Payload) <= 2 * 1024 * 1024
    ):
        raise ValueError("Invalid or oversized Fusion snapshot part")
    Geometry = ReadGeometry(Value.Payload)
    Cones = tuple(Value for Value in Geometry.Entities if isinstance(Value, ConeNode))
    if (
        Geometry.Header.RootCount == 4
        and len(Geometry.Entities) == 59
        and len(Cones) == 1
        and Cones[0].SineAngle == 0
    ):
        return DocumentSnap(Value.Name, ReadSnapshot(Value.Payload))
    if Geometry.Header.RootCount == 4 and len(Geometry.Entities) == 168 and not Cones:
        return DocumentSnap(Value.Name, ReadPrismSnap(Value.Payload))
    return DocumentSnap(Value.Name, Geometry)
