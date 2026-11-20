from convert.adapters.solidworks.Archive.Construction.BodyScope.MakeStockAtom import (
    MakeStockAtom,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
)


# stock output and manager membership must share one generated atom in the independent atom identity domain
def BindStockMut(
    ManagerValue: dict[str, object],
    FeatureValue: ArchiveNode,
    *,
    AppendMember: bool = False,
) -> ArchiveNode:
    PriorRows = ReadRows(ManagerValue.get("atoms")) if AppendMember else ()
    if AppendMember and len(PriorRows) != FieldInt(ManagerValue, "n6c"):
        raise ValueError("stock atom count differs from its ordered manager members")
    AtomValue = MakeStockAtom(FeatureValue, FieldInt(ManagerValue, "f260") + 1)
    AtomId = FieldInt(AtomValue.FieldsValue, "f140")
    MembersValue = [{"o": AtomValue}]
    ManagerRows = [*PriorRows, *MembersValue]
    ManagerValue.update(f260=AtomId, n6c=len(ManagerRows), atoms=ManagerRows)
    FeatureValue.FieldsValue.update(
        has_f528=1,
        f528={"n": len(MembersValue), "items": MembersValue.copy()},
        n494=len(MembersValue),
        f498=[{"v": AtomId}],
    )
    return AtomValue
