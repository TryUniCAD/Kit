# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as HashBytes
from json import dumps as EncodeJson


# registry corruption scenarios require independent hashes of the persisted public contract
def RecordDigest(RecordValue: dict | list) -> str:
    Content = EncodeJson(
        RecordValue, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return HashBytes(Content.encode("utf-8")).hexdigest()
