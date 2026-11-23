# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from SharedQueue.State import installed
from SharedQueue.Dispatch import install_dispatch


# continuous aging has an indexable stable key and cannot starve older runnable work
def rank_order(ledger):
    if not installed(ledger):
        return ""
    install_dispatch(ledger)
    return "(SELECT rank FROM shared_dispatch WHERE job_id=j.id) DESC,"
