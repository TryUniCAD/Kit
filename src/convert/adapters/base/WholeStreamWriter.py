from typing import Protocol
from typing import runtime_checkable as RuntimeCheck


# writers that attest a whole file must publish through the standalone stream boundary
@RuntimeCheck
class WholeStreamWriter(Protocol):

    # this optional capability leaves ordinary stream append semantics with the selected writer
    @property
    def IsWholeStream(self) -> bool:
        raise TypeError("whole stream policy requires a concrete writer")
