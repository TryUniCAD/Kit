from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# independently authored test archives exercise both physical cut directions through the full public reader
def MakeThroughCutArchive(Payload: bytes, Reverse: bool, Both: bool) -> bytes:
    Archive = SldprtArchive.from_bytes(Payload)
    LinkValue = ReadNativeLink(Archive, 0)
    Features = IndexFeatures(LinkValue)
    (Boss,) = (
        Node
        for Node in Features.values()
        if Node.ClassValue.NameValue == "moExtrusion_c"
    )
    (Cut,) = (
        Node for Node in Features.values() if Node.ClassValue.NameValue == "moICE_c"
    )
    RequireNative(Boss.FieldsValue["f818"], "moEndSpec_c").FieldsValue["f0c"] = 6
    End = RequireNative(Cut.FieldsValue["f818"], "moEndSpec_c").FieldsValue
    End.update(f08=int(not Both), f0c=1, f10=int(Both), f8c=int(Reverse))
    for NameValue in ("f18", "f20", "fc8", "fd0"):
        End[NameValue] = None
    Streams = dict(Archive.streams)
    Streams[LinkValue.StreamName], _ = WriteResolMut(
        LinkValue.ResolvedValue.RootsValue,
        LinkValue.ResolvedValue.ExtraFields,
        19000,
        LinkValue.ConfigValue.MapValue,
        LinkValue.ResolvedValue.ContextValue,
    )
    return BuildSldprt(Streams, FormatVersion=4)
