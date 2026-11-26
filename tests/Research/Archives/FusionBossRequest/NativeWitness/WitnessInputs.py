# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath


# the handoff should reuse only the exact persisted inputs used by source free replay
def WitnessInputs(PrepPath: FilePath, MirrorRoot: FilePath) -> dict[str, FilePath]:
    return {
        "request": PrepPath / "P03Request.json",
        "witness": PrepPath / "P03SourceWitness.json",
        "seed_helper": MirrorRoot / "SeedHelper.py",
        "snapshot_builder": MirrorRoot / "SnapshotBuilder.py",
        "snapshot_owners": MirrorRoot / "SnapshotOwners.py",
    }
