# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson
from os import write as WriteBytes
from time import sleep as WaitBriefly


# deliberately split protocol records exercise real pipe framing across separate process writes
def SendReply(Value: dict[str, object]) -> None:
    RawBytes = (EncodeJson(Value) + "\n").encode()
    _ = WriteBytes(1, RawBytes[:7])
    WaitBriefly(0.001)
    _ = WriteBytes(1, RawBytes[7:])
