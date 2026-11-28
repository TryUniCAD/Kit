from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.adapters.Fusion.Native.Graph.SelectExtrusion import SelectExtrusion
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from tests.Convert.Api.Fusion.Native.ChangeNative import ChangeField
from tests.Convert.Api.Fusion.SavedMaterials.AddMapRows import AddMapRows


# an actual archive with a body owned design mapping isolates material prepare from graphics admission
def GenMappedBody(Payload: bytes) -> bytes:
    Model = ReadDocument(Payload)
    assert Model.Graphics is None
    BodyNode = SelectExtrusion(BuildGraph(Model)).BodyNode
    assert BodyNode.Fields["textureMapping"] is None
    (Design,) = tuple(
        Value for Value in Model.Segments if Value.Metadata.Header.SegmentId == 0
    )
    Changed, MappingId = AddMapRows(Design)
    Segments = tuple(Changed if Value is Design else Value for Value in Model.Segments)
    Owned = ChangeField(
        ReplaceData(Model, Segments=Segments),
        BodyNode.ObjectId,
        "textureMapping",
        LocalRef(MappingId),
    )
    return EmitParsed(Owned)
