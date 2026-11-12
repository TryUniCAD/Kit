from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Model.DocumentBody import DocumentBody
from convert.formats.Fusion.DocumentCodec.Model.MaterialPart import MaterialPart
from convert.formats.Fusion.DocumentCodec.ReadBodyPart import ReadBodyPart
from convert.formats.Fusion.DocumentCodec.Reading.ReadMatPart import ReadMatPart


def ReadDocParts(
    Values: tuple[ContainerPart, ...],
) -> tuple[tuple[DocumentBody, ...], tuple[MaterialPart, ...]]:
    Bodies: list[DocumentBody] = []
    Materials: list[MaterialPart] = []
    for Value in Values:
        if Value.Name.startswith("ProteinAssets.BlobParts/"):
            Materials.append(ReadMatPart(Value))
        else:
            Bodies.append(ReadBodyPart(Value))
    return tuple(Bodies), tuple(Materials)
