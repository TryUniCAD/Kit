from convert.formats.Fusion.ContainerCodec.EmitContainer import EmitContainer
from convert.formats.Fusion.ContainerCodec.Model.FusionContainer import FusionContainer
from convert.formats.Fusion.DocumentCodec.EmitBodyPart import EmitBodyPart
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Records.EmitDocSegment import EmitDocSegment


def EmitParsed(Value: DocumentModel) -> bytes:
    Streams = tuple(EmitDocSegment(Segment) for Segment in Value.Segments)
    Parts = tuple(EmitBodyPart(BodyValue) for BodyValue in Value.Bodies)
    Container = FusionContainer(
        Value.Document, Value.Asset, Streams, Value.Previews, Parts, Value.EmptyFolders
    )
    return EmitContainer(Container)
