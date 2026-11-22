# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath


# accepted records must be read from the immutable controller object rather than a worker scratch file
def ReadAccepted(StorePath: FilePath, PinValue: str) -> bytes:
    return (StorePath / "objects" / PinValue[:2] / PinValue).read_bytes()
