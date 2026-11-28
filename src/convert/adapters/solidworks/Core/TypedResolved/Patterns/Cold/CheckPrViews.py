from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KHingeRoot,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Direction.ReadPatFrame import (
    ReadPatPoint,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatAnnoBases import (
    KPatAnnoLeft,
    KPatAnnoTop,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import (
    AnnoViewInput,
    KNoAnno,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.MakeAnnoView import (
    KAnnoWorld,
    MakeAnnoView,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.Patterns.PatternDim import (
    PatternDim,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# each principal mode owns distinct physical registered views and an unassigned active state
def CheckPrViews(
    LinkValue: NativeLink, Drivers: tuple[PatternDim, ...], Reversed: bool
) -> None:
    RootFields = LinkValue.ConfigValue.RootValue.FieldsValue
    Catalog = RequireNative(RootFields.get("fa48"), "suObList")
    Views = tuple(
        RequireNative(RowValue.get("o"), "moAnnotationView_c")
        for RowValue in NativeRows(Catalog.FieldsValue.get("items"))
    )
    CheckTreeAlias(LinkValue, (Catalog, *Views))
    TopView = AnnoViewInput("*Top", KPatAnnoTop)
    FrontView = AnnoViewInput("*Front", KAnnoWorld)
    Inputs = (
        (TopView, AnnoViewInput("*Left", KPatAnnoLeft), FrontView)
        if Reversed
        else (TopView, FrontView)
    )
    if (
        len(Views) != len(Inputs)
        or Catalog.FieldsValue.get("n") != len(Views)
        or RootFields.get("feb0") != KNoAnno + len(Views)
        or RootFields.get("feb4") != KNoAnno
        or RootFields.get("nec8") != 1
        or tuple(NativeRows(RootFields.get("fec0"))) != ({"v": KNoAnno},)
        or RootFields.get("fd44")
        != FieldInt(Drivers[0].DisplayValue.FieldsValue, "f58") + 1
    ):
        raise ValueError(
            "cache free principal pattern requires its own annotation register"
        )
    for ViewValue, Intent, Index in zip(
        Views, Inputs, range(KNoAnno + 1, KNoAnno + 1 + len(Views)), strict=True
    ):
        Fields = ViewValue.FieldsValue
        Actual = {**Fields, "f380": NativeRows(Fields.get("f380"))}
        Expected = {**MakeAnnoView(Intent, Index).FieldsValue, "f3e8#0": None}
        if Actual != Expected:
            raise ValueError(
                "cache free principal pattern requires its canonical annotation frame"
            )
    CheckPrMembers(Drivers, KNoAnno + len(Views), KNoAnno + (2 if Reversed else 1))


# actual live display memberships must point at the verified views while inactive owners stay unassigned
def CheckPrMembers(Drivers: tuple[PatternDim, ...], CountId: int, PitchId: int) -> None:
    Contents = (CountId, PitchId, None, None, None, None)
    for Driver, ViewId in zip(Drivers, Contents, strict=True):
        Fields = Driver.DisplayValue.FieldsValue
        Members = () if ViewId is None else ({"v": ViewId},)
        TextFields = NativeRecord(Fields.get("f6a0"))
        Label = ReadPatPoint(TextFields.get("f38"))
        if (
            Fields.get("n2b0") != len(Members)
            or NativeRows(Fields.get("f2b0")) != Members
            or Label[2] != 0.0
            or any(abs(Value) >= 1e3 for Value in Label)
            or Driver.NativeName == "D3"
            and Label != KHingeRoot
        ):
            raise ValueError(
                "cache free principal pattern has a foreign display view or label"
            )
    if Drivers[0].DisplayValue.FieldsValue.get("fad0") != Drivers[0].LiveValue:
        raise ValueError(
            "cache free principal pattern has a separate count display value"
        )
