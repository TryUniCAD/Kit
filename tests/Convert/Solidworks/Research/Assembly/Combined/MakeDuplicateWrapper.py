from pathlib import Path as FilePath

from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    ReadRows,
    RequireNode,
)
from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


# malformed integration data must duplicate an assembly identity without changing either local endpoint ordinal
def DuplicateWrap(SourcePath: FilePath, TargetPath: FilePath) -> None:
    Archive = SldprtArchive.from_bytes(SourcePath.read_bytes())
    Linked = ReadNativeLink(Archive, 0)
    Stream = "Contents/Config-0-MatesList"
    Graph = ReadMatesMut(Archive.require(Stream), Linked.ResolvedValue)
    First, Second = Graph.RootsValue[:2]
    FirstRef, SecondRef = (
        RequireNode(
            ReadRows(MateValue.FieldsValue.get("f410"))[0].get("o"), "moPlaneRef_w"
        )
        for MateValue in (First, Second)
    )
    SecondRef.FieldsValue["f78"] = FirstRef.FieldsValue["f78"]
    Content, _ = WriteMatesMut(Graph.RootsValue, Linked.ResolvedValue)
    Streams = dict(Archive.streams)
    Streams[Stream] = Content
    _ = TargetPath.write_bytes(build_sldprt(Streams))
