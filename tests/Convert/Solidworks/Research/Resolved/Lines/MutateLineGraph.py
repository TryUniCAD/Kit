from pathlib import Path as FilePath

from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import (
    SldprtArchive,
    build_sldprt as BuildArchive,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from tests.Convert.Solidworks.Research.Resolved.Lines.ApplyLineMut import ApplyLineMut


# complete generated archives must preserve legacy semantics when typed endpoint ownership or plain scope is unqualified
def MutateLineGraph(InputPath: FilePath, ModeValue: str) -> FilePath:
    Archive = SldprtArchive.from_bytes(InputPath.read_bytes())
    LinkValue = ReadNativeLink(Archive, 0)
    Profile = next(
        NodeValue
        for NodeValue in IndexFeatures(LinkValue).values()
        if NodeValue.ClassValue.NameValue == "moProfileFeature_c"
    )
    SketchValue = RequireNative(Profile.FieldsValue["pd_f80"], "sgSketch")
    FieldsValue = SketchValue.FieldsValue
    ApplyLineMut(FieldsValue, ModeValue)
    Streams = dict(Archive.streams)
    Streams[LinkValue.StreamName], _ = WriteResolMut(
        LinkValue.ResolvedValue.RootsValue,
        LinkValue.ResolvedValue.ExtraFields,
        19000,
        LinkValue.ConfigValue.MapValue,
        LinkValue.ResolvedValue.ContextValue,
    )
    OutputPath = InputPath.with_stem(ModeValue)
    with OutputPath.open("xb") as Output:
        _ = Output.write(BuildArchive(Streams))
    return OutputPath
