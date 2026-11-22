from dataclasses import replace as CopyData
from pathlib import Path as FilePath
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)


# a saved carrier can move without changing loop vertices or normal direction
def MakeOffsetPlane(Source: FilePath, Target: FilePath) -> None:
    Model = ReadDocument(Source.read_bytes())
    Snapshot = Model.Snapshots[0].Snapshot
    if not isinstance(Snapshot, GeometryState):
        raise ValueError("Plane replay requires a typed cache snapshot")
    Entities = list(Snapshot.Entities)
    for Index, Entity in enumerate(Entities):
        if not isinstance(Entity, PlaneNode):
            continue
        Entities[Index] = CopyData(
            Entity,
            OriginCm=tuple(
                Point + Normal
                for Point, Normal in zip(Entity.OriginCm, Entity.Normal, strict=True)
            ),
        )
        _ = Target.write_bytes(
            EmitParsed(
                CopyData(
                    Model,
                    Snapshots=(
                        CopyData(
                            Model.Snapshots[0],
                            Snapshot=CopyData(Snapshot, Entities=tuple(Entities)),
                        ),
                    ),
                )
            )
        )
        return
    raise ValueError("Plane replay has no saved planar carrier")
