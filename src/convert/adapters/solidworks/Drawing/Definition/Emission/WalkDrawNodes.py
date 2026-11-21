from collections.abc import Mapping, Sequence
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# whole graph admission must inspect aliases and cycles without serializing or reading a file
def WalkDrawNodes(RootValue: ArchiveNode) -> tuple[ArchiveNode, ...]:
    Pending: list[object] = [RootValue]
    Visited: set[int] = set()
    Results: list[ArchiveNode] = []
    while Pending:
        Current = Pending.pop()
        if id(Current) in Visited:
            continue
        Visited.add(id(Current))
        if isinstance(Current, ArchiveNode):
            Results.append(Current)
            Pending.append(Current.FieldsValue)
        elif isinstance(Current, Mapping):
            Pending.extend(CastValue(Mapping[str, object], Current).values())
        elif isinstance(Current, (list, tuple)):
            Pending.extend(CastValue(Sequence[object], Current))
    return tuple(Results)
