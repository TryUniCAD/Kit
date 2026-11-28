from pathlib import Path as FilePath

from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import (
    SldprtArchive,
    build_sldprt as BuildArchive,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from tests.Convert.Solidworks.Research.Resolved.LineDimensions.ApplyRectMut import (
    ApplyRectMut,
)


# malformed and alternative structural encodings must cross complete archive serialization before normal public reading
def MutateRectGraph(InputPath: FilePath, ModeValue: str) -> FilePath:
    Archive = SldprtArchive.from_bytes(InputPath.read_bytes())
    LinkValue = ReadNativeLink(Archive, 0)
    FeaturesValue = tuple(IndexFeatures(LinkValue).values())
    Profile = next(
        NodeValue
        for NodeValue in FeaturesValue
        if NodeValue.ClassValue.NameValue == "moProfileFeature_c"
    )
    OriginValue = next(
        NodeValue
        for NodeValue in FeaturesValue
        if NodeValue.ClassValue.NameValue == "moOriginProfileFeature_c"
    )
    SketchValue = RequireNative(Profile.FieldsValue["pd_f80"], "sgSketch")
    StreamsValue = dict(Archive.streams)
    ApplyRectMut(
        SketchValue,
        RequireNative(OriginValue.FieldsValue["pd_f80"], "sgSketch"),
        StreamsValue,
        ModeValue,
    )
    StreamsValue[LinkValue.StreamName], _ = WriteResolMut(
        LinkValue.ResolvedValue.RootsValue,
        LinkValue.ResolvedValue.ExtraFields,
        19000,
        LinkValue.ConfigValue.MapValue,
        LinkValue.ResolvedValue.ContextValue,
    )
    OutputPath = InputPath.with_stem(ModeValue)
    with OutputPath.open("xb") as Output:
        _ = Output.write(BuildArchive(StreamsValue))
    return OutputPath
