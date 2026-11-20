# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as HashBytes
from json import loads as LoadJson
from pathlib import Path as FilePath

# public reader evidence stays anchored to the checked out source and original capture receipt
KRepoRoot = FilePath(__file__).resolve().parents[5]

# these five original sources have independent licensed geometry and ownership observations
KCohort = KRepoRoot / "re/automation/PairedCaptures/P02/solidworks-4a9e35f34a39"

# every saved variant retains the same physical units while its native support may differ
KCases = (
    ("baseline-a", 5.0, 2, "mm"),
    ("baseline-b", 5.0, 2, "mm"),
    ("edit-diameter_mm-16", 8.0, 2, "mm"),
    ("units-inch", 5.0, 2, "in"),
    ("plane-yz", 5.0, 4, "mm"),
)


# changed fixture bytes must fail before any expected reader observation can be trusted
def ReadCircleInput(CaseName: str) -> bytes:
    NameValue = f"P02-solidworks-{CaseName}.SLDPRT"
    Receipt = LoadJson((KCohort / "receipt.json").read_bytes())
    (Pinned,) = tuple(
        Entry for Entry in Receipt["native_files"] if Entry["file"] == NameValue
    )
    SourceBytes = (KCohort / NameValue).read_bytes()
    assert len(SourceBytes) == Pinned["size_bytes"]
    assert HashBytes(SourceBytes).hexdigest() == Pinned["sha256"]
    return SourceBytes
