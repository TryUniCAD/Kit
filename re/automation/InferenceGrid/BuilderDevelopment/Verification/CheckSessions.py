# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# qualification requires independently owned fresh native processes that closed normally
def CheckSessions(Check, Report):
    Phases = Check.Field(Report, "phases", "report")
    if not isinstance(Phases, dict):
        Check.Add(
            "report.phases",
            "two owned native phases",
            Phases,
            "verifier_support_missing",
        )
        return
    Owners = []
    for PhaseName in ("first", "second"):
        Phase = Check.Field(Phases, PhaseName, "report.phases")
        if not isinstance(Phase, dict):
            continue
        Owner = Check.Field(Phase, "owner", "report.phases." + PhaseName)
        Native = Check.Field(Phase, "native", "report.phases." + PhaseName)
        if not isinstance(Owner, dict) or not isinstance(Native, dict):
            Check.Add(
                "report.phases." + PhaseName,
                "owner and native lifetime observations",
                Phase,
                "verifier_support_missing",
            )
            continue
        Owners.append(Owner)
        Prefix = "report.phases." + PhaseName
        for Field, Expected in {
            "owned_process_exit_observed": True,
            "forced_owned_cleanup": False,
        }.items():
            Check.Equal(
                Check.Field(Owner, Field, Prefix + ".owner"),
                Expected,
                Prefix + ".owner." + Field,
                "unhealthy_session",
            )
        for Field, Expected in {
            "initial_documents": 0,
            "background_control": True,
            "normal_exit_requested": True,
            "cleanup_errors": [],
        }.items():
            Check.Equal(
                Check.Field(Native, Field, Prefix + ".native"),
                Expected,
                Prefix + ".native." + Field,
                "unhealthy_session",
            )
        Pid = Check.Field(Owner, "pid", Prefix + ".owner")
        if type(Pid) is not int or Pid <= 0:
            Check.Add(
                Prefix + ".owner.pid",
                "positive owned process id",
                Pid,
                "unhealthy_session",
            )
        Check.Equal(
            Check.Field(Native, "pid", Prefix + ".native"),
            Pid,
            Prefix + ".native.pid",
            "unhealthy_session",
        )
        if "failure" in Native:
            Check.Add(
                Prefix + ".native.failure",
                "absent",
                Native["failure"],
                "unhealthy_session",
            )
    if len(Owners) == 2:
        if Owners[0].get("pid") == Owners[1].get("pid"):
            Check.Add(
                "report.phases.process_ids",
                "independently created process ids",
                [Owner.get("pid") for Owner in Owners],
                "unhealthy_session",
            )
        Created = [Owner.get("created") for Owner in Owners]
        if (
            any(type(Value) is not int or Value <= 0 for Value in Created)
            or Created[0] >= Created[1]
        ):
            Check.Add(
                "report.phases.created",
                "positive increasing native process creation times",
                Created,
                "unhealthy_session",
            )


# stable nonzero control geometry alone is insufficient without the pinned original control bytes
def CheckControls(Check, Report):
    Controls = Check.Field(Report, "controls", "report")
    if not isinstance(Controls, dict):
        Check.Add(
            "report.controls",
            "controls before and after each phase",
            Controls,
            "verifier_support_missing",
        )
        return
    for PhaseName in ("first", "second"):
        Phase = Check.Field(Controls, PhaseName, "report.controls")
        for Position in ("before", "after"):
            Prefix = f"report.controls.{PhaseName}.{Position}"
            Control = Check.Field(Phase, Position, "report.controls." + PhaseName)
            if not isinstance(Control, dict):
                Check.Add(
                    Prefix,
                    "healthy native control observation",
                    Control,
                    "unhealthy_session",
                )
                continue
            Expected = Check.Expectations["control"]
            for Field in ("native_sha256", "body_count"):
                Check.Equal(
                    Check.Field(Control, Field, Prefix),
                    Expected[Field],
                    Prefix + "." + Field,
                    "unhealthy_session",
                )
            Check.Near(
                Check.Field(Control, "volume_mm3", Prefix),
                Expected["volume_mm3"],
                Prefix + ".volume_mm3",
                "volume_mm3",
                "unhealthy_session",
            )
            Check.Vector(
                Check.Field(Control, "center_of_mass_mm", Prefix),
                Expected["center_of_mass_mm"],
                Prefix + ".center_of_mass_mm",
                Classification="unhealthy_session",
            )
