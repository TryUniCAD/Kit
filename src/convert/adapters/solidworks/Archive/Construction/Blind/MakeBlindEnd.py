from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Blind.BlindEndInput import (
    BlindEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Blind.BlindEndRefs import (
    BlindEndRefs,
)
from convert.adapters.solidworks.Archive.Construction.Blind.BlindZeroFields import (
    KBlindZeroFields,
)
from convert.adapters.solidworks.Archive.Construction.Blind.CheckBlindRefs import (
    CheckBlindRefs,
)
from convert.adapters.solidworks.Archive.Construction.Blind.EmptyEndArray import (
    EmptyEndArray,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the native blind end owner must be generated from rules and retained graph references without saved fields
def MakeBlindEnd(InputValue: BlindEndInput, RefsValue: BlindEndRefs) -> ArchiveNode:
    if (
        type(CastValue(object, InputValue)) is not BlindEndInput
        or type(CastValue(object, RefsValue)) is not BlindEndRefs
    ):
        raise TypeError(
            "blind end construction requires validated input and reference records"
        )
    CheckBlindRefs(InputValue, RefsValue)
    FieldsValue: dict[str, object] = {FieldName: 0 for FieldName in KBlindZeroFields}
    FieldsValue.update(
        {
            "f138": None,
            "f08": 1,
            "f8c": int(InputValue.IsReversed),
            "f90": None,
            "f18": RefsValue.ForwardValue,
            "f20": RefsValue.ReverseValue,
            "fa0": 0.0,
            "fc8": RefsValue.ForwardDraft,
            "fd0": RefsValue.ReverseDraft,
            "fe0": EmptyEndArray(),
            "f100": EmptyEndArray(),
            "f128": 1,
            "f140": RefsValue.FromEndValue,
        }
    )
    return ArchiveNode(RuntimeClass("moEndSpec_c", 1), FieldsValue)
