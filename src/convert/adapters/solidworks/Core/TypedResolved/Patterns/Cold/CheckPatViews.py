from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the measured annotation list can coexist with cold geometry once its local catalog aliases agree
def CheckPatViews(LinkValue: NativeLink) -> None:
    Fields = LinkValue.ConfigValue.RootValue.FieldsValue
    Catalog = RequireNative(Fields.get("fa48"), "suObList")
    ViewsValue = tuple(
        RequireNative(RowValue.get("o"), "moAnnotationView_c")
        for RowValue in NativeRows(Catalog.FieldsValue.get("items"))
    )
    CheckTreeAlias(LinkValue, (Catalog, *ViewsValue))
    ViewNames = {Value.FieldsValue.get("f358") for Value in ViewsValue}
    ViewIds = {Value.FieldsValue.get("f360") for Value in ViewsValue}
    if (
        Catalog.FieldsValue.get("n") != 2
        or len(ViewsValue) != 2
        or ViewNames != {"*Front", "*Back"}
        or len(ViewIds) != 2
        or any(type(Identity) is not int or Identity <= 199 for Identity in ViewIds)
        or Fields.get("feb0") not in ViewIds
        or Fields.get("feb4") != 199
        or Fields.get("nec8") != 1
        or tuple(RowValue.get("v") for RowValue in NativeRows(Fields.get("fec0")))
        != (199,)
    ):
        raise ValueError("unqualified annotation owner in cache free pattern")
