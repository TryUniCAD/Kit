from convert.adapters.solidworks.Archive.Construction.Geometry.IdentityXform import (
    IdentityXform,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatAnnoBases import (
    KPatAnnoBack,
    KPatAnnoTop,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import (
    KNoAnno,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.MakeAnnoView import (
    MakeAnnoFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# matching names alone cannot validate independent origin frames and their catalog identities
def CheckTopViews(ViewsValue: tuple[ArchiveNode, ...]) -> None:
    for ViewIdx, (ViewValue, BasisValue) in enumerate(
        zip(ViewsValue, (KPatAnnoTop, KPatAnnoBack), strict=True), KNoAnno + 1
    ):
        Fields = ViewValue.FieldsValue
        if (
            Fields.get("f360") != ViewIdx
            or Fields.get("f368") != MakeAnnoFrame(BasisValue)
            or Fields.get("f370") != IdentityXform()
            or Fields.get("n380") != 0
            or Fields.get("f3d0") is not None
            or Fields.get("f3e8") is not None
            or Fields.get("f2f0") is not None
        ):
            raise ValueError("unqualified canonical annotation frame in cold pattern")


# the measured annotation list can coexist with cold geometry once its local catalog aliases agree
def CheckPatViews(LinkValue: NativeLink) -> None:
    Fields = LinkValue.ConfigValue.RootValue.FieldsValue
    Catalog = RequireNative(Fields.get("fa48"), "suObList")
    ViewsValue = tuple(
        RequireNative(RowValue.get("o"), "moAnnotationView_c")
        for RowValue in NativeRows(Catalog.FieldsValue.get("items"))
    )
    CheckTreeAlias(LinkValue, (Catalog, *ViewsValue))
    ViewNames = tuple(Value.FieldsValue.get("f358") for Value in ViewsValue)
    ViewIds = {Value.FieldsValue.get("f360") for Value in ViewsValue}
    IsTopBack = ViewNames == ("*Top", "*Back")
    if (
        Catalog.FieldsValue.get("n") != 2
        or len(ViewsValue) != 2
        or (not IsTopBack and set(ViewNames) != {"*Front", "*Back"})
        or len(ViewIds) != 2
        or any(type(Identity) is not int or Identity <= KNoAnno for Identity in ViewIds)
        or Fields.get("feb0") not in ViewIds
        or Fields.get("feb4") != KNoAnno
        or Fields.get("nec8") != 1
        or tuple(RowValue.get("v") for RowValue in NativeRows(Fields.get("fec0")))
        != (KNoAnno,)
    ):
        raise ValueError("unqualified annotation owner in cache free pattern")
    if IsTopBack:
        CheckTopViews(ViewsValue)
        if Fields.get("feb0") != KNoAnno + len(ViewsValue):
            raise ValueError(
                "unqualified canonical annotation frontier in cold pattern"
            )
