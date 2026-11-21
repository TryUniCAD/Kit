from convert.adapters.solidworks.Archive.Construction.Blind.BlindZeroFields import (
    KBlindZeroFields,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BodyNameGraph import (
    BodyNameGraph,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadOutputAtom import (
    ReadOutputAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismBoss import (
    CheckFirstBoss,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismEnd import (
    CheckPrismDims,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.Saved.CheckThinMarks import (
    CheckThinMarks as CheckRollback,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Thin.Saved.CheckThinState import (
    CheckThinState as CheckOutputState,
)


# saved forward blind ends retain the active depth with only empty reference arrays
def CheckSavedEnd(OwnerValue: ExtrudeOwner) -> None:
    Fields = OwnerValue.EndValue.FieldsValue
    Present = {"has_f28", "has_f48"}
    if (
        Fields.get("f08") != 1
        or Fields.get("f128") != 1
        or any(
            Fields.get(NameValue) != int(NameValue in Present)
            for NameValue in KBlindZeroFields
        )
        or any(
            not IsLineState(Fields.get(NameValue))
            for NameValue in ("f28", "f48", "fe0", "f100")
        )
        or any(Fields.get(NameValue) is not None for NameValue in ("f138", "f90"))
        or Fields.get("fa0") != 0.0
        or RequireNative(Fields.get("f140"), "moFromEndSpec_c").FieldsValue != {"t": 0}
    ):
        raise ValueError("SOLIDWORKS saved first boss has alternate end state")
    CheckPrismDims(OwnerValue, IsSaved=True)


# live stock identity must come from the one saved output and both actual rollback owners
def CheckSavedBoss(OwnerValue: ExtrudeOwner, GraphValue: BodyNameGraph) -> None:
    CheckFirstBoss(OwnerValue)
    CheckSavedEnd(OwnerValue)
    BossValue = OwnerValue.NodeValue
    Fields = BossValue.FieldsValue
    if (
        Fields.get("f28") != 0xC0000140
        or Fields.get("f810") != -1
        or Fields.get("f838") != 0.0
        or Fields.get("f7a0") != 0
        or any(
            not IsLineState(Fields.get(NameValue))
            for NameValue in ("f368", "f388", "f780")
        )
        or any(
            Fields.get(NameValue) is not None
            for NameValue in ("f538", "f548", "f530", "f6e0", "f758")
        )
        or ReadOutputAtom(BossValue) is not GraphValue.AtomValue
    ):
        raise ValueError(
            "SOLIDWORKS saved first boss has selected or alternate body state"
        )
    LinkValue = GraphValue.LinkValue
    if GraphValue.MarksValue is None or not any(
        EntryValue.EntryValue is GraphValue.AtomValue
        for EntryValue in LinkValue.ConfigValue.MapValue.EntriesValue
    ):
        raise ValueError(
            "SOLIDWORKS saved first boss has no actual inherited atom or rollback"
        )
    RootValue = LinkValue.ConfigValue.RootValue
    CheckOutputState(BossValue, RootValue, GraphValue.AtomValue)
    CheckRollback(RootValue, BossValue, GraphValue.MarksValue)
