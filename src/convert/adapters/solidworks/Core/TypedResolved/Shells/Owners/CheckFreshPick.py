from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.ReadChmfRows import (
    KChmfRoleKey,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the separate fresh cap and auxiliary edge must share just one actual file history owner
def CheckFreshPick(
    FaceValue: ArchiveNode, EdgeValue: ArchiveNode, Histories: tuple[ArchiveNode, ...]
) -> None:
    EdgeFields = EdgeValue.FieldsValue
    OwnerFile = Histories[0].FieldsValue["f08"]
    if (
        FaceValue.FieldsValue["f58"] is EdgeFields["f58"]
        or len(set(Histories)) != len(Histories)
        or any(Value.FieldsValue["f08"] is not OwnerFile for Value in Histories)
        or not IsLineState(EdgeFields.get("f130"))
        or any(
            EdgeFields.get(FieldName) != dict.fromkeys("xyz", 0.0)
            for FieldName in ("f158", "f170")
        )
        or any(EdgeFields.get(FieldName) != 0 for FieldName in ("f188", "f18c", "n140"))
    ):
        raise ValueError("fresh shell has alternate clip, point or history ownership")


# the typed fresh auxiliary carriers follow the stored sketch order and carry no selected point
def CheckFreshRoles(
    FaceValue: ArchiveNode,
    EdgeValue: ArchiveNode,
    LoopValue: LineLoop,
    TopKeys: tuple[KChmfRoleKey, ...],
    EdgeKeys: tuple[KChmfRoleKey, ...],
) -> None:
    SideKeys: tuple[KChmfRoleKey, ...] = tuple(
        ("moFromSktEntSurfIdRep_c", Value.PermanentId, None)
        for Value in LoopValue.LinesValue
    )
    First, Second, Third, Closing = SideKeys
    if TopKeys != (
        ("moEndFaceSurfIdRep_c", 1, 0),
        Closing,
        First,
        Second,
        Third,
    ) or EdgeKeys != (Closing, ("moEndFaceSurfIdRep_c", 0, 0), Third, First):
        raise ValueError(
            "fresh shell differs from the ordered stock cap and edge roles"
        )
    for Wrapper in (FaceValue, EdgeValue):
        RefValue = RequireNative(Wrapper.FieldsValue.get("fe8"))
        Fields = RefValue.FieldsValue
        if (
            Fields.get("f70") != 0
            or Fields.get("f48") != 0
            or Fields.get("f28") != 1e100
            or Fields.get("f30") != 1e100
        ):
            raise ValueError("fresh shell has a retained selection qualifier")
