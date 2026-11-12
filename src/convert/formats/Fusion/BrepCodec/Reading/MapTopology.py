from collections import deque as MakeQueue

from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmPtr
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord, AsmTable


def MapTopology(Expected: tuple[AsmRecord, ...], Actual: AsmTable) -> dict[int, int]:
    if len(Expected) != len(Actual.Records):
        raise ValueError("Unsupported Fusion BRep entity count")
    Mapping = {Index: Index for Index in range(Actual.RootCount)}
    Reverse = dict(Mapping)
    Pending = MakeQueue(Mapping.items())
    while Pending:
        ExpectedId, ActualId = Pending.popleft()
        Left, Right = Expected[ExpectedId], Actual.Records[ActualId]
        IsAttribute = Left.Name == "ATTRIB_CUSTOM-attrib"
        Count = 5 if IsAttribute else len(Left.Tokens)
        if Left.Name != Right.Name or (
            len(Right.Tokens) < Count if IsAttribute else len(Right.Tokens) != Count
        ):
            raise ValueError("Unsupported Fusion BRep topology record")
        for Index in range(Count):
            if Left.Tokens[Index][0] != Right.Tokens[Index][0]:
                raise ValueError("Fusion BRep topology field type disagrees")
            if Left.Tokens[Index][0] != 12:
                continue
            ExpectedRef, ActualRef = ReadAsmPtr(Left, Index), ReadAsmPtr(Right, Index)
            if ExpectedRef == -1 or ActualRef == -1:
                if ExpectedRef != ActualRef:
                    raise ValueError("Fusion BRep topology null link disagrees")
                continue
            if not 0 <= ActualRef < len(Actual.Records):
                raise ValueError("Fusion BRep topology link leaves the entity table")
            if ExpectedRef in Mapping:
                if Mapping[ExpectedRef] != ActualRef:
                    raise ValueError("Fusion BRep topology link disagrees")
            else:
                if ActualRef in Reverse:
                    raise ValueError("Fusion BRep topology aliases distinct entities")
                Mapping[ExpectedRef] = ActualRef
                Reverse[ActualRef] = ExpectedRef
                Pending.append((ExpectedRef, ActualRef))
    if len(Mapping) != len(Expected):
        raise ValueError("Unreachable Fusion BRep entity")
    return Mapping
