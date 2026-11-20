# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from json import dumps

from PairedCaptureIntake import GitSnapshot, intake
from PairedCaptures.FusionRunEvidence import VerifyFusionRun


# the original authoring graph remains authoritative after clean history source restoration
def ReplayFusion(RootPath, Entry, RunFolder):
    Report = intake(RootPath, Entry["handoff_revision"])
    if Report["quarantined_families"]:
        raise ValueError("Fusion supplemental capture lineage is quarantined")
    Result = VerifyFusionRun(
        GitSnapshot(RootPath), Report, RunFolder, Entry["input_sha256"]
    )
    Encoded = (dumps(Result, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    if (
        Result["capture_source_revision"] != Entry["source_revision"]
        or sha256(Encoded).hexdigest() != Entry["report_sha256"]
        or Entry["recipe"] not in Result["recipes"]
    ):
        raise ValueError("Fusion supplemental source or normalized replay digest changed")
    Observations = {
        Native["path"].rsplit("/", 1)[1]: Native["sha256"]
        for Capture in Report["captures"]
        if Capture["application"] == "fusion"
        and Capture["recipe_id"] == Entry["recipe"]
        for Native in Capture["native_files"]
    }
    return Observations, Result["recipes"][Entry["recipe"]]
