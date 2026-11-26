# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from math import isclose, isfinite
from re import fullmatch

from CaptureTools.Catalogue.Fusion.CheckReading import CheckReading
from CaptureTools.Catalogue.Fusion.FusionBatch import (
    ModelCase,
    NormalizeCases,
    PhasePaths,
)
from CaptureTools.Catalogue.Fusion.FusionEdits import EditCases
from CaptureTools.Catalogue.Fusion.FusionInputs import KFusionScope


# supplied comparisons must be reproducible from raw native observations and requested parameters
def VerifyReading(Reading, Case):
    if (
        not isinstance(Reading, dict)
        or CheckReading(Reading["observed"], Case) != Reading
    ):
        raise ValueError(
            "fusion comparison differs from independently checked native observations"
        )


# reports cannot substitute a successful flag for both pinned healthy control measurements
def VerifyControls(Report):
    Samples = []
    for Stage in ("healthy_control_before", "healthy_control_after"):
        Control = Report[Stage]
        if (
            Control["compute_all_return"] is not True
            or Control["native_input"] != Report["pins"]["control"]
        ):
            raise ValueError("fusion control lost its pinned input or native rebuild")
        for Moment in ("before_recompute", "after_recompute"):
            Reading = Control[Moment]
            if (
                Reading["body_count"] != 1
                or len(Reading["bodies"]) != 1
                or Reading["bodies"][0]["solid"] is not True
                or not Reading["feature_tree"]
                or not isclose(Reading["volume_mm3"], 30000, rel_tol=1e-9, abs_tol=1e-6)
                or any(
                    Feature["health"]["state"] != "healthy"
                    or Feature["suppressed"]
                    or Feature["rolled_back"]
                    for Feature in Reading["feature_tree"]
                )
            ):
                raise ValueError(
                    "fusion control did not retain its known healthy solid"
                )
            Samples.append(Reading["center_of_mass_mm"])
    if not all(
        len(Sample) == 3
        and all(type(Value) in (int, float) and isfinite(Value) for Value in Sample)
        for Sample in Samples
    ) or not all(
        all(
            isclose(Actual, Target, rel_tol=1e-9, abs_tol=1e-6)
            for Actual, Target in zip(Sample, Samples[0], strict=True)
        )
        for Sample in Samples
    ):
        raise ValueError("fusion healthy controls disagree on measured center of mass")


# controller intake repeats semantic checks instead of trusting the producer status labels
def VerifyReport(Receipt, Report, Raw, PlanHash, Phase, Cases):
    Normal = NormalizeCases(Cases, Report["mode"])
    if (
        Phase not in ("a", "b")
        or Receipt["schema"] != 1
        or Report["schema"] != 1
        or Receipt["scope"] != Report["scope"]
        or Report["scope"] != KFusionScope
        or Receipt["phase"] != Phase
        or Report["phase"] != Phase
        or Receipt["status"] != "complete"
        or Report["status"] != "complete"
        or Receipt["plan_sha256"] != PlanHash
        or Report["plan_sha256"] != PlanHash
        or Receipt["report_sha256"] != sha256(Raw).hexdigest()
        or Report["application"] != "fusion"
        or Report["errors"] != []
    ):
        raise ValueError(
            "fusion catalogue report does not bind a complete exact phase receipt"
        )
    if (
        not isinstance(Report["source_revision"], str)
        or not fullmatch("[0-9a-f]{40}", Report["source_revision"])
        or not isinstance(Report["application_build"], str)
        or not Report["application_build"]
        or len(Report["application_build"]) > 128
    ):
        raise ValueError(
            "fusion catalogue report omits exact source or application identity"
        )
    Process = Report["process"]
    if (
        type(Process["pid"]) is not int
        or Process["pid"] <= 1
        or type(Process["start_unix_seconds"]) is not int
        or Process["start_unix_seconds"] <= 0
        or not all(
            type(Report[Field]) in (int, float) and isfinite(Report[Field])
            for Field in ("started_unix_seconds", "ended_unix_seconds")
        )
        or Report["started_unix_seconds"] > Report["ended_unix_seconds"]
    ):
        raise ValueError(
            "fusion catalogue report omits an ordered native process lifetime"
        )
    VerifyControls(Report)
    if not isinstance(Report["cases"], list) or len(Report["cases"]) != len(Normal):
        raise ValueError("fusion catalogue report case roster differs")
    for Case, Row in zip(Normal, Report["cases"], strict=True):
        if (
            Row["id"] != Case["id"]
            or Row["case"] != ModelCase(Case)
            or "diagnostic" in Row
        ):
            raise ValueError("fusion catalogue report changed requested model inputs")
        if Phase == "a":
            VerifyReading(Row["authored"], ModelCase(Case))
        else:
            VerifyReading(Row["reopened"], ModelCase(Case))
            VerifyReading(Row["rebuilt"], ModelCase(Case))
            ExpectedEdits = EditCases(Case)
            if len(Row["edits"]) != len(ExpectedEdits):
                raise ValueError(
                    "fusion catalogue report omitted a driving parameter edit"
                )
            for Expected, Actual in zip(ExpectedEdits, Row["edits"], strict=True):
                if any(
                    Actual[Field] != Expected[Field]
                    for Field in ("parameter", "value", "case")
                ):
                    raise ValueError(
                        "fusion catalogue report changed its independent edit"
                    )
                VerifyReading(Actual["changed"], Expected["case"])
                VerifyReading(Actual["reopened"], Expected["case"])
                VerifyReading(Actual["restored"], ModelCase(Case))


# every reported archive must match the accepted immutable output artifact bytes
def CheckArtifacts(Report, Files, Phase):
    Identity = {
        "cases": [{"id": Row["id"], **Row["case"]} for Row in Report["cases"]],
        "mode": Report["mode"],
    }
    Paths = PhasePaths(Identity, Phase)
    if set(Paths) != set(Files):
        raise ValueError("fusion catalogue archive artifact roster differs")
    for Row in Report["cases"]:
        Archives = [(f"phase-{Phase}.{Row['id']}.baseline", Row["archive"])]
        if Phase == "b":
            Archives.extend(
                (f"phase-{Phase}.{Row['id']}.edit-{Edit['parameter']}", Edit["archive"])
                for Edit in Row["edits"]
            )
        for RoleName, Archive in Archives:
            if (
                Archive["file"] != Paths[RoleName].rsplit("/", 1)[-1]
                or type(Archive["size_bytes"]) is not int
                or not 0 < Archive["size_bytes"] <= 64 * 1024 * 1024
                or not isinstance(Archive["sha256"], str)
                or not fullmatch("[0-9a-f]{64}", Archive["sha256"])
                or any(
                    Archive[Field] != Files[RoleName][Field]
                    for Field in ("sha256", "size_bytes")
                )
            ):
                raise ValueError(
                    "fusion catalogue archive pins differ from accepted output artifacts"
                )
