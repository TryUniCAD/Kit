from collections.abc import Mapping
from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckCutModes import (
    CheckCutModes,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadCutBodyLink import (
    ReadCutBodyLink,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude


# the portable cut depends on its actual sketch and the producer bound through solid body ownership
def ReadCutHistory(
    Model: NativeModel,
    LinkValue: NativeLink,
    Features: Mapping[int, ArchiveNode],
    OwnersValue: Mapping[int, ExtrudeOwner],
) -> tuple[ExtrudeOwner, dict[str, object]]:
    if any(
        not Report.get("completed")
        or Report.get("missing_schemas")
        or Report.get("provisional_schemas")
        for Report in (
            LinkValue.ConfigValue.ReportValue,
            LinkValue.ResolvedValue.ReportValue,
        )
    ):
        raise ValueError("typed blind pocket requires complete linked archive grammar")
    if (
        len(Model.configurations) != 1
        or len(Model.operations) != 2
        or len(OwnersValue) != 1
    ):
        raise ValueError(
            "multiple operation histories are outside typed blind topology"
        )
    BossOperation, CutOperation = Model.operations
    BossValue = OwnersValue.get(BossOperation.object_id)
    if BossValue is None or (BossOperation.kind, CutOperation.kind) != ("join", "cut"):
        raise ValueError(
            "typed blind pocket requires the ordered boss and cut operations"
        )
    CutValue = ReadExtrude(
        LinkValue, Features[CutOperation.object_id], Features, IsCut=True
    )
    CheckCutModes(BossValue, CutValue)
    HistoryIds = (
        NativeNodeId(BossValue.ProfileValue),
        BossOperation.object_id,
        NativeNodeId(CutValue.ProfileValue),
        CutOperation.object_id,
    )
    if tuple(Value for Value in Features if Value in HistoryIds) != HistoryIds:
        raise ValueError(
            "typed blind pocket requires two distinct ordered profile roots"
        )
    BodyEvidence = ReadCutBodyLink(LinkValue, Features, BossValue, CutValue)
    return (
        ReplaceValue(
            CutValue, ParentsValue=(BossValue.NodeValue, CutValue.ProfileValue)
        ),
        BodyEvidence,
    )
