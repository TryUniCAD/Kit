# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Callable
from contextlib import AbstractContextManager as ContextScope
from pathlib import Path as FilePath
from typing import Protocol


# only the trusted fixture command constructor is exposed across the dynamic research import boundary
class SessionMaker(Protocol):

    # provider construction stays separate from caller controlled protocol requests
    def __call__(self, Options: object, *, Command: list[str]) -> object:
        pass


# controllers expose context ownership without making research implementation details static test dependencies
class BrokerMaker(Protocol):

    # the broker factory receives only the existing options directory and trusted session constructor
    def __call__(
        self,
        Options: object,
        Directory: FilePath,
        SessionFactory: Callable[[object], object],
    ) -> ContextScope[object]:
        pass


# process inspection retains the runtime boolean flags used by the ownership assertion
class LiveProbe(Protocol):

    # the live flag excludes exited processes while preserving the original inspection boundary
    def __call__(self, ProcessId: int, **Flags: bool) -> str | None:
        pass
