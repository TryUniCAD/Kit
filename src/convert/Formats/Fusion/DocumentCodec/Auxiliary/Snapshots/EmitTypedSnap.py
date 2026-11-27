from dataclasses import replace as ReplaceData

from convert.Formats.Fusion.BrepCodec.EmitSnapshot import EmitSnapshot
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry
from convert.Formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.Formats.Fusion.BrepCodec.Models.SnapshotModel import SnapshotModel


# typed cylinder snapshots must retain their validated integer width through the existing wire serializer
def EmitTypedSnap(Snapshot: SnapshotModel) -> bytes:
    Header = Snapshot.Header
    if Header.IntWidth not in (4, 8) or Header != BrepHeader(
        23200, 4, 2, 10.0, 1e-6, 1e-10, Header.IntWidth
    ):
        raise ValueError("Unsupported Fusion snapshot header")
    Payload = EmitSnapshot(
        Snapshot.Model, Snapshot.TagSet, Snapshot.Stamp, Snapshot.Vertices
    )
    if Header.IntWidth == 8:
        return Payload
    Geometry = ReadGeometry(Payload)
    return EmitGeometry(ReplaceData(Geometry, Header=Header))
