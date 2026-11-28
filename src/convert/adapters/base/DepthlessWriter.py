from typing import Protocol, runtime_checkable as RuntimeCheck

from convert.adapters.base.ContractTypes import KTargetType
from interchange.document.Models.DocumentModel import CadDocument


# the selected writer must prove its one depthless root feature before ordinary native validation
@RuntimeCheck
class DepthlessWriter(Protocol):

    # the common guard needs an actual root identity rather than a blanket end mode capability
    def ProveThroughEnd(
        self, DocumentValue: CadDocument, TargetValue: KTargetType
    ) -> str | None:
        raise TypeError("depthless write evidence requires a concrete writer")
