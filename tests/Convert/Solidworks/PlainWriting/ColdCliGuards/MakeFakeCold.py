from dataclasses import replace as CopyData

from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Adapter import KSourceFormatKey
from interchange.document.Models.DocumentModel import CadDocument
from tests.Convert.Solidworks.PlainWriting.MeasurePlainDoc import MeasurePlainDoc


# native looking markers cannot qualify an authored neutral graph lacking exact cold ownership
def MakeFakeCold(Document: CadDocument, RoleName: str) -> CadDocument:
    Neutral, _, _ = MeasurePlainDoc(RoleName)
    return CopyData(
        Neutral,
        source=CopyData(Document.source, sha256="0" * 64, attributes={}),
        bodies=(CopyData(Neutral.bodies[0], id=Document.bodies[0].id),),
        brep=Document.brep,
        metadata={**Neutral.metadata, KSourceFormatKey: KPartFormatId},
    )
