from convert.formats.Fusion.ContainerCodec.EmitContainer import EmitContainer
from convert.formats.Fusion.DocumentCodec.Auxiliary.Configuration.CheckDocConfig import (
    CheckDocConfig,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Configuration.EmitConfigPart import (
    EmitConfigPart,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Snapshots.EmitSnapPart import (
    EmitSnapPart,
)
from convert.formats.Fusion.ContainerCodec.Model.FusionContainer import FusionContainer
from convert.formats.Fusion.DocumentCodec.EmitBodyPart import EmitBodyPart
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Reading.EmitMatPart import EmitMatPart
from convert.formats.Fusion.DocumentCodec.Reading.Materials.CheckDocMats import (
    CheckDocMats,
)
from convert.formats.Fusion.DocumentCodec.Records.EmitDocSegment import EmitDocSegment


def EmitParsed(Value: DocumentModel) -> bytes:
    CheckDocMats(Value)
    CheckDocConfig(Value)
    Streams = tuple(EmitDocSegment(Segment) for Segment in Value.Segments)
    Parts = (
        tuple(EmitBodyPart(BodyValue) for BodyValue in Value.Bodies)
        + tuple(EmitMatPart(Material) for Material in Value.Materials)
        + tuple(EmitSnapPart(Snapshot) for Snapshot in Value.Snapshots)
        + tuple(EmitConfigPart(Configuration) for Configuration in Value.Configurations)
    )
    Container = FusionContainer(
        Value.Document, Value.Asset, Streams, Value.Previews, Parts, Value.EmptyFolders
    )
    return EmitContainer(Container)
