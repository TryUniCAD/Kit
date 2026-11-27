from dataclasses import replace as CopyData

from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.Convert.Integration.Fusion.DualSnapshots.MutateSnapNode import MutateSnapNode
from tests.Convert.Integration.Fusion.DualSnapshots.SwapSnapBodies import SwapSnapBodies


# encoded full native documents must expose incorrect identity attribution and body correspondences
def MakeBadSnap(DataValue: bytes, ModeName: str) -> bytes:
    Model = ReadDocument(DataValue)
    State = Model.Snapshots[0].Snapshot
    assert isinstance(State, GeometryState)
    if ModeName == "body":
        State = SwapSnapBodies(State)
    else:
        Entities = list(State.Entities)
        for Identity, Entity in enumerate(Entities):
            Changed = MutateSnapNode(Entity, ModeName)
            if Changed is not None:
                Entities[Identity] = Changed
                break
        else:
            raise ValueError("Counterexample did not select an owned snapshot record")
        State = CopyData(State, Entities=tuple(Entities))
    return EmitParsed(
        CopyData(Model, Snapshots=(CopyData(Model.Snapshots[0], Snapshot=State),))
    )
