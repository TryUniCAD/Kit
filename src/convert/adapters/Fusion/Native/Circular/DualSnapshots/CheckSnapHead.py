from dataclasses import replace as CopyData

from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.CheckGeometry import (
    CheckGeometry,
)
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)


# absent snapshot identities and matching framing must be checked before normalizing the live solid graph
def CheckSnapHead(State: GeometryState, LiveState: GeometryState) -> None:
    CheckGeometry(State)
    if (
        CopyData(State.Header, RootCount=2) != LiveState.Header
        or State.Header.RootCount != 4
        or State.Stamp != LiveState.Stamp
        or State.Entities[0] != LiveState.Entities[0]
    ):
        raise ValueError("Dual snapshot framing disagrees with its live body")
    for Entity in State.Entities:
        Record = MakeEntityNode(Entity)
        if not Record.Name.startswith("ATTRIB_") and Record.Tokens[1][1] != -1:
            raise ValueError("Dual snapshot has an unsupported saved entity identity")
