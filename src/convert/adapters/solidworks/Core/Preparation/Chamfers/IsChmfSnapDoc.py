from convert.adapters.solidworks.Core.Preparation.Chamfers.IsDistChmf import IsDistChmf
from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import IsColdRead
from interchange.document.Models.DocumentModel import CadDocument


# candidate selection only delegates validation to the actual chamfer snapshot writer
def IsChmfSnapDoc(Document: CadDocument) -> bool:
    return (
        IsColdRead(Document)
        and IsDistChmf(Document)
        and Document.assembly is None
        and not Document.brep_payloads
    )
