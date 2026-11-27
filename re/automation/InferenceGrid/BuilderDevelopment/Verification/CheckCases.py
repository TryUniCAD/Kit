# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from pathlib import Path, PurePosixPath
from re import fullmatch

from InferenceGrid.BuilderDevelopment.Verification.CheckObservation import (
    CheckObservation,
)


# actual saved files are independently rehashed before their observation roster can qualify
def CheckArchives(Check, Report, OutputDirectory):
    Archives = Check.Field(Report, "archives", "report")
    if not isinstance(Archives, list) or not Archives:
        Check.Add(
            "report.archives",
            "nonempty native archive roster",
            Archives,
            "verifier_support_missing",
        )
        return {}
    Root = None if OutputDirectory is None else Path(OutputDirectory).resolve()
    if Root is None or not Root.is_dir():
        Check.Add(
            "report.output_directory",
            "independent existing native output directory",
            str(OutputDirectory),
            "verifier_support_missing",
        )
    ByCase, Seen = {}, set()
    for Index, Archive in enumerate(Archives):
        Prefix = f"report.archives[{Index}]"
        Name = Check.Field(Archive, "file", Prefix)
        Member = (
            PurePosixPath(Name.replace("\\", "/")) if isinstance(Name, str) else None
        )
        if (
            Member is None
            or Member.is_absolute()
            or any(Part in {"..", "."} or ":" in Part for Part in Member.parts)
            or str(Member) in Seen
            or not Member.parts
        ):
            Check.Add(
                Prefix + ".file",
                "unique contained relative native file",
                Name,
                "source_mismatch",
            )
            continue
        Seen.add(str(Member))
        Pin = Check.Field(Archive, "sha256", Prefix)
        Size = Check.Field(Archive, "size_bytes", Prefix)
        if (
            not isinstance(Pin, str)
            or not fullmatch("[0-9a-f]{64}", Pin)
            or type(Size) is not int
            or Size <= 0
            or Size > 64 * 1024 * 1024
        ):
            Check.Add(
                Prefix, "native file hash and positive size", Archive, "source_mismatch"
            )
        if Root is not None and Root.is_dir():
            Target = Root.joinpath(*Member.parts)
            if (
                Target.is_symlink()
                or not Target.is_file()
                or not Target.resolve().is_relative_to(Root)
            ):
                Check.Add(
                    Prefix + ".file",
                    "regular file contained in native output directory",
                    Name,
                    "source_mismatch",
                )
            elif Target.stat().st_size > 64 * 1024 * 1024:
                Check.Add(
                    Prefix + ".size_bytes",
                    "native archive below 64 MiB",
                    Target.stat().st_size,
                    "source_mismatch",
                )
            else:
                Content = Target.read_bytes()
                Check.Equal(
                    sha256(Content).hexdigest(),
                    Pin,
                    Prefix + ".sha256",
                    "source_mismatch",
                )
                Check.Equal(
                    len(Content), Size, Prefix + ".size_bytes", "source_mismatch"
                )
        CaseId = Check.Field(Archive, "case_id", Prefix)
        ByCase.setdefault(CaseId, []).append(Archive)
    return ByCase


# all edit and restoration observations must match the frozen numeric requests
def CheckCase(Check, Expected, Actual, Archives):
    Prefix = "report.cases." + Expected["id"]
    Check.Equal(
        Check.Field(Actual, "application_build", Prefix),
        Check.Expectations["application_build"],
        Prefix + ".application_build",
        "source_mismatch",
    )
    Check.Equal(
        Check.Field(Actual, "requested", Prefix),
        {Key: Expected[Key] for Key in ("offset_mm", "edit_mm")},
        Prefix + ".requested",
    )
    Observed = Check.Field(Actual, "observations", Prefix)
    if not isinstance(Observed, dict):
        Check.Add(
            Prefix + ".observations",
            "complete measurement roster",
            Observed,
            "verifier_support_missing",
        )
        return
    for Name in ("baseline", "unchanged_rebuild"):
        CheckObservation(
            Check,
            Check.Field(Observed, Name, Prefix + ".observations"),
            Expected["offset_mm"],
            Prefix + ".observations." + Name,
        )
    Fresh = Check.Field(Observed, "fresh_reopen", Prefix + ".observations")
    Check.Equal(
        Check.Field(Fresh, "open_status", Prefix + ".observations.fresh_reopen"),
        {"errors": 0, "warnings": 0},
        Prefix + ".observations.fresh_reopen.open_status",
    )
    CheckObservation(
        Check,
        Check.Field(Fresh, "measurements", Prefix + ".observations.fresh_reopen"),
        Expected["offset_mm"],
        Prefix + ".observations.fresh_reopen.measurements",
    )
    EditError = Observed.get("edit_error")
    if EditError:
        Check.Add(
            Prefix + ".observations.edit_error",
            "successful actual driving edit and restoration",
            EditError,
        )
    else:
        for Name, Value in (
            ("edited", Expected["edit_mm"]),
            ("restored", Expected["offset_mm"]),
        ):
            CheckObservation(
                Check,
                Check.Field(Observed, Name, Prefix + ".observations"),
                Value,
                Prefix + ".observations." + Name,
            )
    CheckSaves(Check, Expected, Actual, Observed, Archives, Prefix)


# every baseline edit and restored archive needs independent fresh process reopen measurements
def CheckSaves(Check, Expected, Actual, Observed, Archives, Prefix):
    Saves = Check.Field(Actual, "saves", Prefix)
    if not isinstance(Saves, list):
        Check.Add(
            Prefix + ".saves",
            "saved baseline edit and restored archives",
            Saves,
            "verifier_support_missing",
        )
        return
    Roles = [Save.get("role") for Save in Saves if isinstance(Save, dict)]
    Check.Equal(
        sorted(Roles), ["baseline-a", "baseline-b", "edited"], Prefix + ".saves.roles"
    )
    Names = [Save.get("file") for Save in Saves if isinstance(Save, dict)]
    if len(set(Names)) != len(Names):
        Check.Add(Prefix + ".saves.files", "unique saved filenames", Names)
    Reopened = Check.Field(Observed, "reopened_files", Prefix + ".observations")
    if not isinstance(Reopened, dict):
        Check.Add(
            Prefix + ".observations.reopened_files",
            "independent reopen roster",
            Reopened,
            "verifier_support_missing",
        )
        return
    Check.Equal(
        sorted(Reopened), sorted(Names), Prefix + ".observations.reopened_files.roster"
    )
    ArchiveRoles = [Archive.get("role") for Archive in Archives]
    Check.Equal(
        sorted(ArchiveRoles),
        sorted(Roles),
        Prefix + ".archives.roles",
        "source_mismatch",
    )
    for Save in Saves:
        Name, Role = Save.get("file"), Save.get("role")
        if (
            not isinstance(Name, str)
            or PurePosixPath(Name.replace("\\", "/")).name != Name
        ):
            Check.Add(
                Prefix + ".saves.file", "native saved basename", Name, "source_mismatch"
            )
            continue
        Target = Expected["edit_mm"] if Role == "edited" else Expected["offset_mm"]
        for Field in ("save_errors", "save_warnings"):
            Check.Equal(
                Check.Field(Save, Field, Prefix + ".saves." + Name),
                0,
                Prefix + ".saves." + Name + "." + Field,
            )
        Check.Near(
            Check.Field(Save, "offset_mm", Prefix + ".saves." + Name),
            Target,
            Prefix + ".saves." + Name + ".offset_mm",
        )
        Matching = [Archive for Archive in Archives if Archive.get("role") == Role]
        if len(Matching) == 1:
            for Field in ("sha256", "size_bytes"):
                Check.Equal(
                    Save.get(Field),
                    Matching[0].get(Field),
                    Prefix + ".saves." + Name + "." + Field,
                    "source_mismatch",
                )
            Check.Equal(
                PurePosixPath(Matching[0]["file"].replace("\\", "/")).name,
                Name,
                Prefix + ".archives." + Role + ".file",
                "source_mismatch",
            )
        Reading = Reopened.get(Name)
        if isinstance(Reading, dict):
            Check.Equal(
                Check.Field(Reading, "open_status", Prefix + ".reopened." + Name),
                {"errors": 0, "warnings": 0},
                Prefix + ".reopened." + Name + ".open_status",
            )
            Check.Equal(
                Check.Field(Reading, "role", Prefix + ".reopened." + Name),
                Role,
                Prefix + ".reopened." + Name + ".role",
            )
            Check.Near(
                Check.Field(
                    Reading, "requested_offset_mm", Prefix + ".reopened." + Name
                ),
                Target,
                Prefix + ".reopened." + Name + ".requested_offset_mm",
            )
            CheckObservation(Check, Reading, Target, Prefix + ".reopened." + Name)
