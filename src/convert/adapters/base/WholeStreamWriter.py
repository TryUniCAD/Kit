from typing import Protocol
from typing import runtime_checkable as RuntimeCheck

from interchange.document.Models.DocumentModel import CadDocument


# an opt in writer can attest the complete archive for a particular supported document
@RuntimeCheck
class WholeStreamWriter(Protocol):

    # the selected document determines whether the caller needs standalone stream bounds
    def IsWholeStream(self, DocumentValue: CadDocument) -> bool:
        raise TypeError("whole stream policy requires a concrete writer")
