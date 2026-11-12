from convert.formats.Fusion.BrepCodec.ReadSnapshot import ReadSnapshot
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.ReadPrismSnap import (
    ReadPrismSnap,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Snapshots.SnapshotName import (
    SnapshotName,
)
from convert.formats.Fusion.DocumentCodec.Model.DocumentSnap import DocumentSnap
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmTable


def ReadSnapPart(Value: ContainerPart) -> DocumentSnap:
    SnapshotName(Value.Name)
    if (
        type(Value.Payload) is not bytes
        or not 0 < len(Value.Payload) <= 2 * 1024 * 1024
    ):
        raise ValueError("Invalid or oversized Fusion snapshot part")
    Table = ReadAsmTable(Value.Payload)
    if Table.RootCount != 4:
        raise ValueError("Unsupported Fusion snapshot body count")
    if len(Table.Records) == 59:
        return DocumentSnap(Value.Name, ReadSnapshot(Value.Payload))
    if len(Table.Records) == 168:
        return DocumentSnap(Value.Name, ReadPrismSnap(Value.Payload))
    raise ValueError("Unsupported Fusion snapshot topology profile")
