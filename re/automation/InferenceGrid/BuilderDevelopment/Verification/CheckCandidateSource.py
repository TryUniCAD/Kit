# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from pathlib import Path
from re import fullmatch


# generated code provenance must identify the exact plain source compiled inside the owned native session
def CheckCandidateSource(Check, Report, OutputDirectory):
    Candidate = Check.Field(Report, "candidate_source", "report")
    Prefix = "report.candidate_source"
    if not isinstance(Candidate, dict):
        Check.Add(
            Prefix,
            "executed candidate source provenance",
            Candidate,
            "verifier_support_missing",
        )
        return
    Executed = Check.Field(Candidate, "executed", Prefix)
    if Executed is not True:
        Check.Add(Prefix + ".executed", True, Executed, "verifier_support_missing")
    Pin = Check.Field(Candidate, "sha256", Prefix)
    if not isinstance(Pin, str) or not fullmatch("[0-9a-f]{64}", Pin):
        Check.Add(
            Prefix + ".sha256",
            "compiled source SHA-256",
            Pin,
            "verifier_support_missing" if Pin is None else "source_mismatch",
        )
        return
    SourcePin = Check.Expectations.get("source_pin")
    if (
        isinstance(SourcePin, dict)
        and SourcePin.get("candidate_source_sha256") is not None
    ):
        Check.Equal(
            Pin,
            SourcePin["candidate_source_sha256"],
            Prefix + ".sha256",
            "source_mismatch",
        )
    Name = Check.Field(Candidate, "path", Prefix)
    if not isinstance(Name, str) or not Name:
        Check.Add(
            Prefix + ".path",
            "plain contained compiled C# source file",
            Name,
            "verifier_support_missing",
        )
        return
    if OutputDirectory is None:
        Check.Add(
            "report.output_directory",
            "independent native output directory",
            None,
            "verifier_support_missing",
        )
        return
    try:
        Root = Path(OutputDirectory).resolve(strict=True)
        Target = Path(Name)
        if not Target.is_absolute():
            Target = Root / Target
        if (
            not Root.is_dir()
            or not Target.is_relative_to(Root)
            or Target.suffix.lower() != ".cs"
        ):
            Check.Add(
                Prefix + ".path",
                "C# source contained in native output directory",
                Name,
                "source_mismatch",
            )
            return
        Current = Root
        for Part in Target.relative_to(Root).parts:
            Current = Current / Part
            if Current.is_symlink() or Current.is_junction():
                Check.Add(
                    Prefix + ".path",
                    "plain source without symlinks or junctions",
                    Name,
                    "source_mismatch",
                )
                return
        if not Target.is_file() or not Target.resolve(strict=True).is_relative_to(Root):
            Check.Add(
                Prefix + ".path", "plain contained source file", Name, "source_mismatch"
            )
            return
        Before = Target.stat()
        if not 0 < Before.st_size <= 1024 * 1024:
            Check.Add(
                Prefix + ".size_bytes",
                "source from one byte to one MiB",
                Before.st_size,
                "source_mismatch",
            )
            return
        Content = Target.read_bytes()
        After = Target.stat()
        IdentityBefore = [
            Before.st_dev,
            Before.st_ino,
            Before.st_size,
            Before.st_mtime_ns,
        ]
        IdentityAfter = [After.st_dev, After.st_ino, After.st_size, After.st_mtime_ns]
        Check.Equal(
            IdentityAfter,
            IdentityBefore,
            Prefix + ".identity_after_read",
            "source_mismatch",
        )
        Check.Equal(
            sha256(Content).hexdigest(),
            Pin,
            Prefix + ".sha256_actual",
            "source_mismatch",
        )
    except OSError as Error:
        Check.Add(
            Prefix + ".path",
            "readable plain contained source",
            f"{type(Error).__name__}: {Error}",
            "source_mismatch",
        )
