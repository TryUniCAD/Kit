from convert.adapters.Fusion.Native.Circular.DualSnapshots.BodyClosure import (
    BodyClosure,
)
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord, KAsmToken


# saved solid correspondence must retain every carrier seam and attribute after reference ordinal normalization
def CanonicalBody(State: GeometryState, RootId: int) -> tuple[AsmRecord, ...]:
    OrderValue = BodyClosure(State, RootId, True)
    Positions = {Identity: Index for Index, Identity in enumerate(OrderValue)}
    Result: list[AsmRecord] = []
    for Identity in OrderValue:
        Record = MakeEntityNode(State.Entities[Identity])
        Fields: list[KAsmToken] = []
        for Ordinal, (TagValue, Field) in enumerate(Record.Tokens):
            if Identity == RootId and Ordinal == 0:
                Field = -1
            elif Ordinal == 1 and not Record.Name.startswith("ATTRIB_"):
                Field = -1
            elif TagValue == 12 and isinstance(Field, int) and Field >= 0:
                Field = Positions[Field]
            Fields.append((TagValue, Field))
        Result.append(AsmRecord(Record.Name, tuple(Fields)))
    return tuple(Result)
