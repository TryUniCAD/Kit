from dataclasses import replace as ReplaceValue
from collections.abc import Sequence

from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Core.Partition.ActivePartition import ActivePartition
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.ShellCache import (
    ShellCache,
)
from interchange import BrepPayload


# saved results retain their exact partition while synthetic geometry has no native payload
def BindShellCache(
    CacheValue: ShellCache,
    Payloads: Sequence[BrepPayload],
    BodyId: str,
    *,
    IncludeBrep: bool,
) -> ActivePartition:
    if not IncludeBrep:
        return ActivePartition(None, None)
    PayloadId: str | None = None
    if CacheValue.DigestValue is None:
        if Payloads:
            raise ValueError("fresh shell has unexpected native geometry payloads")
    else:
        (Payload,) = tuple(
            Value
            for Value in Payloads
            if Value.source_stream == KPartitionStream and Value.kind == "partition"
        )
        if Payload.sha256 != CacheValue.DigestValue:
            raise ValueError(
                "SOLIDWORKS shell public payload differs from the typed active body"
            )
        PayloadId = Payload.id
    (BodyValue,) = CacheValue.BodyValue.bodies
    ModelValue = ReplaceValue(
        CacheValue.BodyValue, bodies=(ReplaceValue(BodyValue, design_body_id=BodyId),)
    )
    return ActivePartition(ModelValue, PayloadId)
