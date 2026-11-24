from __future__ import annotations

from interchange.serialization.DecodeChecked import DecodeChecked
from interchange.serialization.WireData import CheckWireData


# untrusted input is validated once at the root before typed records are rebuilt from it
def FromData(SourceValue: object) -> object:
    return DecodeChecked(CheckWireData(SourceValue))
