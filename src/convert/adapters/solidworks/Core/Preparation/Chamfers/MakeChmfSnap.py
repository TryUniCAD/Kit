from hashlib import sha256 as CalcSha
from io import BytesIO

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Adapter import KSourceBytesKey
from convert.adapters.solidworks.Core.Preparation.Chamfers.ChmfSnapMeta import (
    KChmfSnapshot,
    ReadChmfSnap,
)
from convert.adapters.solidworks.Core.Preparation.Chamfers.IsDistChmf import IsDistChmf
from convert.adapters.solidworks.Core.Preparation.Chamfers.PrepChmfPart import (
    PrepChmfPart,
)
from convert.adapters.solidworks.Core.Preparation.Chamfers.ReadChmfSelf import (
    ReadChmfSelf,
)
from convert.adapters.solidworks.Core.Preparation.Chamfers.StripChmfSnap import (
    StripChmfSnap,
)
from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import IsColdRead
from interchange.document.Models.DocumentModel import CadDocument


# candidate selection is only a dispatch hint and confers no authority to pass native rows
def IsChmfSnapDoc(Document: CadDocument) -> bool:
    return (
        IsColdRead(Document)
        and IsDistChmf(Document)
        and Document.assembly is None
        and not Document.brep_payloads
    )


# the interchange snapshot retains all modeled records after exact independent archive regeneration
def MakeChmfSnap(Document: CadDocument) -> CadDocument | None:
    if not IsChmfSnapDoc(Document):
        return None
    Original = Document.metadata.get(KSourceBytesKey)
    if KChmfSnapshot in Document.metadata:
        Recipe = ReadChmfSnap(Document)
    else:
        if (
            type(Original) is not bytes
            or CalcSha(Original).hexdigest() != Document.source.sha256
        ):
            raise ValueError("cold chamfer JSON requires its original source identity")
        Recipe = ReadChmfSelf(Original)
    _ = PrepChmfPart(
        Document,
        BytesIO(),
        Recipe.SavedAt,
        WriteOptions(values={"final_destination": Recipe.PathName}),
    )
    if KChmfSnapshot in Document.metadata:
        return Document
    return StripChmfSnap(Document, Recipe)
