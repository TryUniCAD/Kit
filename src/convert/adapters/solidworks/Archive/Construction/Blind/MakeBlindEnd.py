from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Blind.BlindEndInput import (
    BlindEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Blind.BlindEndRefs import (
    BlindEndRefs,
)
from convert.adapters.solidworks.Archive.Construction.Blind.BossEndInput import (
    BossEndInput,
)
from convert.adapters.solidworks.Archive.Construction.Blind.CheckBlindRefs import (
    CheckBlindRefs,
)
from convert.adapters.solidworks.Archive.Construction.Blind.EndInput import KEndInput
from convert.adapters.solidworks.Archive.Construction.Blind.MakeEndSpec import (
    MakeEndSpec,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# the native blind end owner must be generated from rules and retained graph references without saved fields
def MakeBlindEnd(InputValue: KEndInput, RefsValue: BlindEndRefs) -> ArchiveNode:
    if (
        type(CastValue(object, InputValue)) not in (BlindEndInput, BossEndInput)
        or type(CastValue(object, RefsValue)) is not BlindEndRefs
    ):
        raise TypeError(
            "blind end construction requires validated input and reference records"
        )
    CheckBlindRefs(InputValue, RefsValue)
    ModeValue = InputValue.ModeValue if type(InputValue) is BossEndInput else "blind"
    return MakeEndSpec(
        ModeValue,
        InputValue.IsReversed,
        RefsValue.ForwardValue,
        RefsValue.ReverseValue,
        RefsValue.ForwardDraft,
        RefsValue.ReverseDraft,
        RefsValue.FromEndValue,
    )
