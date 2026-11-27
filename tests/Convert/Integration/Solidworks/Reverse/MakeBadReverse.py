from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from tests.Convert.Integration.Solidworks.Reverse.LoadReverse import LoadReverse


# malformed full archives must exercise public admission after real linked graph serialization
def MakeBadReverse(ModeName: str) -> bytes:
    Sample = LoadReverse("discoveryTriangleReverse")
    Archive = SldprtArchive.from_bytes(
        Sample.SourcePath.read_bytes(), Sample.SourcePath.name
    )
    LinkValue = ReadNativeLink(Archive, 0)
    Features = IndexFeatures(LinkValue)
    BossValue = next(
        Value
        for Value in Features.values()
        if Value.ClassValue.NameValue == "moExtrusion_c"
    )
    EndValue = RequireNative(BossValue.FieldsValue["f818"], "moEndSpec_c")
    if ModeName == "direction":
        EndValue.FieldsValue["f8c"] = 2
    elif ModeName == "owner":
        EndValue.FieldsValue["f18"] = EndValue.FieldsValue["fc8"]
    elif ModeName == "support":
        Profile = next(
            Value
            for Value in Features.values()
            if Value.ClassValue.NameValue == "moProfileFeature_c"
        )
        Reference = RequireNative(Profile.FieldsValue["pd_f78"], "moCompRefPlane_c")
        Reference.FieldsValue["f100"] = 1
    else:
        raise ValueError("unknown malformed reverse fixture")
    ConfigBytes, ConfigValue = WriteConfigMut(
        LinkValue.ConfigValue.RootValue, 19000, LinkValue.ConfigValue.HeaderValue
    )
    ResolvedBytes, _ = WriteResolMut(
        LinkValue.ResolvedValue.RootsValue,
        LinkValue.ResolvedValue.ExtraFields,
        19000,
        ConfigValue.MapValue,
        LinkValue.ResolvedValue.ContextValue,
    )
    Streams = dict(Archive.streams)
    Streams["Contents/Config-0"] = ConfigBytes
    Streams["Contents/Config-0-ResolvedFeatures"] = ResolvedBytes
    return BuildSldprt(Streams, FormatVersion=4)
