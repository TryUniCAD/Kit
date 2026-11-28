# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

# Reserved launcher/worker exit statuses; other runner kinds keep their own exit semantics.
RPC_LOST = 71
SHUTDOWN_TIMEOUT = 72


class SolidRecovery(Exception):
    def __init__(self, status, diagnostic):
        super().__init__(str(diagnostic))
        self.status = status
