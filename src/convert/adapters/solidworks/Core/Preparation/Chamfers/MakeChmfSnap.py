from hashlib import sha256 as CalcSha
from io import BytesIO

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Adapter import KSourceBytesKey
from convert.adapters.solidworks.Core.Preparation.Chamfers.ChmfSnapMeta import (
    KChmfSnapshot,
    ReadChmfSnap,
)
from convert.adapters.solidworks.Core.Preparation.Chamfers.BuildChmfPart import (
    BuildChmfPart,
)
from convert.adapters.solidworks.Core.Preparation.Chamfers.CheckChmfSnap import (
    CheckChmfSnap,
)
from convert.adapters.solidworks.Core.Preparation.Chamfers.IsChmfSnapDoc import (
    IsChmfSnapDoc,
)
from convert.adapters.solidworks.Core.Preparation.Chamfers.ReadChmfSelf import (
    ReadChmfSelf,
)
from interchange.document.Models.DocumentModel import CadDocument


# interchange validation compiles the same logical archive regardless of current compression
def MakeChmfSnap(Document: CadDocument) -> CadDocument | None:
    if not IsChmfSnapDoc(Document):
        return None
    if KChmfSnapshot in Document.metadata:
        Original: tuple[bytes, SldprtArchive] | None = None
        Recipe = ReadChmfSnap(Document)
    else:
        Attachment = Document.metadata.get(KSourceBytesKey)
        if (
            type(Attachment) is not bytes
            or CalcSha(Attachment).hexdigest() != Document.source.sha256
        ):
            raise ValueError("cold chamfer JSON requires its original source identity")
        Archive = SldprtArchive.from_bytes(Attachment)
        Original = (Attachment, Archive)
        Recipe = ReadChmfSelf(Archive)
    Candidate = BuildChmfPart(
        Document,
        BytesIO(),
        Recipe.SavedAt,
        WriteOptions(values={"final_destination": Recipe.PathName}),
    )
    return CheckChmfSnap(Document, Candidate, Recipe, Original)
