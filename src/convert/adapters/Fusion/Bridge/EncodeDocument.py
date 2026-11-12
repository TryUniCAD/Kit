from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
from convert.adapters.Fusion.Projection.ProjectNative import ProjectNative
from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange.document.models.DocumentModel import CadDocument


def EncodeDocument(Document: CadDocument) -> bytes:
    Document.AssertValid()
    if set(Document.metadata) == {"fusion.authoring"}:
        SpecValue = CheckContract(Document.metadata["fusion.authoring"], "spec")
        if (
            not isinstance(SpecValue, DocumentSpec)
            or MakeFusionDoc(SpecValue) != Document
        ):
            raise ValueError("Fusion authoring contract and neutral graph disagree")
        return EmitDocument(SpecValue)
    if set(Document.metadata) != {"fusion.native_state"}:
        raise ValueError(
            "Fusion writing requires a qualified authoring or native-state contract"
        )
    ModelValue = CheckContract(Document.metadata["fusion.native_state"], "model")
    if not isinstance(ModelValue, DocumentModel):
        raise ValueError("Fusion native-state contract requires a document model")
    Payload = EmitParsed(ModelValue)
    Decoded = ReadDocument(Payload)
    if Decoded != ModelValue or ProjectNative(Decoded, Document.source) != Document:
        raise ValueError("Fusion native-state contract and neutral graph disagree")
    return Payload
