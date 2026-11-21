from typing import Protocol, runtime_checkable as RuntimeCheck


# formats must declare that their output can preserve a drawing document
@RuntimeCheck
class DrawingWriter(Protocol):
    KTypedDrawings: bool
