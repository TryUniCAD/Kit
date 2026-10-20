# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from io import BytesIO as ByteStream
from io import StringIO as TextStream
from pathlib import Path as FilePath

from convert.adapters.base.ContractTypes import KSourceType


# probing must not consume one shot sources before the selected reader receives them
def GetReplayMut(SourceData: KSourceType) -> KSourceType:
    if isinstance(SourceData, (str, FilePath, bytes, bytearray)):
        return SourceData
    try:
        StreamPos = SourceData.tell()
        SourceData.seek(StreamPos)
        return SourceData
    except (AttributeError, OSError, TypeError, ValueError):
        SourceValue = SourceData.read()
    if isinstance(SourceValue, str):
        return TextStream(SourceValue)
    if isinstance(SourceValue, (bytes, bytearray)):
        return ByteStream(bytes(SourceValue))
    raise TypeError("source stream must yield text or bytes")
