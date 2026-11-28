# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Callable, NamedTuple, cast as CastValue


# immutable callback contracts preserve the real research client methods exercised by subprocess fixtures
class SessionHooks(NamedTuple):
    CommandArgs: list[str]
    GenerateCall: Callable[[str, dict[str, object], int], dict[str, object]]
    CloseCall: Callable[[], None]


# exact method casts describe the excluded research boundary without replacing its runtime implementation
def BindSession(Session: object) -> SessionHooks:
    return SessionHooks(
        CastValue(list[str], getattr(Session, "command")),
        CastValue(
            Callable[[str, dict[str, object], int], dict[str, object]],
            getattr(Session, "Generate"),
        ),
        CastValue(Callable[[], None], getattr(Session, "close")),
    )
