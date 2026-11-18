from convert.adapters.solidworks.Archive.Construction.BodyScope.MakeStockAtom import (
    MakeStockAtom,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# stock output and manager membership must share one generated atom in the independent atom identity domain
def BindStockMut(
    ManagerValue: dict[str, object], FeatureValue: ArchiveNode
) -> ArchiveNode:
    AtomValue = MakeStockAtom(FeatureValue, FieldInt(ManagerValue, "f260") + 1)
    AtomId = FieldInt(AtomValue.FieldsValue, "f140")
    MembersValue = [{"o": AtomValue}]
    ManagerValue.update(f260=AtomId, n6c=len(MembersValue), atoms=MembersValue)
    FeatureValue.FieldsValue.update(
        has_f528=1,
        f528={"n": len(MembersValue), "items": MembersValue.copy()},
        n494=len(MembersValue),
        f498=[{"v": AtomId}],
    )
    return AtomValue
