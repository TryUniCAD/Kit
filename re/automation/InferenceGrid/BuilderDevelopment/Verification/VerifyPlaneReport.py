# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from re import fullmatch
from argparse import ArgumentParser
from json import dumps, loads
from pathlib import Path
from sys import path

path.insert(0, str(Path(__file__).resolve().parents[3]))

from InferenceGrid.BuilderDevelopment.Verification.CheckCases import (
    CheckArchives,
    CheckCase,
)
from InferenceGrid.BuilderDevelopment.Verification.CheckCandidateSource import (
    CheckCandidateSource,
)
from InferenceGrid.BuilderDevelopment.Verification.CheckArchiveProcesses import (
    CheckArchiveProcesses,
)
from InferenceGrid.BuilderDevelopment.Verification.CheckSessions import (
    CheckControls,
    CheckSessions,
)
from InferenceGrid.BuilderDevelopment.Verification.FreezeExpectations import (
    FreezeExpectations,
    RecordHash,
    VerifierPins,
)
from InferenceGrid.BuilderDevelopment.Verification.ReportChecks import ReportChecks


# frozen contract and independently maintained verifier bytes must precede candidate observations
def CheckContract(Check, Report):
    Expected = Check.Expectations
    Body = {
        Key: Value for Key, Value in Expected.items() if Key != "expectations_sha256"
    }
    Check.Equal(
        RecordHash(Body),
        Expected["expectations_sha256"],
        "expectations.expectations_sha256",
        "source_mismatch",
    )
    Check.Equal(
        VerifierPins(),
        Expected["verifier_sources"],
        "expectations.verifier_sources",
        "source_mismatch",
    )
    Independent = FreezeExpectations(
        Expected["cases"],
        Expected["application_build"],
        Expected.get("source_pin"),
        Expected["control"],
    )
    Check.Equal(
        Expected, Independent, "expectations.frozen_contract", "source_mismatch"
    )
    Check.Equal(
        Check.Field(Report, "schema_version", "report"),
        1,
        "report.schema_version",
        "verifier_support_missing",
    )
    App = Check.Field(Report, "application", "report")
    Check.Equal(
        Check.Field(App, "build", "report.application"),
        Expected["application_build"],
        "report.application.build",
        "source_mismatch",
    )
    Source = Expected.get("source_pin")
    Revision = (
        Source.get("source_revision")
        if isinstance(Source, dict)
        else Source if isinstance(Source, str) and len(Source) == 40 else None
    )
    if Revision is not None:
        Check.Equal(
            Check.Field(Report, "source_revision", "report"),
            Revision,
            "report.source_revision",
            "source_mismatch",
        )
    Pins = Check.Field(Report, "source_pins", "report")
    if not isinstance(Pins, (dict, list)) or not Pins:
        Check.Add(
            "report.source_pins",
            "nonempty trusted collector source manifest",
            Pins,
            "verifier_support_missing",
        )
    elif isinstance(Pins, list):
        for Index, Pin in enumerate(Pins):
            if (
                not isinstance(Pin, dict)
                or not isinstance(Pin.get("path"), str)
                or not isinstance(Pin.get("sha256"), str)
                or not fullmatch("[0-9a-f]{64}", Pin["sha256"])
                or type(Pin.get("size_bytes")) is not int
                or Pin["size_bytes"] <= 0
            ):
                Check.Add(
                    f"report.source_pins[{Index}]",
                    "source path hash and positive size",
                    Pin,
                    "source_mismatch",
                )
    ProgramPin = Check.Field(Report, "program_sha256", "report")
    if not isinstance(ProgramPin, str) or not fullmatch("[0-9a-f]{64}", ProgramPin):
        Check.Add(
            "report.program_sha256",
            "candidate source digest",
            ProgramPin,
            "source_mismatch",
        )
    if isinstance(Source, dict) and Source.get("program_sha256") is not None:
        Check.Equal(
            ProgramPin,
            Source["program_sha256"],
            "report.program_sha256",
            "source_mismatch",
        )


# missing capabilities and unhealthy hosts remain unverified instead of becoming candidate successes
def VerifyPlaneReport(Expectations, Report, OutputDirectory=None):
    Check = ReportChecks(Expectations)
    try:
        if (
            not isinstance(Expectations, dict)
            or Expectations.get("schema_version") != 1
        ):
            raise ValueError("invalid frozen expectation schema")
        if not isinstance(Report, dict):
            raise ValueError("native report is not an object")
        Failure = Report.get("failure")
        if isinstance(Failure, dict) and Failure.get("classification") in {
            "license_unavailable",
            "application_unavailable",
            "unhealthy_session",
            "timeout",
        }:
            Classification = (
                "unhealthy_session"
                if Failure["classification"] == "timeout"
                else Failure["classification"]
            )
            Check.Add(
                "report.failure", "healthy complete native run", Failure, Classification
            )
            return Check.Result()
        CheckContract(Check, Report)
        if any(
            Item["classification"] == "source_mismatch" for Item in Check.Diagnostics
        ):
            return Check.Result()
        CheckCandidateSource(
            Check,
            Report,
            (
                OutputDirectory
                if OutputDirectory is not None
                else Report.get("output_directory")
            ),
        )
        CheckSessions(Check, Report)
        CheckControls(Check, Report)
        Archives = CheckArchives(
            Check,
            Report,
            (
                OutputDirectory
                if OutputDirectory is not None
                else Report.get("output_directory")
            ),
        )
        Cases = Check.Field(Report, "cases", "report")
        if not isinstance(Cases, list):
            Check.Add(
                "report.cases",
                "complete frozen case roster",
                Cases,
                "verifier_support_missing",
            )
            return Check.Result()
        Identities = [Case.get("id") for Case in Cases if isinstance(Case, dict)]
        ExpectedIds = [Case["id"] for Case in Expectations["cases"]]
        Check.Equal(sorted(Identities), sorted(ExpectedIds), "report.cases.roster")
        Check.Equal(
            sorted(Archives),
            sorted(ExpectedIds),
            "report.archives.case_roster",
            "source_mismatch",
        )
        for Expected in Expectations["cases"]:
            Matching = [
                Case
                for Case in Cases
                if isinstance(Case, dict) and Case.get("id") == Expected["id"]
            ]
            if len(Matching) == 1:
                CheckCase(
                    Check, Expected, Matching[0], Archives.get(Expected["id"], [])
                )
                CheckArchiveProcesses(Check, Matching[0], Report)
    except (
        OSError,
        TypeError,
        ValueError,
        KeyError,
        AttributeError,
        IndexError,
        OverflowError,
    ) as Error:
        Check.Add(
            "report.contract",
            "complete independently collectable native evidence",
            f"{type(Error).__name__}: {Error}",
            "verifier_support_missing",
        )
    return Check.Result()


# a separate verifier process can assess frozen native evidence without loading the generated builder
def MainVerify():
    Parser = ArgumentParser(allow_abbrev=False)
    Parser.add_argument("--expectations", required=True, type=Path)
    Parser.add_argument("--report", required=True, type=Path)
    Parser.add_argument("--output-directory", type=Path)
    Args = Parser.parse_args()
    for File in (Args.expectations, Args.report):
        if (
            File.is_symlink()
            or not File.is_file()
            or File.stat().st_size > 16 * 1024 * 1024
        ):
            Parser.error("verification inputs must be bounded regular JSON files")
    Expected = loads(Args.expectations.read_text(encoding="utf-8"))
    Report = loads(Args.report.read_text(encoding="utf-8"))
    Result = VerifyPlaneReport(Expected, Report, Args.output_directory)
    print(dumps(Result, sort_keys=True, allow_nan=False))
    return 0 if Result["verified"] else 2


# process exit status distinguishes accepted native evidence from explicit unverified diagnostics
if __name__ == "__main__":
    raise SystemExit(MainVerify())
