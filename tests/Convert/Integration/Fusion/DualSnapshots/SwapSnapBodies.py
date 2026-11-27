from dataclasses import replace as CopyData

from convert.adapters.Fusion.Native.Circular.DualSnapshots.ReadSnapRoles import (
    ReadSnapRoles,
)
from convert.Formats.Fusion.BrepCodec.Journal.Permutation.RemapEntity import RemapEntity
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)


# swapping complete roots without their passive ids creates a structurally valid ownership counterexample
def SwapSnapBodies(State: GeometryState) -> GeometryState:
    Roles = dict((RoleName, Identity) for Identity, RoleName in ReadSnapRoles(State))
    FirstId, SecondId = Roles["profile"], Roles["sketch"]
    OrderValue = list(range(len(State.Entities)))
    OrderValue[FirstId], OrderValue[SecondId] = SecondId, FirstId
    Mapping = tuple(OrderValue.index(Identity) for Identity in range(len(OrderValue)))
    return CopyData(
        State,
        Entities=tuple(
            RemapEntity(State.Entities[Identity], Mapping) for Identity in OrderValue
        ),
    )
