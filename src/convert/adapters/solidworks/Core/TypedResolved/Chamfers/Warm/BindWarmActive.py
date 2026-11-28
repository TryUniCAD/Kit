from collections.abc import Sequence
from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Core.Partition.ActivePartition import ActivePartition
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.Warm.WarmChmfBody import (
    WarmChmfBody,
)
from interchange.Payloads.PayloadRecord import BrepPayload


# neutral body ownership must remain attached to the exact decoded active frame
def BindWarmActive(
    Proof: WarmChmfBody,
    Payloads: Sequence[BrepPayload],
    BodyId: str,
) -> ActivePartition:
    (Source,) = (
        Value
        for Value in Payloads
        if Value.source_stream == KPartitionStream and Value.kind == "partition"
    )
    if Source.sha256 != Proof.PayloadHash:
        raise ValueError(
            "saved chamfer active payload differs from the linked native proof"
        )
    (BodyValue,) = Proof.BrepValue.bodies
    ModelValue = ReplaceValue(
        Proof.BrepValue, bodies=(ReplaceValue(BodyValue, design_body_id=BodyId),)
    )
    return ActivePartition(ModelValue, Source.id)
