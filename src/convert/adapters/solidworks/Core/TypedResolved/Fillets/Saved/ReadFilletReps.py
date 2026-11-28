from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfRows import (
    ChmfRoleKey,
    EdgeChmfRows,
    KChmfRoleKey,
    ReadChmfRef,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.FilletHistory import (
    FilletHistory,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.ReadFilletKeys import (
    ReadFilletKeys,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# historical faces must resolve to the original stock and to the actual local document
def ReadFilletReps(
    History: FilletHistory,
    Reference: ArchiveNode,
    TopHeader: ArchiveNode,
) -> tuple[KChmfRoleKey, ...]:
    LinkValue = History.LinkValue
    RepsValue = EdgeChmfRows(Reference)
    KeysValue = tuple(ChmfRoleKey(Value) for Value in RepsValue)
    if len(KeysValue) != 4 or len(set(KeysValue)) != 4:
        raise ValueError("saved fillet requires its four different stock face roles")
    RefsValue = tuple(
        ReadChmfRef(LinkValue, Value, History.OwnersValue.StockValue, TopHeader, False)
        for Value in RepsValue
    )
    OwnerValue = RequireNative(RefsValue[0].FieldsValue.get("f08"), "moExtObject_c")
    Headers = (LinkValue.ConfigValue.HeaderValue, TopHeader)
    SelfValues = tuple(
        RequireNative(Header.FieldsValue.get("f38"), "moExtObject_c")
        for Header in Headers
    )
    if (
        len(set(RefsValue)) != 4
        or OwnerValue in SelfValues
        or any(Value.FieldsValue.get("f08") is not OwnerValue for Value in RefsValue)
        or any(
            ReadFilletKeys(Value) != ReadFilletKeys(OwnerValue) for Value in SelfValues
        )
    ):
        raise ValueError("saved fillet faces do not own one historical local file")
    CheckTreeAlias(LinkValue, (Reference, OwnerValue))
    return KeysValue
