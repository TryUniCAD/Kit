from dataclasses import replace as ReplaceValue
from collections.abc import Sequence

from convert.adapters.solidworks.Core.Partition.ActivePartition import ActivePartition
from convert.adapters.solidworks.Core.TypedResolved.Shells.Cache.ShellCache import (
    ShellCache,
)
from interchange import BrepPayload


# the retained active payload must still be the specific verified configuration body
def BindShellCache(
    CacheValue: ShellCache, Payloads: Sequence[BrepPayload], BodyId: str
) -> ActivePartition:
    if not Payloads:
        return ActivePartition(None, None)
    (Payload,) = tuple(
        Value
        for Value in Payloads
        if Value.source_stream == "Contents/Config-0-Partition"
        and Value.kind == "partition"
    )
    if Payload.sha256 != CacheValue.DigestValue:
        raise ValueError(
            "SOLIDWORKS shell public payload differs from the typed active body"
        )
    (BodyValue,) = CacheValue.BodyValue.bodies
    ModelValue = ReplaceValue(
        CacheValue.BodyValue, bodies=(ReplaceValue(BodyValue, design_body_id=BodyId),)
    )
    return ActivePartition(ModelValue, Payload.id)
