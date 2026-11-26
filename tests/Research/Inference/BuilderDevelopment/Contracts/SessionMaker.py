# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from abc import abstractmethod
from pathlib import Path as FilePath
from typing import Protocol


# the fixture constructs a real provider client through its exact trusted public boundary
class SessionMaker(Protocol):

    # constructor keywords pin fixture transport and explicit personal context permission independently
    @abstractmethod
    def __call__(
        self,
        Options: object,
        Directory: FilePath,
        *,
        Command: list[str],
        AllowPersonalInstructions: bool,
    ) -> object:
        pass
