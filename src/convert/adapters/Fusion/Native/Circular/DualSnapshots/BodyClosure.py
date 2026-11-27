from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)


# rooted reachability must preserve ownership while excluding only separately validated live body bookkeeping
def BodyClosure(
    State: GeometryState, RootId: int, IgnoreBody: bool = False
) -> tuple[int, ...]:
    if not 0 <= RootId < len(State.Entities) or not isinstance(
        State.Entities[RootId], BodyNode
    ):
        raise ValueError("Dual snapshot closure requires an actual body root")
    Result = [RootId]
    for Identity in Result:
        Record = MakeEntityNode(State.Entities[Identity])
        for Ordinal, (TagValue, Field) in enumerate(Record.Tokens):
            if IgnoreBody and Identity == RootId and Ordinal == 0:
                continue
            if TagValue == 12 and isinstance(Field, int) and Field >= 0:
                if Field >= len(State.Entities):
                    raise ValueError(
                        "Dual snapshot body reference leaves its entity table"
                    )
                if Field not in Result:
                    Result.append(Field)
    return tuple(Result)
