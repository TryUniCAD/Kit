from dataclasses import replace as CopyData
from struct import pack as PackValue

from convert.Formats.Fusion.ContainerCodec.EmitContainer import EmitContainer
from convert.Formats.Fusion.ContainerCodec.ReadContainer import ReadContainer


# a valid container must carry the malformed scalar past the finite only entity encoder
def MakeNonfinite(Payload: bytes) -> bytes:
    Container = ReadContainer(Payload)
    Pattern = PackValue("<d", 1.23456789e123)
    assert sum(Stream.BulkData.count(Pattern) for Stream in Container.Streams) == 1
    Streams = tuple(
        CopyData(
            Stream,
            BulkData=Stream.BulkData.replace(Pattern, PackValue("<d", float("inf"))),
        )
        for Stream in Container.Streams
    )
    return EmitContainer(CopyData(Container, Streams=Streams))
