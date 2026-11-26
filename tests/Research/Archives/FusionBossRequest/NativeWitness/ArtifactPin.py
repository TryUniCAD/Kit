# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath


# custody comparisons require the identity and length of the actual retained file bytes
def ArtifactPin(PathValue: FilePath) -> tuple[str, int]:
    Content = PathValue.read_bytes()
    return HashBytes(Content).hexdigest(), len(Content)
