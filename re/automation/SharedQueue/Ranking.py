# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from SharedQueue.State import installed


# minute aging prevents newly submitted urgent jobs from starving older runnable work
def rank_order(ledger):
    if not installed(ledger):
        return ""
    return """(COALESCE((SELECT MAX(r.priority) FROM shared_members m JOIN shared_requests r ON r.request=m.request WHERE m.job_id=j.id AND r.active=1),50) + CAST(MAX(0,:now-j.created)/60 AS INTEGER)) DESC,"""
