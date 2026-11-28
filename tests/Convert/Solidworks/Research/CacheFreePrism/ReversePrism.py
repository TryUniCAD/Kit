from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# a valid typed reversed end remains outside this reconstruction profile and must preserve the previous strict payload failure
def ReversePrism(BytesValue: bytes) -> bytes:
    Archive = SldprtArchive.from_bytes(BytesValue)
    LinkValue = ReadNativeLink(Archive, 0)
    Features = IndexFeatures(LinkValue)
    (BossValue,) = (
        NodeValue
        for NodeValue in Features.values()
        if NodeValue.ClassValue.NameValue == "moExtrusion_c"
    )
    EndValue = RequireNative(BossValue.FieldsValue.get("f818"), "moEndSpec_c")
    EndValue.FieldsValue["f8c"] = 1
    ResolvedValue, _ = WriteResolMut(
        LinkValue.ResolvedValue.RootsValue,
        LinkValue.ResolvedValue.ExtraFields,
        19000,
        LinkValue.ConfigValue.MapValue,
        LinkValue.ResolvedValue.ContextValue,
    )
    StreamsValue = Archive.streams
    StreamsValue[LinkValue.StreamName] = ResolvedValue
    return BuildSldprt(StreamsValue, FormatVersion=4)
