from convert.adapters.base.AdapterProtocols import CadWriterAdapter
from convert.adapters.registry.NativeWrite import CheckNative
from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import IsColdRead
from convert.adapters.solidworks.Core.Writing.AttachedBox.BoxProof import BoxProof
from convert.adapters.solidworks.Core.Writing.AttachedBox.FindBoxProof import (
    FindBoxProof,
)
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.document.Models.DocumentModel import CadDocument


# only the actual measured part writer can replace source gates with independently verified typed ownership
def CheckPartSource(
    Document: CadDocument, WriterValue: CadWriterAdapter
) -> BoxProof | None:
    ProofValue = FindBoxProof(WriterValue, Document)
    if ProofValue is None and (
        type(WriterValue) is not SldprtWriter or not IsColdRead(Document)
    ):
        CheckNative(Document)
    return ProofValue
