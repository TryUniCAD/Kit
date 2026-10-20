# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from io import TextIOBase as TextStream
from pathlib import Path as FilePath
from typing import BinaryIO as BinaryStream
from typing import TextIO as TypeTextStream


# reader contracts accept paths memory payloads and caller owned streams
KSourceType = str | FilePath | bytes | bytearray | BinaryStream | TypeTextStream


# writer contracts accept filesystem destinations and caller owned streams
KTargetType = str | FilePath | BinaryStream | TypeTextStream


# windows path validation must reject reserved device names before filesystem access
def IsDeviceName(ValueText: str) -> bool:
    StemValue = ValueText.split(".", 1)[0].casefold()
    return StemValue in {"con", "prn", "aux", "nul"} or (
        len(StemValue) == 4
        and StemValue[:3] in {"com", "lpt"}
        and StemValue[3] in "123456789¹²³"
    )


# stream staging needs a reliable distinction between binary and text destinations
def IsBinaryTarget(TargetValue: KTargetType) -> bool:
    if isinstance(TargetValue, (str, FilePath, TextStream)):
        return False
    WriterValue = getattr(TargetValue, "write", None)
    return callable(WriterValue) and getattr(TargetValue, "encoding", None) is None
