from convert.formats.Fusion.BrepCodec.EmitHistory import EmitHistory
from convert.formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Model.DocumentBody import DocumentBody


def EmitBodyPart(Value: DocumentBody) -> ContainerPart:
    History = Value.History
    if History.Header != BrepHeader(23200, 2, 3, 50.0, 1e-6, 1e-10):
        raise ValueError("Unsupported Fusion document BRep header")
    Payload = EmitHistory(
        History.Model,
        History.Identity,
        History.TagSet,
        History.History,
        History.Stamp,
        History.Vertices,
    )
    return ContainerPart(Value.PartName, Payload)
