# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from InferenceArchives import FORMATS, native_bytes
from InferenceGrid.FeatureAssessment import ProvisionAssessment, ReadFeatureAssessment
from InferenceRunner import GAP_KIND
from InferenceSchedule import build_schedule
from Ledger import Ledger
from PairedCaptureIntake import GitSnapshot, require
from RectanglePairEvidence import REVISION, ROOT, report
from Records import canonical

# corner rectangle and its driving dimensions share one pinned discovery assessment
RectangleScope = "p01-corner-rectangle"


# the existing paired reader verifies measured geometry before archive jobs are allowed
def RectangleSchedule(Revision):
    Compared = report(recipe_ids=("P01",))
    Rows = Compared["pairs"]
    require(
        Compared["capture_revision"] == REVISION and len(Rows) == 6,
        "P01 paired evidence does not contain the expected six variants",
    )
    Snapshot = GitSnapshot(ROOT)
    Sources = {}
    Corroboration = {}
    for Row in Rows:
        require(
            Row["recipe_id"] == "P01"
            and Row["rectangle"]["perimeter"]["status"] == "equal",
            "P01 rectangle geometry did not agree with the paired observations",
        )
        require(
            set(Row["rectangle"]["dimensions"]) == {"width_mm", "height_mm"},
            "P01 paired evidence lacks its two driving dimensions",
        )
        Corroboration[Row["variant"]] = {
            "perimeter": Row["rectangle"]["perimeter"]["status"],
            "dimensions": Row["rectangle"]["dimensions"],
            "sources": {App: Asset["sha256"] for App, Asset in Row["sources"].items()},
        }
        for App, Asset in Row["sources"].items():
            Pin = Asset["sha256"]
            require(Pin not in Sources, "P01 pairs repeat an archive identity")
            Sources[Pin] = (FORMATS[App], native_bytes(Snapshot, Asset))
    require(
        len(Sources) == 12 and len(Corroboration) == 6,
        "P01 discovery archive roster differs",
    )
    return BuildRectangleBatch(
        Revision, Sources, Corroboration, Compared["receipts"]["P01"]
    )


# a paired result provides the existing decoder with exact downstream archive selectors
def BuildRectangleBatch(Revision, Sources, Corroboration, Receipts):
    PlanName = RectangleScope + ":plan"
    Plan = {
        "inference_version": 1,
        "scope": RectangleScope,
        "status": "corroborated",
        "capture_revision": REVISION,
        "hypothesis": "The P01 paired readers preserve the measured planar rectangle and its driving dimensions",
        "affected_archives": {Pin: Format for Pin, (Format, _) in Sources.items()},
        "corroboration": {"receipts": Receipts, "variants": Corroboration},
    }
    Bindings = {
        PlanName: canonical(Plan).encode("utf-8"),
        **{Pin: Raw for Pin, (_, Raw) in Sources.items()},
    }
    Batch = build_schedule(
        {
            "inference_version": 1,
            "scope": RectangleScope,
            "family": "rectangular-history",
            "rule_version": "paired-rectangle-discovery@1",
            "tool_version": Revision,
            "plan_input": PlanName,
            "stream_inputs": {},
            "assessment_kind": GAP_KIND,
            "archives": {
                Pin: {"format": Format, "binding": Pin}
                for Pin, (Format, _) in Sources.items()
            },
            "distinguishing_evidence": [
                "width-edit",
                "height-edit",
                "plane-yz",
                "units-inch",
            ],
            "depends_on": [],
        }
    )
    return Bindings, Batch


# the standard controller publishes the assessment and archive dependencies
def SubmitRectangle(Store, Revision):
    return ProvisionAssessment(Store, Revision, REVISION, RectangleSchedule)


# equivalent catalogue routes read the same paired receipt records
def StatusRectangle(Store):
    with Ledger(Store) as State:
        return ReadFeatureAssessment(State, RectangleScope)
