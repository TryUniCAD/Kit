from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Attributes.CylAttrDef import (
    CylAttrDef,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Attributes.CylAttrIn import (
    CylAttrIn,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# untransmitted pointer fields remain allocated independently of serialized integer and unicode lists
def MakeCylValues(
    InputValue: CylAttrIn,
    SpecValue: CylAttrDef,
    FirstIndex: int,
) -> tuple[tuple[int, ...], tuple[XmtNode, ...]]:
    Pointers: list[int] = []
    NodesValue: list[XmtNode] = []
    for KindValue, ValuesValue in zip(
        SpecValue.FieldKinds, InputValue.ValuesValue, strict=True
    ):
        if ValuesValue is None:
            Pointers.append(0)
        else:
            if KindValue not in (1, 10) or not ValuesValue:
                raise ValueError(
                    "concentric attribute has an unsupported resident value"
                )
            IndexValue = FirstIndex + len(NodesValue)
            Pointers.append(IndexValue)
            NodesValue.append(
                XmtNode(
                    IndexValue,
                    82 if KindValue == 1 else 98,
                    {
                        "values": ValuesValue,
                    },
                )
            )
    return tuple(Pointers), tuple(NodesValue)
