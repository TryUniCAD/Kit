from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyOwner import (
    ReadBodyOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadMgrAtom import (
    ReadMgrAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadOutputAtom import (
    ReadOutputAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Fillets.FilletOwners import (
    FilletOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# fillet rollback must restore the one actual preceding producer of the active atom
def ReadFilletOwn(LinkValue: NativeLink) -> FilletOwners:
    RootValue = RequireNative(LinkValue.ConfigValue.RootValue, "moPart_c")
    FilletValues = tuple(
        RequireNative(NodeValue, "Fillet_c")
        for NodeValue in LinkValue.ResolvedValue.RootsValue
        if NodeValue is not None and NodeValue.ClassValue.NameValue == "Fillet_c"
    )
    if len(FilletValues) != 1:
        raise ValueError("SOLIDWORKS fillet history needs one actual fillet root")
    (FilletValue,) = FilletValues
    StockValue = ReadBodyOwner(LinkValue, None)
    AtomValue = ReadMgrAtom(LinkValue)
    Fields = AtomValue.FieldsValue
    if (
        ReadOutputAtom(StockValue) is not AtomValue
        or FilletValue.FieldsValue.get("f538") is not AtomValue
        or Fields.get("f12c") != NativeNodeId(StockValue)
        or Fields.get("f130") != NativeNodeId(FilletValue)
        or Fields.get("f12c") == Fields.get("f130")
        or Fields.get("f18") is not None
        or Fields.get("f18c") != 1
    ):
        raise ValueError("SOLIDWORKS fillet must modify the actual stock atom")
    Controllers = (
        RequireNative(RootValue.FieldsValue.get("fe38"), "moPMarkRecord_c"),
        RequireNative(StockValue.FieldsValue.get("f3d0"), "moPMarkRecord_c"),
        RequireNative(FilletValue.FieldsValue.get("f3d0"), "moPMarkRecord_c"),
    )
    CheckTreeAlias(LinkValue, (StockValue, FilletValue, AtomValue, *Controllers))
    Inherited = LinkValue.ConfigValue.MapValue.EntriesValue
    if any(
        not any(
            EntryValue.IndexValue == OwnerValue.IndexValue
            and EntryValue.EntryValue is OwnerValue
            for EntryValue in Inherited
        )
        for OwnerValue in (AtomValue, Controllers[0])
    ):
        raise ValueError(
            "SOLIDWORKS fillet lost its inherited atom or activation owner"
        )
    if any(set(Controller.FieldsValue) != {"f18"} for Controller in Controllers):
        raise ValueError("SOLIDWORKS fillet controller has alternate mark state")
    return FilletOwners(StockValue, FilletValue, AtomValue, Controllers)
