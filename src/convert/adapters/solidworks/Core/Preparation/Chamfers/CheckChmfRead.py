from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.Chamfers.ChmfSnapMeta import (
    KChmfSnapshot,
    ReadChmfSnap,
)
from convert.adapters.solidworks.Core.Preparation.Chamfers.ReadChmfSelf import (
    ReadChmfSelf,
)
from convert.adapters.solidworks.Core.Preparation.Chamfers.StripChmfSnap import (
    StripChmfSnap,
)
from convert.adapters.solidworks.Core.Preparation.Readback.CheckColdRead import (
    CheckColdRead,
)
from convert.adapters.solidworks.Core.Preparation.Readback.ReadColdDoc import (
    ReadColdDoc,
)
from interchange.document.Behavior.DocumentIo import ToJson
from interchange.document.Models.DocumentModel import CadDocument


# a byte free snapshot must reproduce every canonical row before it may publish again
def CheckChmfRead(Document: CadDocument, Payload: bytes) -> None:
    if KChmfSnapshot not in Document.metadata:
        CheckColdRead(Document, Payload)
        return
    Recipe = ReadChmfSelf(SldprtArchive.from_bytes(Payload))
    if ReadChmfSnap(Document) != Recipe:
        raise ValueError("cold chamfer JSON recipe differs from its regenerated part")
    Expected = ReadColdDoc(Document.source.path, Payload)
    if Expected.brep is None or ToJson(Document, IndentSize=None) != ToJson(
        StripChmfSnap(Expected, Recipe), IndentSize=None
    ):
        raise ValueError("cold chamfer JSON readback differs from its regenerated part")
