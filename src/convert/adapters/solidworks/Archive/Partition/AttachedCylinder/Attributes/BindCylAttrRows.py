from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Attributes.CylAttrDefs import (
    KCylAttrDefs,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Attributes.CylAttrIn import (
    CylAttrIn,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Attributes.CylAttrRows import (
    CylAttrRows,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Attributes.MakeCylValues import (
    MakeCylValues,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# each new attribute links to the preceding owner and type independently
def BindCylAttrRows(
    InputsValue: tuple[CylAttrIn, ...],
    Definitions: dict[str, int],
    FirstIndex: int,
    FirstEntity: int,
) -> CylAttrRows:
    RowsValue: list[XmtNode] = []
    ByIndex: dict[int, dict[str, object]] = {}
    OwnerHeads: dict[int, int] = {}
    TypeHeads: dict[str, int] = {}
    HiddenCount = 0
    EntityId = FirstEntity
    for InputValue in InputsValue:
        NameValue = InputValue.NameValue
        SpecValue = KCylAttrDefs[NameValue]
        OwnerIndex = InputValue.OwnerValue.IndexValue
        IndexValue = FirstIndex + len(RowsValue)
        PreviousOwner = OwnerHeads.get(OwnerIndex, 0)
        PreviousType = TypeHeads.get(NameValue, 0)
        Pointers, Values = MakeCylValues(InputValue, SpecValue, IndexValue + 1)
        EntityId += 1
        FieldsValue: dict[str, object] = {
            "node_id": EntityId,
            "definition": Definitions[NameValue],
            "owner": OwnerIndex,
            "next": PreviousOwner,
            "previous": 0,
            "next_of_type": PreviousType,
            "previous_of_type": 0,
            "fields": Pointers,
        }
        if PreviousOwner:
            ByIndex[PreviousOwner]["previous"] = IndexValue
        if PreviousType:
            ByIndex[PreviousType]["previous_of_type"] = IndexValue
        OwnerHeads[OwnerIndex] = TypeHeads[NameValue] = IndexValue
        ByIndex[IndexValue] = FieldsValue
        RowsValue.extend((XmtNode(IndexValue, 81, FieldsValue), *Values))
        HiddenCount += SpecValue.FieldKinds.count(9)
    return CylAttrRows(tuple(RowsValue), OwnerHeads, TypeHeads, HiddenCount)
