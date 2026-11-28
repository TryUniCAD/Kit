from dataclasses import dataclass
from convert.adapters.solidworks.Drawing.Construction.Portable.BlankDrawInput import (
    BlankDrawInput,
)


# strict reconstruction needs typed semantic owners without retaining an opaque native payload
@dataclass(frozen=True, slots=True)
class BlankIntent:
    InputValue: BlankDrawInput
    NativeSheetId: int
    VersionValue: int
