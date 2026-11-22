from dataclasses import replace as ReplaceValue

from interchange.document.Models.DocumentModel import CadDocument


# the existing boss composer must validate every other semantic before the real authored name is represented explicitly
def PlainBodyView(DocumentValue: CadDocument) -> CadDocument:
    BodyValue = DocumentValue.bodies[0]
    return ReplaceValue(
        DocumentValue,
        bodies=(ReplaceValue(BodyValue, name=DocumentValue.feature_timeline[0].name),),
    )
