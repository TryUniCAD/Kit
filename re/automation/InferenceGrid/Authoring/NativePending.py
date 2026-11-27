# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from StoreRead import read_store


# application restart waits must not trigger the offline supervisor idle cutoff
def HasNativeWork(StorePath):
    with read_store(StorePath / "ledger.sqlite3", None, (4,), timeout=0.1) as Database:
        PairTable = Database.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='fusion_restart_pairs'"
        ).fetchone()
        if (
            PairTable
            and Database.execute(
                "SELECT 1 FROM fusion_restart_pairs p JOIN jobs b ON b.id=p.phase_b "
                "WHERE p.a_receipt IS NOT NULL AND p.final_evidence IS NULL "
                "AND b.state NOT IN ('failed','rejected') LIMIT 1"
            ).fetchone()
        ):
            return True
        return (
            Database.execute(
                "SELECT 1 FROM jobs j JOIN job_resources r ON r.job_id=j.id "
                "JOIN resources a ON a.name=r.resource "
                "WHERE j.state IN ('queued','running','waiting_application','waiting_evidence') "
                "AND a.available=1 LIMIT 1"
            ).fetchone()
            is not None
        )
