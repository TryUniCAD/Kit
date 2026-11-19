# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import sqlite3
import subprocess
import sys

from InferenceGrid.CatalogueRunPlan import BuildRunPlan, RunOutcome
from InferenceGrid.FeatureRoutes import FeatureRecipes
from InferenceGrid.Provision import CheckRevision
from Ledger import Ledger
from Pilot.PilotConfig import PilotConfig
from Pilot.PilotFiles import WriteRecord
from Supervisor import read_config

# independent routes keep running when another route lacks local prerequisites
ScopeErrors = (
    OSError,
    ValueError,
    KeyError,
    TypeError,
    RuntimeError,
    sqlite3.Error,
    subprocess.SubprocessError,
)


# a private worker store keeps batch results separate from active research work
def RunCatalogueBatch(Directory, SourceRoot, Revision, Catalogues, MaxSeconds, Native):
    CheckRevision(Revision)
    if Directory.is_relative_to(SourceRoot):
        raise ValueError("use a new run directory outside the source checkout")
    Plan = BuildRunPlan(Catalogues, Revision)
    Directory.mkdir(mode=0o700)
    WriteRecord(Directory / "CataloguePlan.json", Plan)
    Store = Directory / "Store"
    Config, _, _ = PilotConfig(Directory, SourceRoot, 1)
    with Ledger(Store, create=True, max_running=1):
        pass
    if Native is not None:
        NativeConfig, _, _ = Native
        Controller = read_config(NativeConfig)["controller"]
        if Controller != {"adapter": "a03", "store": str(Store)}:
            raise ValueError("native supervisor must use this run's private A03 store")
    Submissions, Results = SubmitCatalogue(Directory, Plan, Store, Revision)
    Failures = []
    PhaseJobs = {}
    if Submissions:
        Failure = RunSupervisor(Directory, SourceRoot, Config, MaxSeconds, "Offline")
        if Failure:
            Failures.append(Failure)
        if Native is not None:
            try:
                PhaseJobs = AdvanceCatalogue(Plan, Store, Submissions, Native)
                if PhaseJobs:
                    Failure = RunSupervisor(
                        Directory, SourceRoot, Native[0], MaxSeconds, "Native"
                    )
                    if Failure:
                        Failures.append(Failure)
            except ScopeErrors as Error:
                Failures.append(
                    {"stage": "native_evidence", "reason": str(Error)[:2048]}
                )
    Results.update(ReadCatalogueJobs(Store, Submissions, PhaseJobs))
    Outcome = RunOutcome(Plan, Results, Failures)
    WriteRecord(Directory / "CatalogueResult.json", Outcome)
    return Outcome


# per scope submission receipts remain inspectable even before the batch finishes
def SubmitCatalogue(Directory, Plan, Store, Revision):
    Submissions, Results = {}, {}
    for Index, (Scope, Identity) in enumerate(Plan["scopes"].items(), 1):
        try:
            Receipt = FeatureRecipes[Identity].Submit(Store, Revision)
            if Receipt["scope"] != Scope:
                raise ValueError("submitted scope differs from the selected recipe")
            Submissions[Scope] = Receipt
        except ScopeErrors as Error:
            Results[Scope] = {
                "status": "failed",
                "stage": "submission",
                "reason": str(Error)[:2048],
            }
        WriteRecord(
            Directory / f"Submission{Index}.json",
            {
                "scope": Scope,
                "receipt": Submissions.get(Scope),
                "failure": Results.get(Scope),
            },
        )
        print(
            f"Prepared {Scope}: {'submitted' if Scope in Submissions else 'failed'}",
            file=sys.stderr,
            flush=True,
        )
    return Submissions, Results


# only explicitly configured native experiments can advance a parked assessment
def AdvanceCatalogue(Plan, Store, Submissions, Native):
    Config, Kind, Resource = Native
    Phases = {}
    for Scope, Identity in Plan["scopes"].items():
        Recipe = FeatureRecipes[Identity]
        if Scope in Submissions and Recipe.Advance is not None:
            Result = Recipe.Advance(Store, Config, Kind, Resource, 0)
            if Result["status"] == "experiment_attached":
                Phases[Scope] = Result["phase_jobs"]
    return Phases


# the established supervisor executes each claim and retains its own durable receipts
def RunSupervisor(Directory, SourceRoot, Config, MaxSeconds, Stage):
    try:
        with (Directory / f"{Stage}Supervisor.log").open("xb") as Log:
            Process = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(SourceRoot / "re/automation/Supervisor.py"),
                    "--config",
                    str(Config),
                    "run",
                    "--idle-seconds",
                    "8",
                    "--max-seconds",
                    str(MaxSeconds),
                ],
                cwd=SourceRoot,
                stdout=Log,
                stderr=subprocess.STDOUT,
                timeout=MaxSeconds + 90,
                check=False,
            )
        if Process.returncode:
            return {"stage": Stage, "exit_code": Process.returncode}
    except (OSError, subprocess.TimeoutExpired) as Error:
        return {"stage": Stage, "reason": str(Error)[:2048]}
    return None


# controller receipts are the authority for the batch's completed and blocked work
def ReadCatalogueJobs(Store, Submissions, PhaseJobs):
    Results = {}
    with Ledger(Store) as State:
        for Scope, Receipt in Submissions.items():
            Identities = [Job["id"] for Job in Receipt["jobs"]]
            Identities.extend(PhaseJobs.get(Scope, {}).values())
            Jobs = [State.status(Identity)["jobs"][0] for Identity in Identities]
            States = {Job["state"] for Job in Jobs}
            if States == {"completed"}:
                Status = "completed"
            elif States & {"rejected", "failed"}:
                Status = "failed"
            else:
                Status = next(
                    (
                        Item
                        for Item in (
                            "running",
                            "queued",
                            "waiting_application",
                            "waiting_evidence",
                            "waiting_ci",
                        )
                        if Item in States
                    ),
                    "unfinished",
                )
            Results[Scope] = {
                "status": Status,
                "assessment_job": Receipt["assessment_job"],
                "jobs": Jobs,
            }
    return Results
