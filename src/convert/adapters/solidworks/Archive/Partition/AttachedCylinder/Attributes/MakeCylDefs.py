from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Attributes.CylAttrDefs import (
    KCylAttrDefs,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# definition chains run backwards from the last newly registered type
def MakeCylDefs(
    NamesValue: tuple[str, ...],
    FirstIndex: int,
) -> tuple[XmtNode, ...]:
    RowsValue: list[XmtNode] = []
    PriorIndex = 0
    for NameValue in NamesValue:
        SpecValue = KCylAttrDefs[NameValue]
        IndexValue = FirstIndex + len(RowsValue)
        RowsValue.extend(
            (
                XmtNode(
                    IndexValue,
                    80,
                    {
                        "next": PriorIndex,
                        "identifier": IndexValue + 1,
                        "type_id": 9000,
                        "actions": SpecValue.ActionsValue,
                        "field_names": 0,
                        "legal_owners": tuple(
                            int(Position in SpecValue.OwnerSlots)
                            for Position in range(17)
                        ),
                        "fields": SpecValue.FieldKinds,
                    },
                ),
                XmtNode(IndexValue + 1, 79, {"string": NameValue}),
            )
        )
        PriorIndex = IndexValue
    return tuple(RowsValue)
