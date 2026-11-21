from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadOutputAtom import (
    ReadOutputAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# real output objects and reciprocal ids must agree before a cache free body can inherit a name
def ReadColdBoss(LinkValue: NativeLink, AtomValue: ArchiveNode) -> ArchiveNode:
    BossValues = tuple(
        NodeValue
        for NodeValue in LinkValue.ResolvedValue.RootsValue
        if NodeValue is not None and NodeValue.ClassValue.NameValue == "moExtrusion_c"
    )
    if len(BossValues) != 1 or ReadOutputAtom(BossValues[0]) is not AtomValue:
        raise ValueError("cold name lacks its actual unique producing boss")
    BossValue = BossValues[0]
    FeatureId = NativeNodeId(BossValue)
    if any(
        AtomValue.FieldsValue.get(NameValue) != FeatureId
        for NameValue in ("f12c", "f130")
    ):
        raise ValueError("cold atom base and last modifier are not the actual boss")
    RowsValue = NativeRows(BossValue.FieldsValue.get("f498"))
    if (
        BossValue.FieldsValue.get("n494") != 1
        or len(RowsValue) != 1
        or RowsValue[0].get("v") != AtomValue.FieldsValue["f140"]
    ):
        raise ValueError("cold output ids disagree with the actual manager atom")
    return BossValue
