from typing import cast as CastValue
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeCommonView import (
    MakeCommonView,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeDistTail import (
    MakeDistTail,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakePoint import (
    MakePoint,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# ordinary feature dimensions retain their verified native text kinds and angle or distance tails instead of mate presentation defaults
def MakeBossView(
    OwnerValue: ArchiveNode,
    HandleValue: ArchiveNode,
    IsAngular: bool,
    DesignIntent: bool,
    SelectedLeader: int,
) -> ArchiveNode:
    if (
        type(CastValue(object, IsAngular)) is not bool
        or HandleValue.FieldsValue.get("owner") is not OwnerValue
    ):
        raise ValueError(
            "boss display must retain its actual dimension owner and explicit kind"
        )
    FieldsValue = MakeCommonView(
        HandleValue, DesignIntent, SelectedLeader, 13 if IsAngular else 2
    )
    if IsAngular:
        FieldsValue.update(
            {
                "f100c": 0,
                "f1010": 1,
                "f1008": 1,
                "ffb8": MakePoint(XValue=1.0),
                "ffd0": MakePoint(YValue=1.0),
                "ffe8": 0.1,
                "fff0": 0.9,
                "fff8": 0.1,
                "f1000": 0.9,
                "f1018": 0x18,
            }
        )
    else:
        FieldsValue.update(MakeDistTail())
    FieldsValue["owner"] = OwnerValue
    return ArchiveNode(
        RuntimeClass(
            "moDisplayAngularDim_c" if IsAngular else "moDisplayDistanceDim_c", 1
        ),
        FieldsValue,
    )
