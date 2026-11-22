from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# evaluated point coordinates are insufficient when unrepresented equations or expression owners can drive different geometry
def CheckPrismRels(RootValue: ArchiveNode) -> None:
    Fields = RequireNative(RootValue.FieldsValue.get("f9d0"), "moRelMgr_c").FieldsValue
    if any(
        not IsLineState(Fields.get(FieldName))
        for FieldName in ("f58", "f10", "fa0", "f1c0")
    ):
        raise ValueError("cache free prism has unqualified model relations")
    if Fields.get("f170") != "" or any(
        Fields.get(FieldName) != 0 for FieldName in ("f178", "f180", "f150", "n1c0")
    ):
        raise ValueError("cache free prism has expressions or authored relation state")
