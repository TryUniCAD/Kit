# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import TypedDict


# immutable source bytes retain their measured identity across fixture transport boundaries
class MemberData(TypedDict):
    sha256: str
    size_bytes: int


# publication metadata separates transport paths from authenticated content identities
class ArtifactData(MemberData):
    path: str
