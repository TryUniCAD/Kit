# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from tests.Research.Inference.Scope.ReceiptReport import ReceiptReport


# settled job attempts and receipt identities must both survive a restart
def ReadReceipts(Report: ReceiptReport) -> dict[str, tuple[str | None, int]]:
    return {
        JobRow["id"]: (JobRow["receipt"], JobRow["attempts"])
        for Scope in Report["scopes"].values()
        for JobRow in Scope["jobs"]
        if JobRow["state"] == "completed"
    }
