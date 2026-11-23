# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import TypedDict


# receipt comparisons need the persisted identity and attempt fields of each job
class ReceiptJob(TypedDict):
    id: str
    receipt: str | None
    attempts: int
    state: str


# each scope retains its own jobs across catalogue restarts
class ReceiptScope(TypedDict):
    jobs: list[ReceiptJob]


# restart comparisons consume the scopes in the saved catalogue report
class ReceiptReport(TypedDict):
    scopes: dict[str, ReceiptScope]
