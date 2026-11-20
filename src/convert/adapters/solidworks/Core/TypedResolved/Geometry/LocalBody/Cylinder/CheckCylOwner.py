from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Native import NativeFeature
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.Local.ReadLocalOwner import (
    ReadLocalOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# a periodic capsule needs physical feature atom and rollback ownership before projection
def CheckCylOwner(
    Archive: SldprtArchive,
    OwnerValue: NativeFeature,
    GroupKey: str,
    MarkValue: int,
    PriorMark: int,
) -> None:
    LinkValue = ReadNativeLink(Archive, 0)
    AtomValue, FeatureId = ReadLocalOwner(LinkValue, GroupKey, MarkValue)
    FeatureValue = next(
        RequireNative(NodeValue, "moBaseBody_c")
        for NodeValue in LinkValue.ResolvedValue.RootsValue
        if isinstance(NodeValue, ArchiveNode)
        and NodeValue.ClassValue.NameValue == "moBaseBody_c"
    )
    ModelValue = RequireNative(LinkValue.ConfigValue.RootValue, "moPart_c")
    Activation = RequireNative(ModelValue.FieldsValue.get("fe38"), "moPMarkRecord_c")
    OffsetValue = OwnerValue.native_offset
    if (
        AtomValue.FieldsValue.get("f180") != 0
        or OwnerValue.object_id != FeatureId
        or OwnerValue.native_stream != LinkValue.StreamName
        or OffsetValue is None
        or FeatureValue.StartOffset is None
        or FeatureValue.EndOffset is None
        or not FeatureValue.StartOffset <= OffsetValue < FeatureValue.EndOffset
    ):
        raise ValueError("local cylinder has a foreign feature or marked atom")
    if (
        ModelValue.FieldsValue.get("f1010") != 1
        or not 0 < PriorMark < MarkValue
        or Activation.FieldsValue.get("f18") != PriorMark
    ):
        raise ValueError(
            "local cylinder activation does not own the rollback predecessor"
        )
